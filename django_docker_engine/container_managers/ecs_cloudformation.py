from base import BaseManager, BaseContainer
import os
import boto3
import re
import datetime
import time
from pprint import pprint


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


if __name__ == '__main__':
    timestamp = re.sub(r'\D', '-', str(datetime.datetime.now()))
    prefix = 'django-docker-'
    name = prefix + timestamp

    tags = {
        'department': 'dbmi',
        'environment': 'test',
        'project': 'django_docker_engine',
        'product': 'refinery'
    }
    expanded_tags = [{
                         'Key': key,
                         'Value': tags[key]
                     } for key in tags]

    path = os.path.join(os.path.dirname(__file__), 'stack.json')
    json = open(path).read()
    client = boto3.client('cloudformation')

    create_stack_response = client.create_stack(
        StackName=name,
        TemplateBody=json,
        Tags=expanded_tags
    )
    stack_id = create_stack_response['StackId']

    CREATE_IN_PROGRESS = 'CREATE_IN_PROGRESS'
    CREATE_COMPLETE = 'CREATE_COMPLETE'

    describe_stack_response = None
    status = CREATE_IN_PROGRESS
    while status == CREATE_IN_PROGRESS:
        time.sleep(1)
        describe_create = client.describe_stacks(StackName=stack_id)
        status = describe_create['Stacks'][0]['StackStatus']

    pprint(describe_create)

    if status != CREATE_COMPLETE:
        describe_events = client.describe_stack_events(StackName=stack_id)
        pprint(describe_events)
