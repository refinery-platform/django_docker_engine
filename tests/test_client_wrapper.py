import unittest

from django_docker_engine.docker_utils import DockerClientWrapper
from django_docker_engine.container_managers.docker_engine import (
    PossiblyOutOfDiskSpace)

class ClientWrapperTests(unittest.TestCase):
    # It seems that most of the methods of DockerClientWrapper
    # are hit by test_demo.py, but more direct tests would be better.

    def test_pull_missing_image(self):
        # Because all the image names are hardcoded, it's unlikely that the
        # image really doesn't exist... It's more likely that we got this
        # error because we ran out of disk space: hence the exception name.
        with self.assertRaises(PossiblyOutOfDiskSpace):
            DockerClientWrapper().pull('no-such-image')