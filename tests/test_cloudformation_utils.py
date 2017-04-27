import logging
import unittest

from tests.cloudformation_utils import (
    create_stack,
    create_ec2_template,
    delete_stack
)


class CloudFormationTests(unittest.TestCase):
    def setUp(self):
        # TODO: Is there a better idiom for this?
        logging.basicConfig(level=logging.INFO)

    def test_start_container(self):
        self.base_stack_name = create_stack(create_ec2_template)
        self.addCleanup(delete_stack, self.base_stack_name)
