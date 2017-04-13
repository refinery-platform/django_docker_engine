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
            'service-role/AmazonEC2ContainerServiceforEC2Role',
            'service-role/AmazonEC2ContainerServiceRole'
        ]
        for policy in policies:
            arn = prefix + '/' + policy
            self.__user.attach_policy(PolicyArn=arn)
            print(policy)

    def __set_inline_policies(self):
        # Alternatively, could create new managed policies,
        # either for each of these, or all of them.
        actions = {
            'CreateAndDeleteKeyPair':
                ["ec2:CreateKeyPair", "ec2:DeleteKeyPair"],
            'CreateAndDeleteSecurityGroup':
                ['ec2:CreateSecurityGroup', 'ec2:DeleteSecurityGroup'],
            'RunAndTerminateInstances':
                ['ec2:RunInstances', 'ec2:TerminateInstances'],
            'AuthorizeSecurityGroupIngressAndEgress':
                ['ec2:AuthorizeSecurityGroupEgress', 'ec2:AuthorizeSecurityGroupIngress'],
            'IamPassRole':  # Assign a role to ECS EC2 instance
                ['iam:PassRole'],
            'EcsAllowEverything':
                ['ecs:*'],  # TODO: Tighten
            'CreateAndDeleteLogGroup':
                ['logs:CreateLogGroup', 'logs:DeleteLogGroup'],
            # 'LogsAllowEverything':
            #     ['logs:*'], # TODO: Tighten
        }
        for name in actions:
            full_doc = {
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": actions[name],
                        "Resource": ["*"]  # TODO: Tighten
                    }
                ]
            }
            user_policy = self.__user.Policy(name)
            user_policy.put(PolicyDocument=json.dumps(full_doc))
            print(actions[name])


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        PolicySetter(sys.argv[1]).set_policies()
    else:
        print('USAGE: %s AWS_USERNAME' % sys.argv[0])
        print('Grants to the specified user the privs necessary to run AWS-ECS tests')
