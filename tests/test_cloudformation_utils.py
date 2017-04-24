import unittest
from django_docker_engine.container_managers.cloudformation_utils \
    import create_default_stack, delete_stack


class CloudFormationTests(unittest.TestCase):
    def setUp(self):
        self.stack_name = create_default_stack()

    def tearDown(self):
        delete_stack(self.stack_name)

    def test_placeholder(self):
        pass
