#from django.test import TestCase

import unittest
import os
import datetime
import re
from docker_utils import DockerClient
from tempfile import mkdtemp
from shutil import rmtree

class DockerTests(unittest.TestCase):
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
        client = DockerClient()
        output = client.run('alpine', 'echo hello world')
        self.assertEqual(output, 'hello world\n')

    def test_volumes(self):
        with open(os.path.join(DockerTests.tmp , 'world.txt'), 'w') as file:
            file.write('hello world')
        client = DockerClient()
        volume_spec = {DockerTests.tmp: {'bind': '/hello', 'mode': 'ro'}}
        output = client.run('alpine', 'cat /hello/world.txt',
                            volumes=volume_spec)
        self.assertEqual(output, 'hello world')

    def test_httpd(self):
        client = DockerClient()
        pass