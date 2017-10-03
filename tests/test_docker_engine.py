import unittest
from datetime import datetime
import re
from django_docker_engine.container_managers.docker_engine \
    import (DockerEngineManager, NoPortsOpen, ExpectedPortMissing, MisconfiguredPort)


class DockerEngineManagerTests(unittest.TestCase):

    def setUp(self):
        timestamp = re.sub(r'\W', '-', datetime.now().isoformat())
        data_dir = '/tmp/django-docker-tests-' + timestamp
        self.root_label = 'test-root'
        self.manager = DockerEngineManager(data_dir, self.root_label)
        self.container_name = timestamp

    def test_expected_errors(self):
        kwargs = {
            'name': self.container_name,
            'cmd': None
        }
        self.manager.run('alpine:3.6', **kwargs)
        with self.assertRaises(KeyError):
            self.manager.get_url(self.container_name)

        self.manager.list({'name': '/' + self.container_name})[0].remove(force=True)

        kwargs['labels'] = {self.root_label+'.port': '12345'}
        self.manager.run('alpine:3.6', **kwargs)
        with self.assertRaises(NoPortsOpen):
            self.manager.get_url(self.container_name)

        self.manager.list({'name': '/' + self.container_name})[0].remove(force=True)

        kwargs['detach'] = True
        self.manager.run('nginx:1.10.3-alpine', **kwargs)
        with self.assertRaises(ExpectedPortMissing):
            self.manager.get_url(self.container_name)

        self.manager.list({'name': '/' + self.container_name})[0].remove(force=True)

        kwargs['labels'] = {self.root_label + '.port': '80'}
        self.manager.run('nginx:1.10.3-alpine', **kwargs)
        with self.assertRaises(MisconfiguredPort):
            self.manager.get_url(self.container_name)

        self.manager.list({'name': '/' + self.container_name})[0].remove(force=True)

        kwargs['ports'] = {'80/tcp': None}
        self.manager.run('nginx:1.10.3-alpine', **kwargs)
        self.manager.get_url(self.container_name)
        # Finally works!

        self.manager.list({'name': '/' + self.container_name})[0].remove(force=True)