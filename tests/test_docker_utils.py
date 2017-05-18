import unittest
import os
import datetime
import re
import requests
import django
import paramiko
from urllib2 import URLError
from requests.exceptions import ConnectionError
from distutils import dir_util
from shutil import rmtree
from time import sleep
from django_docker_engine.docker_utils import DockerClientWrapper, DockerContainerSpec


class DockerTests(unittest.TestCase):
    def setUp(self):
        # mkdtemp is the obvious way to do this, but
        # the resulting directory is not visible to Docker.
        base = '/tmp/django-docker-tests'
        self.tmp = os.path.join(
            base,
            re.sub(r'\W', '_', str(datetime.datetime.now())))
        self.mkdir_on_host(self.tmp)
        self.client_wrapper = DockerClientWrapper()
        self.test_label = self.client_wrapper.root_label + '.test'
        self.initial_containers = self.client_wrapper.list()
        # There may be containers running which are not "my containers".
        self.assertEqual(0, self.count_my_containers())

    def tearDown(self):
        self.rmdir_on_host(self.tmp)
        self.client_wrapper.purge_by_label(self.test_label)
        final_containers = self.client_wrapper.list()
        self.assertEqual(self.initial_containers, final_containers)

    # Utils for accessing remote docker engine:

    def docker_host(self):
        return os.environ.get('DOCKER_HOST')

    def docker_host_ip(self):
        return re.search(
            r'^tcp://(\d+\.\d+\.\d+\.\d+):\d+$',
            self.docker_host()
        ).group(1)

    def remote_exec(self, command):
        host_ip = self.docker_host_ip()
        key = paramiko.RSAKey.from_private_key_file(DockerTests.PEM)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=host_ip, username='ec2-user', pkey=key)
        client.exec_command(command)

    PEM = 'django_docker_cloudformation.pem'

    # These *_on_host methods are in a sense duplicates of the helper methods
    # in docker_utils.py, but I think here it makes sense to have explicit
    # if-thens, rather than hiding it with polymorphism.

    def rmdir_on_host(self, path):
        if self.docker_host():
            self.remote_exec('rm -rf {}'.format(path))
        else:
            rmtree(self.tmp)

    def mkdir_on_host(self, path):
        if self.docker_host():
            self.remote_exec('mkdir -p {}'.format(path))
        else:
            dir_util.mkpath(path)

    def write_to_host(self, content, path):
        if self.docker_host():
            self.remote_exec("cat > {} <<'END'\n{}\nEND".format(path, content))
        else:
            with open(path, 'w') as file:
                file.write(content)
                file.write('\n')  # For consistency with heredoc

    # Other supporting methods for tests:

    def timestamp(self):
        return re.sub(r'\W', '_', str(datetime.datetime.now()))

    def count_my_containers(self):
        return len(self.client_wrapper.list(
            filters={'label': self.test_label}
        ))

    def one_file_server(self, container_name, html):
        self.write_to_host(html, os.path.join(self.tmp, 'index.html'))
        volume_spec = [{
            'host': self.tmp,
            'bind': '/usr/share/nginx/html'}]
        ports_spec = {'80/tcp': None}
        self.client_wrapper._manager_run(
            'nginx:1.10.3-alpine',
            name=container_name,
            detach=True,
            volumes=volume_spec,
            ports=ports_spec,
            labels={self.test_label: 'true'})
        return self.client_wrapper.lookup_container_url(container_name)

    def assert_url_content(self, url, content, client=django.test.Client()):
        for i in xrange(10):
            try:
                response = client.get(url)
                if response.status_code == 200:
                    self.assertIn(content, response.content)
                return
            except (ConnectionError, URLError):
                pass
            sleep(1)
        self.fail('Never got 200')

    # Tests at the top are low level;
    # Tests at the bottom are at higher levels of abstraction.

    def test_at_a_minimum(self):
        # A no-op, but if the tests stall, it may be
        # helpful to see if they are even starting.
        self.assertTrue(True)

    def test_container_spec_no_input(self):
        url = self.client_wrapper.run(DockerContainerSpec(
            image_name='nginx:1.10.3-alpine',
            container_name=self.timestamp(),
            labels={self.test_label: 'true'}
        ))
        self.assert_url_content(url, 'Welcome to nginx!')

    def test_container_spec_with_input(self):
        url = self.client_wrapper.run(DockerContainerSpec(
            image_name='nginx:1.10.3-alpine',
            container_name=self.timestamp(),
            labels={self.test_label: 'true'},
            input={'foo': 'bar'},
            container_input_path='/usr/share/nginx/html/index.html'
        ))
        self.assert_url_content(url, '{"foo": "bar"}')

    def test_docker_proxy(self):
        container_name = self.timestamp()
        hello_html = '<html><body>hello proxy</body></html>'
        self.one_file_server(container_name, hello_html)
        url = '/docker/{}/'.format(container_name)
        self.assert_url_content(url, hello_html)

    def test_hello_world(self):
        input = 'hello world'
        output = self.client_wrapper._manager_run(
            'alpine:3.4',
            'echo ' + input,
            labels={self.test_label: 'true'}
        )
        self.assertEqual(output, input + '\n')

    def test_httpd(self):
        container_name = self.timestamp()
        hello_html = '<html><body>hello direct</body></html>'
        url = self.one_file_server(container_name, hello_html)
        self.assert_url_content(url, hello_html, client=requests)

    def test_mount_host_volumes(self):
        input = 'hello world\n'
        self.write_to_host(input, os.path.join(self.tmp, 'world.txt'))
        volume_spec = [{'host': self.tmp, 'bind': '/hello'}]
        output = self.client_wrapper._manager_run(
            'alpine:3.4',
            'cat /hello/world.txt',
            labels={self.test_label: 'true'},
            volumes=volume_spec
        )
        self.assertEqual(output, input + '\n')

    def test_mount_scratch_volumes(self):
        volume_spec = [{'bind': '/hello'}]
        self.assertEqual(volume_spec[0].get('host'), None)  # Note: No explicit volume.
        input = 'hello_world'  # TODO: Without underscore, only "hello" comes back?
        output = self.client_wrapper._manager_run(
            'alpine:3.4',
            'sh -c "echo \"{}\" > /hello/world.txt; cat /hello/world.txt"'.format(input),
            labels={self.test_label: 'true'},
            volumes=volume_spec
        )
        self.assertEqual(output, input + '\n')
        # Note that this doesn't really confirm that an outside volume was created,
        # but better than nothing.

    def test_purge(self):
        """
        WARNING: I think this is prone to race conditions.
        If you get an error, try just giving it more time.
        """
        self.assertEqual(0, self.count_my_containers())

        url = self.client_wrapper.run(DockerContainerSpec(
            image_name='nginx:1.10.3-alpine',
            container_name=self.timestamp(),
            labels={self.test_label: 'true'}
        ))
        self.assertEqual(1, self.count_my_containers())

        self.client_wrapper.purge_inactive(5)
        self.assertEqual(1, self.count_my_containers())
        # Even without activity, it should not be purged if younger than the limit.

        sleep(2)

        self.assert_url_content(url, 'Welcome to nginx!')

        # Be careful of race conditions if developing locally:
        # I had to give a bit more time for the same test to pass with remote Docker.
        self.client_wrapper.purge_inactive(4)
        sleep(2)

        self.assertEqual(1, self.count_my_containers())
        # With a tighter time limit, recent activity should keep it alive.

        sleep(2)

        self.client_wrapper.purge_inactive(0)
        self.assertEqual(0, self.count_my_containers())
        # But with an even tighter limit, it should be purged.
