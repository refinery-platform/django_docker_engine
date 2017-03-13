from django.test import TestCase
import docker

class DockerTests(TestCase):
    def test_hello_world(self):
        # This seems to work, but it takes forever to download the image the first time.
        # Is there something I should do differently?
        client = docker.from_env()
        output = client.containers.run("ubuntu", "echo hello world")
        self.assertEqual(output, 'hello world\n')