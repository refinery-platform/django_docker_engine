import datetime
import logging
import os
import re
import subprocess
import unittest
from collections import namedtuple
from distutils import dir_util
from shutil import rmtree
from sys import version_info
from time import sleep

import requests
from mock import patch
from requests.exceptions import ConnectionError

from django_docker_engine.container_managers.docker_engine import \
    DockerEngineManager
from django_docker_engine.docker_utils import (DockerClientRunWrapper,
                                               DockerClientSpec,
                                               DockerContainerSpec)
from tests import NGINX_IMAGE

if version_info >= (3,):
    from urllib.error import URLError
else:
    from urllib2 import URLError

logging.basicConfig()
logger = logging.getLogger(__name__)


ContainerInfo = namedtuple('ContainerInfo', ['url', 'name'])


class LiveDockerTests(unittest.TestCase):

    @property
    def spec(self):
        return DockerClientSpec('/tmp/django-docker-engine-test',
                                do_input_json_envvar=True)

    def setUp(self):
        # Docker Engine's clock stops when the computer goes to sleep,
        # and restarts where it left off when it wakes up.
        # https://github.com/docker/for-mac/issues/17
        # This gets it back in sync with reality.
        subprocess.call(
            'docker run --rm --privileged alpine hwclock -s'.split(' '))

        self.client_wrapper = DockerClientRunWrapper(self.spec)
        self.test_label = self.client_wrapper.root_label + '.test'
        self.initial_containers = self.client_wrapper.list()
        self.initial_tmp = self.ls_tmp()
        if self.initial_tmp != []:
            logger.warn('Previous tests left junk in {}'.format(
                self.client_wrapper._get_data_dir()))

        # There may be containers running which are not "my containers".
        self.assertEqual(0, self.count_containers())

    def start_container(self, extra_kwargs={}):
        name = self.timestamp()
        self.assertFalse(self.client_wrapper.is_live(name))
        kwargs = {
            'image_name': NGINX_IMAGE,
            'container_name': name,
            'labels': {self.test_label: 'true'}
        }
        kwargs.update(extra_kwargs)
        return ContainerInfo(
            url=self.client_wrapper.run(DockerContainerSpec(**kwargs)),
            name=name,
        )

    def docker_host(self):
        return os.environ.get('DOCKER_HOST')

    def docker_host_ip(self):
        return re.search(
            r'^tcp://(\d+\.\d+\.\d+\.\d+):\d+$',
            self.docker_host()
        ).group(1)

    # Other supporting methods for tests:
    def timestamp(self):
        return re.sub(r'\W', '_', str(datetime.datetime.now()))

    def count_containers(self):
        return len(self.client_wrapper.list(
            filters={'label': self.test_label}
        ))

    def assert_loads_eventually(self, url, text):
        """
        Retries until it gets a 200 response. Note that these tests hit the
        container directly, rather than going through the proxy, so there
        is no corresponding "assert_loads_immediately".
        """
        for i in range(100):
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    self.assertIn(text, response.text)
                return
            except (ConnectionError, URLError):
                pass
            sleep(0.1)
        self.fail('Never got 200')

    def ls_tmp(self):
        try:
            return sorted(os.listdir(self.client_wrapper._get_data_dir()))
        except OSError:
            return []


class LiveDockerTestsDirty(LiveDockerTests):
    # This test leaves temp files around so we can't make
    # the same tearDown assertions that we do for other tests.

    def test_container_spec_with_extra_directories_bad(self):
        with self.assertRaises(AssertionError) as context:
            self.start_container({
                'input': {'foo': 'bar'},
                'container_input_path': '/usr/share/nginx/html/index.html',
                'extra_directories': ["/test", "coffee"]
            })
        self.assertEqual(
            context.exception.args[0],
            "Specified path: `coffee` is not absolute"
        )


class LiveDockerTestsClean(LiveDockerTests):

    def tearDown(self):
        self.client_wrapper.purge_by_label(self.test_label)

        self.assertEqual(self.initial_containers, self.client_wrapper.list())
        self.assertEqual(self.initial_tmp, self.ls_tmp())

    def test_at_a_minimum(self):
        # A no-op, but if the tests stall, it may be
        # helpful to see if they are even starting.
        self.assertTrue(True)

    def test_container_spec_no_input(self):
        info = self.start_container()
        self.assert_loads_eventually(info.url, 'Welcome to nginx!')
        self.assertTrue(self.client_wrapper.is_live(info.name))

    def test_container_spec_with_input(self):
        url = self.start_container({
            'input': {'foo': 'bar'},
            'container_input_path': '/usr/share/nginx/html/index.html'
        }).url
        self.assert_loads_eventually(url, '{"foo": "bar"}')

    def assert_cpu_quota(self, expected, given={}):

        with patch.object(DockerEngineManager,
                          'run') as mock_run, \
                patch.object(DockerClientRunWrapper,
                             'lookup_container_url'):
            old_dirs = set(self.ls_tmp())
            self.start_container(given)
            (args, kwargs) = mock_run.call_args
            self.assertEqual(kwargs['nano_cpus'], expected)
            new_dirs = set(self.ls_tmp()) - old_dirs
            # Can't rely on normal cleanup, because there is no container.
            for dir in new_dirs:
                rmtree('/tmp/django-docker-engine-test/' + dir)

    def test_container_spec_cpu_default(self):
        self.assert_cpu_quota(5e8)

    def test_container_spec_cpu_small(self):
        self.assert_cpu_quota(1e7, given={'cpus': 0.01})

    def test_container_spec_with_extra_directories_good(self):
        self.start_container({
            'input': {'foo': 'bar'},
            'container_input_path': '/usr/share/nginx/html/index.html',
            'extra_directories': ["/test", "/coffee"]
        })

    def test_purge(self):
        """
        WARNING: I think this is prone to race conditions.
        If you get an error, try just giving it more time.
        """
        self.assertEqual(0, self.count_containers())

        url = self.start_container().url
        self.assertEqual(1, self.count_containers())
        self.assert_loads_eventually(url, 'Welcome to nginx!')

        self.client_wrapper.purge_inactive(5)
        self.assertEqual(1, self.count_containers())
        # Even without activity, it should not be purged if younger than the limit.

        sleep(2)

        self.assert_loads_eventually(url, 'Welcome to nginx!')

        # Be careful of race conditions if developing locally:
        # I had to give a bit more time for the same test to pass with remote Docker.
        self.client_wrapper.purge_inactive(4)
        sleep(2)

        self.assertEqual(1, self.count_containers())
        # With a tighter time limit, recent activity should keep it alive.

        sleep(2)

        self.client_wrapper.purge_inactive(0)
        self.assertEqual(0, self.count_containers())
        # But with an even tighter limit, it should be purged.
