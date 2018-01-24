import unittest
from datetime import datetime
import re
from django_docker_engine.container_managers.docker_engine \
    import (DockerEngineManager, ExpectedPortMissing,
            MisconfiguredPort, NoPortLabel)


class DockerEngineManagerTests(unittest.TestCase):

    def setUp(self):
        timestamp = re.sub(r'\W', '-', datetime.now().isoformat())
        data_dir = '/tmp/django-docker-tests-' + timestamp
        self.root_label = 'test-root'
        self.manager = DockerEngineManager(data_dir, self.root_label)
        self.container_name = timestamp
        self.kwargs = {
            'cmd': None
        }

    def assert_add_kwarg_still_fails(self, key, value, image, expected_error):
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

    def test_expected_errors(self):
        self.assert_add_kwarg_still_fails(
            'name', self.container_name,
            'alpine:3.6',
            NoPortLabel
        )

        self.assert_add_kwarg_still_fails(
            'labels', {self.root_label + '.port': '12345'},
            'alpine:3.6',
            ExpectedPortMissing
            # Had been 'NoPortsOpen': I'm not sure why behavior changed. :(
        )

        self.assert_add_kwarg_still_fails(
            'detach', True,
            'nginx:1.10.3-alpine',
            ExpectedPortMissing
        )

        self.assert_add_kwarg_still_fails(
            'labels', {self.root_label + '.port': '80'},
            'nginx:1.10.3-alpine',
            MisconfiguredPort
        )

        self.assert_add_kwarg_still_fails(
            'ports', {'80/tcp': None},
            'nginx:1.10.3-alpine',
            None
        )
