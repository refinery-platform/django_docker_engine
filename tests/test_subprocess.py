import socket
import subprocess
import time
import unittest
from os import mkdir
from shutil import rmtree

import requests
from bs4 import BeautifulSoup

from django_docker_engine.docker_utils import (DockerClientRunWrapper,
                                               DockerClientSpec,
                                               DockerContainerSpec)
from tests import ECHO_IMAGE, NGINX_IMAGE


class PathRoutingTests(unittest.TestCase):
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
        self.process = subprocess.Popen(
            ['./manage.py', 'runserver', self.port])
        time.sleep(1)
        self.container_name = 'test-' + self.port
        self.url = 'http://localhost:{}/docker/{}/'.format(
            self.port, self.container_name)
        self.tmp_dir = '/tmp/test-' + self.port
        mkdir(self.tmp_dir)
        # TODO: Might use mkdtemp, but Docker couldn't see the directory?
        # self.tmp_dir = mkdtemp()
        # chmod(self.tmp_dir, 0777)
        spec = DockerClientSpec(self.tmp_dir,
                                do_input_json_envvar=True)
        self.client = DockerClientRunWrapper(spec)

    def tearDown(self):
        self.process.kill()
        rmtree(self.tmp_dir)
        self.client.purge_by_label('subprocess-test-label')

    def test_please_wait(self):
        self.client.run(
            DockerContainerSpec(
                image_name=NGINX_IMAGE,
                container_name=self.container_name,
                labels={'subprocess-test-label': 'True'}
            )
        )
        r = requests.get(self.url)
        self.assertIn('Please wait', r.content)

    def assert_in_html(self, substring, html):
        # Looks for substring in the text content of html.
        soup = BeautifulSoup(html, 'html.parser', from_encoding='latin-1')
        # Python error page may be misencoded?
        # Pick "latin-1" because it's forgiving.
        text = soup.get_text()
        if substring not in text:
            self.fail(u'"{}" not found in text of html:\n{}'
                      .format(substring, text))

    def test_nginx_container(self):
        self.client.run(
            DockerContainerSpec(
                image_name=NGINX_IMAGE,
                container_name=self.container_name,
                labels={'subprocess-test-label': 'True'}
            )
        )
        time.sleep(1)  # TODO: Race condition sensitivity?
        r_good = requests.get(self.url)
        self.assert_in_html('Welcome to nginx', r_good.content)

        r_bad = requests.get(self.url + 'bad-path')
        self.assert_in_html('Not Found', r_bad.content)
        self.assertEqual(404, r_bad.status_code)

    def assert_http_verb(self, verb):
        response = requests.__dict__[verb.lower()](self.url)
        self.assert_in_html('HTTP/1.1 {} /'.format(verb), response.content)
        # Response shouldn't be HTML, but if we get the Django error page,
        # this will make it much more readable.

    def test_http_echo_verbs(self):
        self.client.run(
            DockerContainerSpec(
                image_name=ECHO_IMAGE,
                container_port=8080,  # and/or set PORT envvar
                container_name=self.container_name
            )
        )
        time.sleep(1)  # TODO: Race condition sensitivity?
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods
        self.assert_http_verb('GET')
        # HEAD has no body, understandably
        # self.assert_http_verb('HEAD')
        self.assert_http_verb('POST')
        self.assert_http_verb('PUT')
        self.assert_http_verb('DELETE')
        # CONNECT not supported by Requests
        # self.assert_http_verb('CONNECT')
        self.assert_http_verb('OPTIONS')
        # TRACE not supported by Requests
        # self.assert_http_verb('TRACE')
        self.assert_http_verb('PATCH')

    def test_url(self):
        self.assertRegexpMatches(
            self.url, r'http://localhost:\d+/docker/test-\d+/')


class HostRoutingTests(PathRoutingTests):

    def setUp(self):
        self.container_name = 'container-name'
        hostname = self.container_name + '.docker.localhost'

        with open('/etc/hosts') as f:
            etc_hosts = f.read()
            if hostname not in etc_hosts:
                self.fail('In /etc/hosts add entry for "{}"; currently: {}'.format(
                    hostname, etc_hosts
                ))

        self.port = self.free_port()
        self.url = 'http://{}:{}/'.format(hostname, self.port)
        self.tmp_dir = '/tmp/test-' + self.port
        mkdir(self.tmp_dir)
        # Wanted to use mkdtemp, but Docker couldn't see the directory?
        # self.tmp_dir = mkdtemp()
        # chmod(self.tmp_dir, 0777)
        self.process = subprocess.Popen([
            './manage.py', 'runserver', self.port,
            '--settings', 'demo_host_routing.settings'
        ])
        time.sleep(1)
        spec = DockerClientSpec(self.tmp_dir,
                                do_input_json_envvar=True)
        self.client = DockerClientRunWrapper(spec)

    # Tests from superclass are run

    def test_url(self):
        self.assertRegexpMatches(
            self.url, r'http://container-name.docker.localhost:\d+/')
