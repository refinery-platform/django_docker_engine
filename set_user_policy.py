#!/usr/bin/env python
import boto3
import json


class PolicySetter():
    def __init__(self, user):
        self.__user = boto3.resource('iam').User(user)

    def set_policies(self):
        self.__set_managed_policies()
        self.__set_inline_policies()

    def __set_managed_policies(self):
        prefix = 'arn:aws:iam::aws:policy'
        policies = [
            # TODO: Add notes about why these are needed.
            'AmazonEC2ContainerRegistryFullAccess',
            'AmazonEC2ContainerServiceforEC2Role',
            'AmazonEC2ContainerServiceRole'
        ]
        for policy in policies:
            arn = prefix + '/' + policy
            self.__user.attach_policy(PolicyArn=arn)

    def __set_inline_policies(self):
        actions = {
            'CreateAndDeleteKeyPair':
                ["ec2:CreateKeyPair", "ec2:DeleteKeyPair"],
            'CreateAndDeleteSecurityGroup':
                ['ec2:CreateSecurityGroup', 'ec2:DeleteSecurityGroup'],
            'RunAndTerminateInstances':
                ['ec2:RunInstances', 'ec2:TerminateInstances'],
            'CreateAndDeleteLogGroup':
                ['logs:CreateLogGroup', 'logs:DeleteLogGroup'],
            'LogsAllowEverything':
                ['logs:*'], # TODO: Tighten
        }
        for name in actions:
            full_doc = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        # "Sid": "Stmt1491412963000",
                        "Effect": "Allow",
                        "Action": actions[name],
                        "Resource": ["*"] # TODO: Tighten
                    }
                ]
            }
            user_policy = self.__user.Policy(name)
            user_policy.put(json.dumps(full_doc))


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        PolicySetter(sys.argv[1]).set_policies()
    else:
        print('USAGE: %s AWS_USERNAME' % sys.argv[0])
        print('Grants to the specified user the privs necessary to run AWS-ECS tests')
        import doctest
        doctest.testmod()