#!/usr/bin/env python
import boto3
import re
import datetime
import time
import logging
import pytz
import collections
import requests
import sys
import subprocess
import troposphere
from pprint import pformat
from troposphere import (
    ec2, Ref, Output, Base64,
)


def _uniq_id():
    timestamp = re.sub(r'\D', '-', str(datetime.datetime.now()))
    prefix = 'django-docker-'
    return prefix + timestamp


_DOCKERD_PORT = 2375
_SSH_PORT = 22
_UNIQ_ID = _uniq_id()
_CLUSTER = 'EcsCluster-' + _UNIQ_ID
_EC2_OUTPUT_KEY = 'ec2'
_EC2_REF = 'EC2'
_PADDING = ' ' * len('INFO:root:123: ')


def _format_event(event):
    formatted = '{:<20} {:<27} {} {}'.format(
        event['ResourceStatus'],
        event['ResourceType'],
        event['LogicalResourceId'],
        event['PhysicalResourceId'])
    reason = event.get('ResourceStatusReason')
    if reason:
        formatted += '\n' + _PADDING + reason
    return formatted


def _format_events(events, since, formatter):
    return ('\n' + _PADDING). \
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


def _create_ec2_template(
        key_name,
        host_cidr,
        ami,
        instance_type,
        extra_security_groups,
        enable_ssh):
    if not(key_name):
        raise RuntimeError('key_name is required')
    if not (host_cidr or extra_security_groups):
        raise RuntimeError(
            'Either a CIDR or a AWS Security Group must be given')
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
            FromPort=_DOCKERD_PORT,
            ToPort=_DOCKERD_PORT,
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
                FromPort=_SSH_PORT,
                ToPort=_SSH_PORT,
                CidrIp='0.0.0.0/0'  # SSH is protected by key
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
    all_security_groups = list(extra_security_groups) + \
        [default_security_group]
    warning = 'WARNING: dockerd should not be open unless ' \
              'security is provided at a higher level'
    command = "echo 'OPTIONS=\"$OPTIONS -H tcp://0.0.0.0:2375\" # {}' " \
              ">> /etc/sysconfig/docker".format(warning)

    template.add_resource(
        ec2.Instance(
            _EC2_REF,
            SecurityGroups=[Ref(sg) for sg in all_security_groups],
            # ImageId='ami-c58c1dd3', # plain Amazon Linux AMI, needs docker installed
            # ImageId='ami-80861296', # Ubuntu ebs, hvm; "Permission denied (publickey)"
            ImageId=ami,
            InstanceType=instance_type,
            KeyName=key_name,

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
            _EC2_OUTPUT_KEY,
            Value=Ref(_EC2_REF)
        )
    )
    return template


def _create_stack(create_template, tags={}, **args):
    json = create_template(**args).to_json()
    logging.info(json)
    stack_name = create_template.__name__.replace('_', '') + '-' + _UNIQ_ID

    expanded_tags = _expand_tags(tags)
    client = boto3.client('cloudformation')

    create_stack_response = client.create_stack(
        StackName=stack_name,
        TemplateBody=json,
        Tags=expanded_tags
    )
    stack_id = create_stack_response['StackId']
    _tail_logs(stack_id=stack_id,
               in_progress='CREATE_IN_PROGRESS',
               complete='CREATE_COMPLETE')
    return stack_id


def _get_ip_for_stack(stack_id):
    stack = boto3.resource('cloudformation').Stack(stack_id)
    logging.info('stack.output: %s', stack.outputs)

    ec2_ids = [
        output['OutputValue']
        for output in stack.outputs
        if output['OutputKey'] == _EC2_OUTPUT_KEY
    ]
    assert len(ec2_ids) == 1, 'Should be exactly one ec2_id: %s' % ec2_ids
    ec2_id = ec2_ids[0]
    logging.info('ec2 ID: %s', ec2_id)

    instance = boto3.resource('ec2').Instance(ec2_id)
    ip = instance.public_ip_address
    logging.info('IP: %s', ip)
    return ip


def build(host_cidr,
          tags,
          enable_ssh=False,
          key_name='django_docker_cloudformation',
          ami='ami-275ffe31',  # ECS Optimized
          instance_type='t2.nano',
          extra_security_groups=()):
    """
    Builds a Cloudformation stack with a single EC2 running Docker.
    Access will be restricted, either to originating IP, or to
    an AWS Security Group.

    Returns the stack id, and a TCP URL for use with the
    "-H" parameter of the Docker CLI.
    """
    stack_id = _create_stack(
        _create_ec2_template,
        tags=tags,
        host_cidr=host_cidr,
        key_name=key_name,
        ami=ami,
        instance_type=instance_type,
        extra_security_groups=extra_security_groups,
        enable_ssh=enable_ssh)
    stack_ip = _get_ip_for_stack(stack_id)
    docker_h_url = 'tcp://{}:{}'.format(stack_ip, _DOCKERD_PORT)
    docker_command_tokens = ['docker', '-H', docker_h_url, 'info']

    docker_output = None
    t = 0
    while not docker_output and t < 60:
        t += 1
        try:
            docker_output = subprocess.check_output(docker_command_tokens)
        except subprocess.CalledProcessError:
            time.sleep(1)
    if not docker_output:
        raise RuntimeError('Docker never came up')

    logging.info(' '.join(docker_command_tokens))
    logging.info(docker_output)

    if enable_ssh:
        commands = '; '.join([
            'cat /etc/sysconfig/docker',
            'echo',
            'ps aux | grep dockerd'
        ])
        ssh_command = 'ssh -i {}.pem ec2-user@{} \'{}\'' \
            .format(key_name, stack_ip, commands)
        logging.info(ssh_command)

    DockerStackInfo = collections.namedtuple('DockerStackInfo', ['id', 'url'])
    return DockerStackInfo(id=stack_id, url=docker_h_url)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    args = sys.argv[1:]

    if args == ['--create']:
        host_ip = requests.get('http://ipinfo.io/ip').text.strip()
        host_cidr = host_ip + '/32'
        tags = {
            'department': 'dbmi',
            'environment': 'test',
            'project': 'django_docker_engine',
            'product': 'refinery'
        }
        info = build(host_cidr=host_cidr, tags=tags, enable_ssh=True)
        print 'export DOCKER_HOST={} DOCKER_STACK_ID={}' \
            .format(info.url, info.id)
    elif len(args) == 2 and args[0] == '--delete':
        stack_id = args[1]
        stack = boto3.resource('cloudformation').Stack(stack_id)
        stack.delete()
    else:
        print 'Usage: $( {name} --create ) \n\tor\n\t{name} --delete STACK_ID' \
              .format(name=sys.argv[0])
        print '--create: Creates a CloudFormation stack. ' \
              'A shell statement is returned on STDOUT with the connection information ' \
              'for Docker Engine, and the ID of the stack.'
        print '--delete: Deletes a stack, given its ID.'

        exit(1)
