==========
AWS Extras
==========

Before each test run, the environment variable DOCKER_HOST is checked:
If unset, the local Docker engine will be used, but it could also refer
to an AWS instance.

You'll need a django_docker_cloudformation.pem and sufficient AWS privs.

The tests shouldn't leak AWS resources, but if they do:

- `CloudFormation Stacks <https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks?filter=active>`_
- `Security Groups <https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#SecurityGroups:search=django_docker_;sort=groupId>`_
- `EC2 Instances <https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Instances:search=django_docker_;sort=keyName>`_

Clean up of stacks is easy on the command line::

    aws cloudformation list-stacks \
        --query 'StackSummaries[].[StackName,StackStatus]' \
        --output text | \
    grep -v DELETE_COMPLETE | \
    grep django-docker | \
    cut -f 1 | \
    xargs -n 1 aws cloudformation delete-stack --stack-name

If lower level resources have leaked, they can be handled independently::

    aws ec2 describe-instances \
        --filters Name=tag:project,Values=django_docker_engine \
        --query 'Reservations[].Instances[].[InstanceId]' \
        --output text | \
    xargs aws ec2 terminate-instances --instance-ids

    aws ec2 describe-security-groups \
        --filters Name=description,Values='Security group for django_docker_engine' \
        --query 'SecurityGroups[].[GroupId]' \
        --output text | \
    xargs -n 1 aws ec2 delete-security-group --group-id