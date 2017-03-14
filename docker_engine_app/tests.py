#from django.test import TestCase

import unittest
import os
import datetime
import re
import requests
from docker_utils import DockerClient
from tempfile import mkdtemp
from shutil import rmtree
from time import sleep

class DockerTests(unittest.TestCase):
    # TODO: Plain setup should be fine
    @classmethod
    def setUpClass(cls):
        # mkdtemp is the obvious way to do this, but
        # the resulting directory is not visible to Docker.
        base = '/tmp/django-docker-tests'
        try:
            os.mkdir(base)
        except:
            pass # May already exist
        cls.tmp = base + '/' + re.sub(r'\W', '_', str(datetime.datetime.now()))
        os.mkdir(cls.tmp)

    @classmethod
    def tearDownClass(cls):
        rmtree(cls.tmp)

    def test_hello_world(self):
        input = 'hello world'
        output = DockerClient().run('alpine:3.4', 'echo '+input)
        self.assertEqual(output, input + '\n')

    def test_volumes(self):
        input = 'hello world'
        with open(os.path.join(DockerTests.tmp , 'world.txt'), 'w') as file:
            file.write(input)
        volume_spec = {DockerTests.tmp: {'bind': '/hello', 'mode': 'ro'}}
        output = DockerClient().run('alpine:3.4', 'cat /hello/world.txt',
                            volumes=volume_spec)
        self.assertEqual(output, input)

    def test_httpd(self):
        hello_html = '<html><body>hello world</body></html>'
        with open(os.path.join(DockerTests.tmp, 'index.html'), 'w') as file:
            file.write(hello_html)
        volume_spec = {DockerTests.tmp: {'bind': '/usr/share/nginx/html', 'mode': 'ro'}}
        port = 9999
        ports_spec = {'80/tcp': port} # TODO: 9999 -> None
        container = DockerClient().run('nginx:1.10.3-alpine',
                                       detach=True,
                                       volumes=volume_spec,
                                       ports=ports_spec)
        while True:
            r = requests.get('http://localhost:{}/index.html'.format(port))
            if r.status_code == 200:
                self.assertEqual(r.text, hello_html)
                break
            sleep(1) # It seems to be up on the first request, but this is safer.
        pass