import unittest
import logging
from django_docker_engine.container_managers.cloudformation_utils import (
    create_stack,
    delete_stack,
    host_port,
    create_base_template,
    create_container_template
)


class CloudFormationTests(unittest.TestCase):
    def setUp(self):
        # TODO: Is there a better idiom for this?
        logging.basicConfig(level=logging.INFO)


    def test_start_container(self):
        self.base_stack_name = create_stack(create_base_template)
        # TODO: self.addCleanup(delete_stack, self.base_stack_name)

        self.container_stack_name = create_stack(create_container_template)
        # TODO: self.addCleanup(delete_stack, self.container_stack_name)

        # TODO: export port and hit nginx?
        print(host_port(self.container_stack_name))