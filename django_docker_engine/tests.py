import unittest
import os
import datetime
import re
import requests
import django
from docker_utils import DockerClient, DockerContainerSpec
from shutil import rmtree
from time import sleep


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

    def tearDown(self):
        rmtree(self.tmp)
        DockerContainerSpec.purge(DockerClient.TEST_LABEL)

    def timestamp(self):
        return re.sub(r'\W', '_', str(datetime.datetime.now()))

    def one_file_server(self, container_name, html):
        with open(os.path.join(self.tmp, 'index.html'), 'w') as file:
            file.write(html)
        volume_spec = {
            self.tmp: {
                'bind': '/usr/share/nginx/html',
                'mode': 'ro'}}
        ports_spec = {'80/tcp': None}
        client = DockerClient()
        client.run('nginx:1.10.3-alpine',
                   name=container_name,
                   detach=True,
                   volumes=volume_spec,
                   ports=ports_spec,
                   labels={DockerClient.TEST_LABEL: 'true'})
        return client.lookup_container_port(container_name)

    def assert_url_content(self, url, content, client=django.test.Client()):
        for i in xrange(10):
            response = client.get(url)
            if response.status_code == 200:
                self.assertEqual(response.content, content)
                return
            sleep(1)
        self.fail('Never got 200')

    # Tests at the top are low level;
    # Tests at the bottom are at higher levels of abstraction.

    def test_hello_world(self):
        input = 'hello world'
        output = DockerClient().run(
            'alpine:3.4',
            'echo ' + input,
            labels={DockerClient.TEST_LABEL: 'true'}
        )
        self.assertEqual(output, input + '\n')

    def test_volumes(self):
        input = 'hello world\n'
        with open(os.path.join(self.tmp, 'world.txt'), 'w') as file:
            file.write(input)
        volume_spec = {self.tmp: {'bind': '/hello', 'mode': 'ro'}}
        output = DockerClient().run(
            'alpine:3.4',
            'cat /hello/world.txt',
            labels={DockerClient.TEST_LABEL: 'true'},
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

    def test_container_spec(self):
        input = 'hello world'
        input_file = os.path.join(self.tmp, 'index.html')
        with open(input_file, 'w') as file:
            file.write(input)
        container_name = self.timestamp()
        DockerContainerSpec(
            image_name='nginx:1.10.3-alpine',
            container_name=container_name,
            input_mount='/usr/share/nginx/html',
            input_files=[input_file],
            labels={DockerClient.TEST_LABEL: 'true'}).run()
        url = '/docker/{}/'.format(container_name)
        self.assert_url_content(url, input)
