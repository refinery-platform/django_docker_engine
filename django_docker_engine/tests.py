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
    def timestamp(self):
        return re.sub(r'\W', '_', str(datetime.datetime.now()))

    def one_file_server(self, container_name, html):
        with open(os.path.join(DockerTests.tmp, 'index.html'), 'w') as file:
            file.write(html)
        volume_spec = {
            DockerTests.tmp: {
                'bind': '/usr/share/nginx/html',
                'mode': 'ro'}}
        ports_spec = {'80/tcp': None}
        client = DockerClient()
        client.run('nginx:1.10.3-alpine',
                   name=container_name,
                   detach=True,
                   volumes=volume_spec,
                   ports=ports_spec)
        return client.lookup_container_port(container_name)

    # TODO: Plain setup should be fine
    @classmethod
    def setUpClass(cls):
        # mkdtemp is the obvious way to do this, but
        # the resulting directory is not visible to Docker.
        base = '/tmp/django-docker-tests'
        try:
            os.mkdir(base)
        except BaseException:
            pass  # May already exist
        cls.tmp = base + '/' + re.sub(r'\W', '_', str(datetime.datetime.now()))
        os.mkdir(cls.tmp)

    @classmethod
    def tearDownClass(cls):
        rmtree(cls.tmp)

    def test_hello_world(self):
        input = 'hello world'
        output = DockerClient().run('alpine:3.4', 'echo ' + input)
        self.assertEqual(output, input + '\n')

    def test_volumes(self):
        input = 'hello world\n'
        with open(os.path.join(DockerTests.tmp, 'world.txt'), 'w') as file:
            file.write(input)
        volume_spec = {DockerTests.tmp: {'bind': '/hello', 'mode': 'ro'}}
        output = DockerClient().run('alpine:3.4', 'cat /hello/world.txt',
                                    volumes=volume_spec)
        self.assertEqual(output, input)

    def test_httpd(self):
        container_name = self.timestamp()
        hello_html = '<html><body>hello direct</body></html>'
        port = self.one_file_server(container_name, hello_html)
        for i in xrange(10):
            r = requests.get('http://localhost:{}/'.format(port))
            if r.status_code == 200:
                self.assertEqual(r.text, hello_html)
                return
            sleep(1)
        self.fail('Never got 200')

    def test_docker_proxy(self):
        container_name = self.timestamp()
        hello_html = '<html><body>hello proxy</body></html>'
        self.one_file_server(container_name, hello_html)
        c = django.test.Client()
        for i in xrange(10):
            r = c.get('/docker/{}/'.format(container_name))
            if r.status_code == 200:
                self.assertEqual(r.content, hello_html)
                return
            sleep(1)
        self.fail('Never got 200')

    def test_container_spec(self):
        input = 'hello world'
        input_file = os.path.join(DockerTests.tmp, 'index.html')
        with open(input_file, 'w') as file:
            file.write(input)
        container_name = self.timestamp()
        spec = DockerContainerSpec(
            image_name='nginx:1.10.3-alpine',
            container_name=container_name,
            input_mount='/usr/share/nginx/html',
            input_files=[input_file])
        spec.run()
        c = django.test.Client()
        for i in xrange(10):
            r = c.get('/docker/{}/'.format(container_name))
            if r.status_code == 200:
                self.assertEqual(r.content, input)
                return
            sleep(1)
        self.fail('Never got 200')