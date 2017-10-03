import unittest
from datetime import datetime
import logging
import re
from django_docker_engine.container_managers.docker_engine import (DockerEngineManager, NoPortsOpen)

logging.basicConfig()
logger = logging.getLogger(__name__)


class DockerEngineManagerTests(unittest.TestCase):

    def test_no_ports_open(self):
        timestamp = re.sub(r'\W', '-', datetime.now().isoformat())
        data_dir = '/tmp/django-docker-tests-' + timestamp
        root_label = 'test-root'
        manager = DockerEngineManager(data_dir, root_label)
        container_name = timestamp
        manager.run('alpine:3.6',
                    name=container_name,
                    cmd=None,
                    labels={root_label+'.port': '12345'}
        )
        with self.assertRaises(NoPortsOpen):
            manager.get_url(container_name)


