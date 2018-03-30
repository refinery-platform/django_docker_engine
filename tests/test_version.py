import os
import unittest

import requests


class VersionTests(unittest.TestCase):

    try:
        assertRegex
    except NameError:  # Python 2 fallback
        def assertRegex(self, s, re):
            self.assertRegexpMatches(s, re)

    def test_version_has_been_incremented(self):
        if not hasattr(self, 'assertRegexp'):
            self.assertRegexp = self.assertRegexpMatches

        version_re = r'^\d+\.\d+\.\d+$'
        r = requests.get(
            'https://pypi.python.org/pypi/django-docker-engine/json')
        pypi_versions = list(r.json()['releases'].keys())

        for v in pypi_versions:
            self.assertRegex(v, version_re)

        version_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'django_docker_engine',
            'VERSION.txt'
        )
        local_version = open(version_path).read().strip()

        self.assertRegex(local_version, version_re)

        self.assertNotIn(local_version, pypi_versions)
