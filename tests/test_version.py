import unittest
import requests
import os


class VersionTests(unittest.TestCase):

    def test_version_has_been_incremented(self):
        version_re = r'^\d+\.\d+\.\d+$'
        r = requests.get(
            'https://pypi.python.org/pypi/django-docker-engine/json')
        pypi_versions = r.json()['releases'].keys()

        for v in pypi_versions:
            self.assertRegexpMatches(v, version_re)

        version_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'django_docker_engine',
            'VERSION.txt'
        )
        local_version = open(version_path).read().strip()

        self.assertRegexpMatches(local_version, version_re)

        self.assertNotIn(local_version, pypi_versions)
