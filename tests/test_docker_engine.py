import unittest
from datetime import datetime
import logging
import re
from django_docker_engine.container_managers.docker_engine \
    import (DockerEngineManager, NoPortsOpen, ExpectedPortMissing, MisconfiguredPort)

logging.basicConfig()
logger = logging.getLogger(__name__)


class DockerEngineManagerTests(unittest.TestCase):

    def setUp(self):
        timestamp = re.sub(r'\W', '-', datetime.now().isoformat())
        data_dir = '/tmp/django-docker-tests-' + timestamp
        self.root_label = 'test-root'
        self.manager = DockerEngineManager(data_dir, self.root_label)
        self.container_name = timestamp

    def test_missing_port_label(self):
        self.manager.run(
            'alpine:3.6',
            name=self.container_name,
            cmd=None
        )
        with self.assertRaises(KeyError):
            self.manager.get_url(self.container_name)

    def test_no_ports_open(self):
        self.manager.run(
            'alpine:3.6',
            name=self.container_name,
            cmd=None,
            labels={self.root_label+'.port': '12345'}
        )
        with self.assertRaises(NoPortsOpen):
            self.manager.get_url(self.container_name)

    def test_wrong_port(self):
        self.manager.run(
            'nginx:1.10.3-alpine',
            name=self.container_name,
            cmd=None,
            labels={self.root_label+'.port': '12345'},
            detach = True
        )
        with self.assertRaises(ExpectedPortMissing):
            self.manager.get_url(self.container_name)

    def test_misconfigured_port(self):
        self.manager.run(
            'nginx:1.10.3-alpine',
            name=self.container_name,
            cmd=None,
            labels={self.root_label + '.port': '80'},
            detach=True
        )
        with self.assertRaises(MisconfiguredPort):
            self.manager.get_url(self.container_name)