import boto3
import re
import datetime
import time
import logging
import pytz
from pprint import pformat
import troposphere
from troposphere import ec2, ecs

PADDING = ' ' * len('INFO:root:')


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


def _tail_logs(stack_id, in_progress, complete):
    client = boto3.client('cloudformation')
    stack_description = None
    status = in_progress
    since = datetime.datetime.min.replace(tzinfo=pytz.UTC)
    while status == in_progress:
        time.sleep(1)
        stack_description = client.describe_stacks(StackName=stack_id)
        status = stack_description['Stacks'][0]['StackStatus']
        event_descriptions = \
            client.describe_stack_events(StackName=stack_id)['StackEvents']
        logging.info(_format_events(event_descriptions, since))
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


# def _update_stack(stack_name):
#     stack = boto3.resource('cloudformation').Stack(stack_name)
#     update_stack_response = stack.update(
#         TemplateBody=_create_update_template_json()
#     )
#     stack_id = update_stack_response['StackId']
#     _tail_logs(stack_id=stack_id,
#                in_progress='',
#                complete='')


def create_base_template():
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
    template.add_resource(
        ecs.Cluster('ECS')
    )
    return template


def create_container_template():
    template = troposphere.Template()
    template.add_resource(
        ecs.TaskDefinition(
            'taskDef',
            ContainerDefinitions=[
                ecs.ContainerDefinition(
                    'containerDef',
                    Name='containerDef',
                    Image='nginx:alpine',
                    Memory=100
                )
            ]
        )
    )
    #     ecs.ContainerDefinition(
    #         'containerDef',
    #         #Essential=True, # TODO: what does this do?
    #         Name='containerDef',
    #         # Memory=100,
    #         # Cpu=10, # Causes "Invalid template resource property 'Cpu'"
    #         # With 'Image' I get "Invalid template resource property 'Image'"
    #         # Without, I get "ValueError: Resource Image required"
    #         Image='amazon/amazon-ecs-sample', # TODO: nginx:alpine, or parameterize?
    #         # LogConfiguration=ecs.LogConfiguration(
    #         #     LogDriver='awslogs',
    #         #     # Options={
    #         #     #     'awslogs-group': Ref(web_log_group),
    #         #     #     'awslogs-region': Ref(AWS_REGION),
    #         #     # }
    #         # ),
    #     )
    # )
    return template

# def _create_update_template_json():
#     template = _create_template()  # TODO: Or should this be passed in?
#     container_definition = template.add_resource(
#         ecs.ContainerDefinition(
#             'containerDef',
#             #Essential=True, # TODO: what does this do?
#             Name='containerDef',
#             Memory=100,
#             # Cpu=10, # Causes "Invalid template resource property 'Cpu'"
#             # With 'Image' I get "Invalid template resource property 'Image'"
#             # Without, I get "ValueError: Resource Image required"
#             # Image='amazon/amazon-ecs-sample', # TODO: nginx:alpine, or parameterize?
#             LogConfiguration=ecs.LogConfiguration(
#                 LogDriver='awslogs',
#                 # Options={
#                 #     'awslogs-group': Ref(web_log_group),
#                 #     'awslogs-region': Ref(AWS_REGION),
#                 # }
#             ),
#             # Environment=[
#             #     ecs.Environment(
#             #         Name="AWS_STORAGE_BUCKET_NAME",
#             #         Value=Ref(assets_bucket),
#             #     ),
#             # ]
#             # PortMappings=[PortMapping(
#             #     ContainerPort=web_worker_port,
#             #     HostPort=web_worker_port,
#             # )],
#             # TODO
#         )
#     )
#     task_definition = template.add_resource(
#         ecs.TaskDefinition(
#             'taskDef',
#             ContainerDefinitions=[
#                 container_definition
#             ],
#             # TODO
#         )
#     )
#
#     json = template.to_json()
#     logging.info('Generated "update" json: %s', json)
#     return json

TAGS = {
    'department': 'dbmi',
    'environment': 'test',
    'project': 'django_docker_engine',
    'product': 'refinery'
}


def create_stack(create_template):
    timestamp = re.sub(r'\D', '-', str(datetime.datetime.now()))
    prefix = 'django-docker-'
    name = prefix + timestamp

    json = create_template().to_json()
    logging.info(json)
    _create_stack(name, json, TAGS)
    return name


# def start_container(stack_name, docker_image):
#     stack = boto3.resource('cloudformation').Stack(stack_name)
#     # stack.update(
#     #     TemplateBody=_create_update_template_json()
#     # )


def delete_stack(name):
    logging.info('delete_stack: %s', name)
    client = boto3.client('cloudformation')
    client.delete_stack(
        StackName=name
    )


if __name__ == '__main__':
    name = create_stack()
    print(name)
