import boto3
import re
import datetime
import time
import logging
import pytz
from pprint import pformat
import troposphere
from troposphere import (
    ec2, Ref, Output, Base64, Join,
)
import requests
import sys
import subprocess

PADDING = ' ' * len('INFO:root:123: ')


def _format_event(event):
    formatted = '{:<20} {:<27} {} {}'.format(
        event['ResourceStatus'],
        event['ResourceType'],
        event['LogicalResourceId'],
        event['PhysicalResourceId'])
    reason = event.get('ResourceStatusReason')
    if reason:
        formatted += '\n' + PADDING + reason
    return formatted


def _format_events(events, since, formatter):
    return ('\n' + PADDING). \
        join([formatter(event) for event in events[::-1]
              if event['Timestamp'] > since])


def _readable_events(events, since):
    return _format_events(events, since, _format_event)


def _raw_events(events, since):
    return _format_events(events, since, pformat)


def _expand_tags(tags):
    return [{
                'Key': key,
                'Value': tags[key]
            } for key in tags]


def _tail_logs(stack_id, in_progress, complete, timeout=300, increment=2):
    client = boto3.client('cloudformation')
    stack_description = None
    status = in_progress
    since = datetime.datetime.min.replace(tzinfo=pytz.UTC)
    t = 0
    while status == in_progress:
        if t > timeout:
            raise RuntimeError('Timeout: After %s, %s is still %s' % (
                timeout, stack_id, in_progress
            ))
        t += increment
        time.sleep(increment)
        stack_description = client.describe_stacks(StackName=stack_id)
        status = stack_description['Stacks'][0]['StackStatus']
        event_descriptions = \
            client.describe_stack_events(StackName=stack_id)['StackEvents']
        logging.info('%3s: %s', t, _readable_events(event_descriptions, since))
        logging.debug(_raw_events(event_descriptions, since))
        since = event_descriptions[0]['Timestamp']
    if status != complete:
        raise RuntimeError(
            'Stack is %s instead of %s: %s' %
            (status, complete, pformat(stack_description)))


def _create_stack(name, json, tags):
    expanded_tags = _expand_tags(tags)
    client = boto3.client('cloudformation')

    create_stack_response = client.create_stack(
        StackName=name,
        TemplateBody=json,
        Tags=expanded_tags
    )
    stack_id = create_stack_response['StackId']
    _tail_logs(stack_id=stack_id,
               in_progress='CREATE_IN_PROGRESS',
               complete='CREATE_COMPLETE')

DOCKERD_PORT = 2375
SSH_PORT = 22

def create_ec2_template(
        host_cidr=None,
        extra_security_groups=(),
        enable_ssh=False):
    if not (host_cidr or extra_security_groups):
        raise RuntimeError('Either a CIDR or a AWS Security Group must be given')
    sg_cidr = host_cidr or '0.0.0.0/0'

    min_port = 32768
    max_port = 65535
    ecs_container_agent_port = 51678
    # For now, we are using an ECS image, even if we are not using ECS.

    security_group_rules = [
        ec2.SecurityGroupRule(
            IpProtocol='tcp',
            FromPort=min_port,
            ToPort=ecs_container_agent_port - 1,
            CidrIp=sg_cidr,
        ),
        ec2.SecurityGroupRule(
            IpProtocol='tcp',
            FromPort=ecs_container_agent_port + 1,
            ToPort=max_port,
            CidrIp=sg_cidr
        ),
        ec2.SecurityGroupRule(
            IpProtocol='tcp',
            FromPort=DOCKERD_PORT,
            ToPort=DOCKERD_PORT,
            CidrIp=sg_cidr
        )
        # Uncomment for ECS:
        # ec2.SecurityGroupRule(
        #     IpProtocol='tcp',
        #     FromPort=ecs_container_agent_port,
        #     ToPort=ecs_container_agent_port,
        #     CidrIp=sg_cidr
        # )
    ]
    if enable_ssh:
        security_group_rules.append(
            ec2.SecurityGroupRule(
                IpProtocol='tcp',
                FromPort=SSH_PORT,
                ToPort=SSH_PORT,
                CidrIp='0.0.0.0/0' # SSH is protected by key
            ),
        )

    template = troposphere.Template()
    default_security_group = template.add_resource(
        ec2.SecurityGroup(
            'SG',
            GroupDescription='All high ports are open',
            SecurityGroupIngress=security_group_rules
        )
    )
    all_security_groups = list(extra_security_groups) + [default_security_group]
    warning = 'WARNING: dockerd should not be open unless security is provided at a higher level'
    command = "echo 'OPTIONS=\"$OPTIONS -H tcp://0.0.0.0:2375\" # {}' >> /etc/sysconfig/docker" \
        .format(warning)

    template.add_resource(
        ec2.Instance(
            EC2_REF,
            SecurityGroups=[Ref(sg) for sg in all_security_groups],
            # ImageId='ami-c58c1dd3', # plain Amazon Linux AMI, needs docker installed
            # ImageId='ami-80861296', # Ubuntu ebs, hvm; "Permission denied (publickey)"
            ImageId='ami-275ffe31',  # ECS Optimized
            InstanceType='t2.nano',

            KeyName='django_docker_cloudformation',
            # On a fresh install, this keypair needs to exist.

            UserData=Base64('\n'.join([
                '#!/bin/bash -xe',
                command,
                'service docker restart'
            ])),

            # These are critical for ECS, but we're not using ECS:
            #
            # IamInstanceProfile='ecsInstanceRole', # Created by hand
            # UserData=Base64(Join('', [
            #     '#!/bin/bash -xe\n',
            #     'echo ECS_CLUSTER=',
            #     Ref(cluster),
            #     ' >> /etc/ecs/ecs.config\n'
            # ])),
        )
    )
    template.add_output(
        Output(
            EC2_OUTPUT_KEY,
            Value=Ref(EC2_REF)
        )
    )
    return template

