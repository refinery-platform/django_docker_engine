import unittest
import logging
from django_docker_engine.container_managers.cloudformation_utils import (
    create_default_stack,
    start_container,
    delete_stack
)


class CloudFormationTests(unittest.TestCase):
    def setUp(self):
        # TODO: Is there a better idiom for this?
        logging.basicConfig(level=logging.INFO)

    def addCleanup(self):
        delete_stack(self.stack_name)

    def test_start_container(self):
        self.stack_name = create_default_stack()
        start_container(self.stack_name, 'nginx:alpine')
