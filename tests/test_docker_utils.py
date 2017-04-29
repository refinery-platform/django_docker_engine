import unittest
import os
import datetime
import re
import requests
import django
import errno
import subprocess
import tempfile
from shutil import rmtree
from time import sleep
from django_docker_engine.docker_utils import DockerClientWrapper, DockerContainerSpec
from django_docker_engine.container_managers import docker_engine


class DockerTests(unittest.TestCase):
    def setUp(self):
        # mkdtemp is the obvious way to do this, but
        # the resulting directory is not visible to Docker.
        base = '/tmp/django-docker-tests'
        self.tmp = os.path.join(
            base,
            re.sub(r'\W', '_', str(datetime.datetime.now())))
        self.mkdir_on_host(self.tmp)
        self.manager = docker_engine.DockerEngineManager()
        self.client = DockerClientWrapper(manager=self.manager)
        self.test_label = self.client.root_label + '.test'
        self.initial_containers = self.client.list()

        # There may be containers running which are not "my containers".
        self.assertEqual(0, self.count_my_containers())

    def tearDown(self):
        rmtree(self.tmp)
        self.client.purge_by_label(self.test_label)
        final_containers = self.client.list()
        self.assertEqual(self.initial_containers, final_containers)

    def docker_host_ip(self):
        return re.search(
            r'^tcp://(\d+\.\d+\.\d+\.\d+):\d+$',
            os.environ['DOCKER_HOST']
        ).group(1)

    PEM = 'django_docker_cloudformation.pem'

    def mkdir_on_host(self, path):
        """
        mkdir, wherever Docker is running.
        If Docker is remote (ie, DOCKER_HOST is set) we will
        try to ssh to that machine to put the file in place;
        port 22 must be open, and we must have the necessary key.
        """
        if os.environ.get('DOCKER_HOST'):
            ip = self.docker_host_ip()
            subprocess.check_call([
                'ssh',
                '-o', 'StrictHostKeyChecking=no',
                '-i', DockerTests.PEM,
                'ec2-user@{}'.format(ip),
                "'mkdir -p {}'".format(path)
            ])
        else:
            try:
                os.makedirs(path)
            except OSError as exc:
                if exc.errno == errno.EEXIST and os.path.isdir(path):
                    pass
                else:
                    raise

    def write_to_host(self, content, path):
        """
        Writes content to path, wherever Docker is running.
        If Docker is remote (ie, DOCKER_HOST is set) we will
        try to ssh to that machine to put the file in place;
        port 22 must be open, and we must have the necessary key.
        """
        if os.environ.get('DOCKER_HOST'):
            ip = self.docker_host_ip()
            (handle, temp_path) = tempfile.mkstemp()
            handle.write(content)
            subprocess.check_call([
                'scp',
                '-o', 'StrictHostKeyChecking=no',
                '-i', DockerTests.PEM,
                temp_path,
                'ec2-user@{}:{}'.format(ip, path)
            ])
        else:
            with open(path, 'w') as file:
                file.write(content)

    def timestamp(self):
        return re.sub(r'\W', '_', str(datetime.datetime.now()))

    def count_my_containers(self):
        return len(self.client.list(
            filters={'label': self.test_label}
        ))

    def one_file_server(self, container_name, html):
        self.write_to_host(html, os.path.join(self.tmp, 'index.html'))
        volume_spec = {
            self.tmp: {
                'bind': '/usr/share/nginx/html',
                'mode': 'ro'}}
        ports_spec = {'80/tcp': None}
        client = self.client
        client.run('nginx:1.10.3-alpine',
                   name=container_name,
                   detach=True,
                   volumes=volume_spec,
                   ports=ports_spec,
                   labels={self.test_label: 'true'})
        return client.lookup_container_url(container_name)

    def assert_url_content(self, url, content, client=django.test.Client()):
        for i in xrange(10):
            response = client.get(url)
            if response.status_code == 200:
                self.assertIn(content, response.content)
                return
            sleep(1)
        self.fail('Never got 200')

    # Tests at the top are low level;
    # Tests at the bottom are at higher levels of abstraction.

    def test_hello_world(self):
        input = 'hello world'
        output = self.client.run(
            'alpine:3.4',
            'echo ' + input,
            labels={self.test_label: 'true'}
        )
        self.assertEqual(output, input + '\n')

    def test_volumes(self):
        input = 'hello world\n'
        self.write_to_host(input, os.path.join(self.tmp, 'world.txt'))
        volume_spec = {self.tmp: {'bind': '/hello', 'mode': 'ro'}}
        output = self.client.run(
            'alpine:3.4',
            'cat /hello/world.txt',
            labels={self.test_label: 'true'},
            volumes=volume_spec
        )
        self.assertEqual(output, input)

    def test_httpd(self):
        container_name = self.timestamp()
        hello_html = '<html><body>hello direct</body></html>'
        url = self.one_file_server(container_name, hello_html)
        self.assert_url_content(url, hello_html, client=requests)

    def test_docker_proxy(self):
        container_name = self.timestamp()
        hello_html = '<html><body>hello proxy</body></html>'
        self.one_file_server(container_name, hello_html)
        url = '/docker/{}/'.format(container_name)
        self.assert_url_content(url, hello_html)

    def test_container_spec_no_input(self):
        container_name = self.timestamp()
        DockerContainerSpec(
            manager=self.manager,
            image_name='nginx:1.10.3-alpine',
            container_name=container_name,
            labels={self.test_label: 'true'}).run()
        url = '/docker/{}/'.format(container_name)
        self.assert_url_content(url, 'Welcome to nginx!')

    def test_container_spec_with_input(self):
        container_name = self.timestamp()
        DockerContainerSpec(
            manager=self.manager,
            image_name='nginx:1.10.3-alpine',
            container_name=container_name,
            input={'foo': 'bar'},
            container_input_path='/usr/share/nginx/html/index.html',
            labels={self.test_label: 'true'}
        ).run()
        url = '/docker/{}/'.format(container_name)
        self.assert_url_content(url, '{"foo": "bar"}')

    def test_container_active(self):
        container_name = self.timestamp()
        DockerContainerSpec(
            manager=self.manager,
            image_name='nginx:1.10.3-alpine',
            container_name=container_name,
            labels={self.test_label: 'true'}).run()
        self.assertEqual(1, self.count_my_containers())

        self.client.purge_inactive(5)
        self.assertEqual(1, self.count_my_containers())
        # Even without activity, it should not be purged if younger than the limit.

        sleep(2)

        url = '/docker/{}/'.format(container_name)
        django.test.Client().get(url)

        self.client.purge_inactive(1)
        self.assertEqual(1, self.count_my_containers())
        # With a tighter time limit, recent activity should keep it alive.

        sleep(2)

        self.client.purge_inactive(0)
        self.assertEqual(0, self.count_my_containers())
        # But with an even tighter limit, it should be purged.