KEY_NAME = 'django_docker_cloudformation'
EC2_REF = 'EC2'

TAGS = {
    'department': 'dbmi',
    'environment': 'test',
    'project': 'django_docker_engine',
    'product': 'refinery'
}


def _uniq_id():
    timestamp = re.sub(r'\D', '-', str(datetime.datetime.now()))
    prefix = 'django-docker-'
    return prefix + timestamp


UNIQ_ID = _uniq_id()
CLUSTER = 'EcsCluster-' + UNIQ_ID

EC2_OUTPUT_KEY = 'ec2'

def create_stack(create_template, **args):
    json = create_template(**args).to_json()
    logging.info(json)
    stack_id = create_template.__name__.replace('_', '-') + '-' + UNIQ_ID
    _create_stack(stack_id, json, TAGS)
    return stack_id

def get_ip_for_stack(stack_id):
    stack = boto3.resource('cloudformation').Stack(stack_id)
    logging.info('stack.output: %s', stack.outputs)

    ec2_ids = [
        output['OutputValue']
        for output in stack.outputs
        if output['OutputKey'] == EC2_OUTPUT_KEY
        ]
    assert len(ec2_ids) == 1, 'Should be exactly one ec2_id: %s' % ec2_ids
    ec2_id = ec2_ids[0]
    logging.info('ec2 ID: %s', ec2_id)

    instance = boto3.resource('ec2').Instance(ec2_id)
    ip = instance.public_ip_address
    logging.info('IP: %s', ip)

    return ip

def delete_stack(name):
    logging.info('delete_stack: %s', name)
    client = boto3.client('cloudformation')
    client.delete_stack(StackName=name)


if __name__ == "__main__":
    if len(sys.argv) != 1:
        print('No arguments: Creates a new EC2 with CloudFormation')
        exit(1)

    logging.basicConfig(level=logging.INFO)

    host_ip = requests.get('http://ipinfo.io/ip').text.strip()
    host_cidr = host_ip + '/32'
    enable_ssh = True  # Helps with debugging, but default should be False
    stack_id = create_stack(
        create_ec2_template,
        host_cidr=host_cidr,
        enable_ssh=enable_ssh)
    stack_ip = get_ip_for_stack(stack_id)

    docker_command_tokens = [
        'docker', '-H',
        'tcp://{}:{}'.format(stack_ip, DOCKERD_PORT),
        'info']

    docker_output = None
    t = 0
    while not docker_output and t < 30:
        t += 1
        try:
            docker_output = subprocess.check_output(docker_command_tokens)
        except subprocess.CalledProcessError:
            pass
    if not docker_output:
        raise RuntimeError('Docker never came up')

    logging.info(' '.join(docker_command_tokens))
    logging.info(docker_output)
    if enable_ssh:
        commands = '; '.join([
            'cat /etc/sysconfig/docker',
            'echo'
            'ps aux | grep dockerd'
        ])
        ssh_command = 'ssh -i ~/.ssh/{}.pem ec2-user@{} \'{}\'' \
            .format(KEY_NAME, stack_ip, commands)
        logging.info(ssh_command)
