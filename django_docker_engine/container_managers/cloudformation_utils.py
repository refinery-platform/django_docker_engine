import boto3
import re
import datetime
import time
import logging
import pytz
from pprint import pformat
import troposphere
import troposphere.ec2 as ec2
# import troposphere.ecs as ecs

PADDING = ' ' * len('INFO:root:')


def _format_event(event):
    formatted = '{:<20} {:<27} {:<42} {:<70}'.format(
        event['ResourceStatus'],
        event['ResourceType'],
        event['LogicalResourceId'],
        event['PhysicalResourceId']).strip()
    reason = event.get('ResourceStatusReason')
    if reason:
        formatted += '\n' + PADDING + reason
    return formatted


def _format_events(events, since):
    return ('\n' + PADDING). \
        join([_format_event(event) for event in events[::-1]
              if event['Timestamp'] > since])


def _raw_events(events, since):
    log_prefix_width = 10
    return ('\n' + ' ' * log_prefix_width). \
        join([pformat(event) for event in events[::-1]
              if event['Timestamp'] > since])


def _expand_tags(tags):
    return [{
                'Key': key,
                'Value': tags[key]
            } for key in tags]


def _create_stack(name, json, tags):
    expanded_tags = _expand_tags(tags)
    client = boto3.client('cloudformation')

    create_stack_response = client.create_stack(
        StackName=name,
        TemplateBody=json,
        Tags=expanded_tags
    )
    stack_id = create_stack_response['StackId']

    CREATE_IN_PROGRESS = 'CREATE_IN_PROGRESS'
    CREATE_COMPLETE = 'CREATE_COMPLETE'

    stack_description = None
    status = CREATE_IN_PROGRESS
    since = datetime.datetime.min.replace(tzinfo=pytz.UTC)
    while status == CREATE_IN_PROGRESS:
        time.sleep(1)
        stack_description = client.describe_stacks(StackName=stack_id)
        status = stack_description['Stacks'][0]['StackStatus']
        event_descriptions = \
            client.describe_stack_events(StackName=stack_id)['StackEvents']
        logging.info(_format_events(event_descriptions, since))
        logging.debug(_raw_events(event_descriptions, since))
        since = event_descriptions[0]['Timestamp']

    if status != CREATE_COMPLETE:
        logging.warn('Stack creation not successful: %s', pformat(stack_description))


def _create_template_json():
    min_port = 32768
    max_port = 65535
    ecs_container_agent_port = 51678

    template = troposphere.Template()
    security_group = template.add_resource(
        ec2.SecurityGroup(
            'SG',
            GroupDescription='All high ports are open',
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort=min_port,
                    ToPort=ecs_container_agent_port - 1,
                    CidrIp='0.0.0.0/0',
                ),
                ec2.SecurityGroupRule(
                    IpProtocol='tcp',
                    FromPort=ecs_container_agent_port + 1,
                    ToPort=max_port,
                    CidrIp='0.0.0.0/0'
                ),
            ]
        )
    )
    template.add_resource(
        ec2.Instance(
            'EC2',
            SecurityGroups=[troposphere.Ref(security_group)],
            ImageId='ami-275ffe31',
            InstanceType='t2.nano'
        )
    )
    # template.add_resource(
    #     ecs.Cluster(
    #         'ECS',
    #
    #     )
    # )

    json = template.to_json()
    logging.info(json)
    return json


def create_default_stack():
    timestamp = re.sub(r'\D', '-', str(datetime.datetime.now()))
    prefix = 'django-docker-'
    name = prefix + timestamp

    json = _create_template_json()
    tags = {
        'department': 'dbmi',
        'environment': 'test',
        'project': 'django_docker_engine',
        'product': 'refinery'
    }
    _create_stack(name, json, tags)
    return name


def delete_stack(name):
    client = boto3.client('cloudformation')
    client.delete_stack(
        StackName=name
    )


if __name__ == '__main__':
    name = create_default_stack()
    print(name)
