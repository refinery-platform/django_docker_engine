import re
import unittest
from datetime import datetime

from django_docker_engine.container_managers.docker_engine import (DockerEngineManager,
                                                                   ExpectedPortMissing,
                                                                   MisconfiguredPort,
                                                                   NoPortLabel)
from tests import ALPINE_IMAGE, ECHO_IMAGE, NGINX_IMAGE


class DockerEngineManagerErrorTests(unittest.TestCase):

    def setUp(self):
        timestamp = re.sub(r'\W', '-', datetime.now().isoformat())
        data_dir = '/tmp/django-docker-tests-' + timestamp
        self.root_label = 'test-root'
        self.manager = DockerEngineManager(data_dir, self.root_label)
        self.container_name = timestamp
        self.kwargs = {
            'cmd': None
        }

    def assert_kwarg_fails(self, key, value, image, expected_error):
        self.kwargs[key] = value
        self.manager.run(image, **self.kwargs)
        if expected_error:
            with self.assertRaises(expected_error):
                self.manager.get_url(self.container_name)
        else:
            self.manager.get_url(self.container_name)
        # TODO: Why the '/'?
        self.manager.list({'name': '/' + self.container_name}
                          )[0].remove(force=True)

    def test_no_port_label(self):
        self.assert_kwarg_fails(
            'name', self.container_name,
            ALPINE_IMAGE,
            NoPortLabel
        )

    def test_expected_port_missing_label(self):
        self.assert_kwarg_fails(
            'labels', {self.root_label + '.port': '12345'},
            ALPINE_IMAGE,
            ExpectedPortMissing
            # Had been 'NoPortsOpen': I'm not sure why behavior changed. :(
        )

    def test_expected_port_missing_detach(self):
        self.assert_kwarg_fails(
            'detach', True,
            NGINX_IMAGE,
            ExpectedPortMissing
        )

    def test_misconfigured_port(self):
        self.assert_kwarg_fails(
            'labels', {self.root_label + '.port': '80'},
            NGINX_IMAGE,
            MisconfiguredPort
        )

    def test_no_error(self):
        self.assert_kwarg_fails(
            'ports', {'80/tcp': None},
            NGINX_IMAGE,
            None
        )
