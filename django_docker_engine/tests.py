import unittest
import os
import datetime
import re
import requests
import django
from docker_utils import DockerClientWrapper, DockerContainerSpec
from shutil import rmtree
from time import sleep
import docker  # Only to be used in setUp and tearDown


class DockerTests(unittest.TestCase):
    def setUp(self):
        # mkdtemp is the obvious way to do this, but
        # the resulting directory is not visible to Docker.
        base = '/tmp/django-docker-tests'
        try:
            os.mkdir(base)
        except BaseException:
            pass  # May already exist
        self.tmp = os.path.join(
            base,
            re.sub(r'\W', '_', str(datetime.datetime.now())))
        os.mkdir(self.tmp)
        self.initial_containers = docker.from_env().containers.list()
        self.assertEqual(0, self.count_my_containers())

    def tearDown(self):
        rmtree(self.tmp)
        DockerClientWrapper().purge_by_label(DockerTests.TEST_LABEL)
        final_containers = docker.from_env().containers.list()
        self.assertEqual(self.initial_containers, final_containers)

    TEST_LABEL = DockerClientWrapper.ROOT_LABEL + '.test'

    def timestamp(self):
        return re.sub(r'\W', '_', str(datetime.datetime.now()))

    def count_my_containers(self):
        return len(docker.from_env().containers.list(
            filters={'label': DockerTests.TEST_LABEL}
        ))

    def one_file_server(self, container_name, html):
        with open(os.path.join(self.tmp, 'index.html'), 'w') as file:
            file.write(html)
        volume_spec = {
            self.tmp: {
                'bind': '/usr/share/nginx/html',
                'mode': 'ro'}}
        ports_spec = {'80/tcp': None}
        client = DockerClientWrapper()
        client.run('nginx:1.10.3-alpine',
                   name=container_name,
                   detach=True,
                   volumes=volume_spec,
                   ports=ports_spec,
                   labels={DockerTests.TEST_LABEL: 'true'})
        return client.lookup_container_port(container_name)

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
        output = DockerClientWrapper().run(
            'alpine:3.4',
            'echo ' + input,
            labels={DockerTests.TEST_LABEL: 'true'}
        )
        self.assertEqual(output, input + '\n')

    def test_volumes(self):
        input = 'hello world\n'
        with open(os.path.join(self.tmp, 'world.txt'), 'w') as file:
            file.write(input)
        volume_spec = {self.tmp: {'bind': '/hello', 'mode': 'ro'}}
        output = DockerClientWrapper().run(
            'alpine:3.4',
            'cat /hello/world.txt',
            labels={DockerTests.TEST_LABEL: 'true'},
            volumes=volume_spec
        )
        self.assertEqual(output, input)

    def test_httpd(self):
        container_name = self.timestamp()
        hello_html = '<html><body>hello direct</body></html>'
        port = self.one_file_server(container_name, hello_html)
        url = 'http://localhost:{}/'.format(port)
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
            image_name='nginx:1.10.3-alpine',
            container_name=container_name,
            labels={DockerTests.TEST_LABEL: 'true'}).run()
        url = '/docker/{}/'.format(container_name)
        self.assert_url_content(url, 'Welcome to nginx!')

    def test_container_spec_with_input(self):
        container_name = self.timestamp()
        DockerContainerSpec(
            image_name='nginx:1.10.3-alpine',
            container_name=container_name,
            input={'foo': 'bar'},
            labels={DockerTests.TEST_LABEL: 'true'}).run()
        url = '/docker/{}/'.format(container_name)
        self.assert_url_content(url, 'Welcome to nginx!')
        # TODO: do something that depends on input

    def test_container_active(self):
        container_name = self.timestamp()
        DockerContainerSpec(
            image_name='nginx:1.10.3-alpine',
            container_name=container_name,
            labels={DockerTests.TEST_LABEL: 'true'}).run()
        self.assertEqual(1, self.count_my_containers())

        DockerClientWrapper().purge_inactive(5)
        self.assertEqual(1, self.count_my_containers())
        # Even without activity, it should not be purged if younger than the limit.

        sleep(2)

        url = '/docker/{}/'.format(container_name)
        django.test.Client().get(url)

        DockerClientWrapper().purge_inactive(1)
        self.assertEqual(1, self.count_my_containers())
        # With a tighter time limit, recent activity should keep it alive.

        sleep(2)

        DockerClientWrapper().purge_inactive(0)
        self.assertEqual(0, self.count_my_containers())
        # But with an even tighter limit, it should be purged.
