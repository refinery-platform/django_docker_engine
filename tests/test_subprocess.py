import unittest
import requests
import os
import subprocess
import time
import socket
from django_docker_engine.docker_utils import (DockerContainerSpec, DockerClientWrapper)

class SubprocessTests(unittest.TestCase):

    def free_port(self):
        s = socket.socket()
        s.bind(('', 0))
        return str(s.getsockname()[1])

    def setUp(self):
        self.port = self.free_port()
        subprocess.Popen(['./manage.py', 'runserver', self.port])
        time.sleep(1)
        self.container_name = 'test-' + self.port
        self.url = 'http://127.0.0.1:{}/docker/{}/'.format(self.port, self.container_name)

    def tearDown(self):
        pass
        # TODO: remove old container
        # TODO: remove old tmp dir

    def test_please_wait(self):
        r = requests.get(self.url)
        self.assertIn('Please wait', r.content)

    def test_container(self):
        DockerClientWrapper('/tmp/test-' + self.port).run(
            DockerContainerSpec(
                image_name='nginx:1.10.3-alpine', 
                container_name=self.container_name
            )
        )
        time.sleep(1)
        r = requests.get(self.url)
        self.assertIn('nginx', r.content)
