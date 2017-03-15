#from django.test import TestCase

import pprint

import unittest
import os
import datetime
import re
import requests
import django
from docker_utils import DockerClient
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
        ports_spec = {'80/tcp': None}
        container = DockerClient().run('nginx:1.10.3-alpine',
                                       detach=True,
                                       volumes=volume_spec,
                                       ports=ports_spec)
        container.reload()
        port = container.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
        while True:
            r = requests.get('http://localhost:{}/index.html'.format(port))
            if r.status_code == 200:
                self.assertEqual(r.text, hello_html)
                break
            sleep(1) # It seems to be up on the first request, but this is safer.

class ProxyTests(unittest.TestCase):

    def test_higlass_proxy(self):
        c = django.test.Client()
        r = c.get('/docker/proxy_any_host/higlass.io/app/')
        self.assertEqual(200, r.status_code)
        self.assertRegexpMatches(r.content, r'HiGlass')
        # TODO: URLs for AJAX requests are not being rewritten, for example: /api/v1/tileset_info/...

    def test_gehlenborg_proxy(self):
        c = django.test.Client()
        r = c.get('/docker/proxy_any_host/gehlenborg.com/research/')
        self.assertEqual(200, r.status_code)
        self.assertRegexpMatches(r.content, r'Refinery Platform')
