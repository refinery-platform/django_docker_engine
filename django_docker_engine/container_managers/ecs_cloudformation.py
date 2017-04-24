from base import BaseManager, BaseContainer
import boto3
import re
import datetime
import time
import logging
import pytz
from pprint import pformat
import troposphere
import troposphere.ec2 as ec2


class EcsCloudFormationManager(BaseManager):

    def __init__(self,
                 key_pair_name=None,
                 cluster_name=None,
                 security_group_id=None,
                 instance_id=None,
                 log_group_name=None):
        raise NotImplementedError()

    def run(self, image_name, cmd, **kwargs):
        raise NotImplementedError()

    def get_url(self, container_name):
        raise NotImplementedError()

    def list(self, filters={}):
        raise NotImplementedError()


class EcsCloudFormationContainer(BaseContainer):

    def remove(self):
        raise NotImplementedError()

    def logs(self):
        raise NotImplementedError()


def _format_events(events, since):
    log_prefix_width = 10
    return ('\n'+' '*log_prefix_width).\
        join(['{:<20} {:<27} {:<42} {:<70}'.format(
            event['ResourceStatus'],
            event['ResourceType'],
            event['LogicalResourceId'],
            event['PhysicalResourceId']) for event in events[::-1]
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
        since = event_descriptions[0]['Timestamp']

    if status != CREATE_COMPLETE:
        logging.warn('Stack creation not successful: %s', pformat(stack_description))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    timestamp = re.sub(r'\D', '-', str(datetime.datetime.now()))
    prefix = 'django-docker-'
    name = prefix + timestamp

    tags = {
        'department': 'dbmi',
        'environment': 'test',
        'project': 'django_docker_engine',
        'product': 'refinery'
    }

    template = troposphere.Template()
    template.add_resource(
        ec2.SecurityGroup(
            'highports',
            GroupDescription='All high ports are open'
        )
    )

    json = template.to_json()
    logging.info(json)

    _create_stack(name, json, tags)
