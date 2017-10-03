import unittest
import requests
import subprocess
import time
import socket
from django_docker_engine.docker_utils import (DockerContainerSpec, DockerClientWrapper)
from shutil import rmtree
from os import mkdir


class SubprocessTests(unittest.TestCase):
    """
    Check that the basic functionality works from end-to-end,
    starting the django server as you would from the command-line.
    """

    def free_port(self):
        s = socket.socket()
        s.bind(('', 0))
        return str(s.getsockname()[1])

    def setUp(self):
        self.port = self.free_port()
        self.process = subprocess.Popen(['./manage.py', 'runserver', self.port])
        time.sleep(1)
        self.container_name = 'test-' + self.port
        self.url = 'http://127.0.0.1:{}/docker/{}/'.format(self.port, self.container_name)
        self.tmp_dir = '/tmp/test-' + self.port
        mkdir(self.tmp_dir)
        # TODO: Might use mkdtemp, but Docker couldn't see the directory?
        # self.tmp_dir = mkdtemp()
        # chmod(self.tmp_dir, 0777)

    def tearDown(self):
        self.process.kill()
        rmtree(self.tmp_dir)

    def test_please_wait(self):
        r = requests.get(self.url)
        self.assertIn('Please wait', r.content)

    def test_container(self):
        client = DockerClientWrapper(self.tmp_dir)
        client.run(
            DockerContainerSpec(
                image_name='nginx:1.10.3-alpine',
                container_name=self.container_name
            )
        )
        time.sleep(1)
        r = requests.get(self.url)
        self.assertIn('nginx', r.content)

        client.purge_by_label(self.container_name)
