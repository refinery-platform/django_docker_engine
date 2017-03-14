#from django.test import TestCase

import unittest
from docker_utils import DockerClient

class DockerTests(unittest.TestCase):
    def test_hello_world(self):
        client = DockerClient()
        output = client.run('ubuntu', 'echo hello world')
        self.assertEqual(output, 'hello world\n')

    def test_mount(self):
        pass