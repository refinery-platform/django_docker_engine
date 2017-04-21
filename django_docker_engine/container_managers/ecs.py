import boto3
import logging
import datetime
import re
import time
from base import BaseManager, BaseContainer
from collections import namedtuple
from argparse import ArgumentParser


class EcsManager(BaseManager):

    DEFAULT_INSTANCE_TYPE = 't2.nano'
    DEFAULT_REGION = 'us-east-1'
    # us-east-1: amzn-ami-2016.09.g-amazon-ecs-optimized
    DEFAULT_AMI_ID = 'ami-275ffe31'
    DEFAULT_ROLE_ARN = \
        'arn:aws:iam::100836861126:instance-profile/ecsInstanceRole'
    TIMESTAMP = re.sub(r'\D', '_', str(datetime.datetime.now()))
    PREFIX = 'django_docker_'
    DEFAULT = PREFIX + TIMESTAMP
    TIMEOUT = 60

    DEFAULT_TAGS = {
        'department': 'dbmi',
        'environment': 'test',
        'project': 'django_docker_engine',
        'product': 'refinery'
    }

    def __init__(self,
                 key_pair_name=None,
                 cluster_name=None,
                 security_group_id=None,
                 instance_id=None,
                 log_group_name=None):
        """
        Specify a key pair, cluster, and security group to use,
        or new ones will be created with names based on the given prefix.
        """
        self._ecs_client = boto3.client('ecs')
        self._ec2_client = boto3.client('ec2')
        self._ec2_resource = boto3.resource('ec2')

        if (
                instance_id and
                security_group_id and
                cluster_name and
                key_pair_name and
                log_group_name):
            self._instance_id = instance_id
            self._cluster_name = cluster_name
            self._security_group_id = security_group_id
            self._key_pair_name = key_pair_name
            self._log_group_name = log_group_name
        elif not (instance_id or
                  security_group_id or
                  cluster_name or
                  key_pair_name or
                  log_group_name):
            # TODO: Will we ever use this branch?
            aws_ids = EcsManager.create_instance(
                key_pair_name=key_pair_name,
                cluster_name=cluster_name,
                security_group_id=security_group_id
            )
            self._key_pair_name = aws_ids.key_pair_name
            self._cluster_name = aws_ids.cluster_name
            self._security_group_id = aws_ids.security_group_id
            self._instance_id = aws_ids.instance_id
            self._log_group_name = aws_ids.log_group_name
        else:
            raise RuntimeError(
                'All IDs must be given, or none; Instead we have {}'
                .format({
                        'security_group_id': security_group_id,
                        'cluster_name': cluster_name,
                        'key_pair_name': key_pair_name,
                        'log_group_name': log_group_name
                        })
            )

    @staticmethod
    def _create_key_pair(key_pair_name):
        response = boto3.client('ec2').create_key_pair(KeyName=key_pair_name)
        assert(response['KeyName'] == key_pair_name)
        return key_pair_name

    @staticmethod
    def _create_cluster(cluster_name):
        response = boto3.client('ecs').create_cluster(clusterName=cluster_name)
        assert(response['cluster']['status'] == 'ACTIVE')
        return cluster_name

    @staticmethod
    def _create_security_group(security_group_name):
        response = boto3.client('ec2').create_security_group(
            GroupName=security_group_name,
            Description='Security group for django_docker_engine'
        )
        security_group_id = response['GroupId']
        security_group = boto3.resource('ec2').SecurityGroup(security_group_id)

        # http://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html
        # Ephermal port range has changed in different versions;
        # This is a super-set.
        min_port = 32768
        max_port = 65535
        ecs_container_agent_port = 51678

        # Fails silently if Cidr is missing.
        security_group.authorize_ingress(
            IpProtocol='tcp',
            CidrIp='0.0.0.0/0',
            FromPort=min_port,
            ToPort=ecs_container_agent_port-1
        )
        security_group.authorize_ingress(
            IpProtocol='tcp',
            CidrIp='0.0.0.0/0',
            FromPort=ecs_container_agent_port + 1,
            ToPort=max_port
        )
        return security_group_id

    @staticmethod
    def _create_log_group(log_group_name):
        boto3.client('logs').create_log_group(logGroupName=log_group_name)
        return log_group_name

    @staticmethod
    def create_instance(
            key_pair_name=None,
            security_group_id=None,
            cluster_name=None,
            log_group_name=None,
            ami_id=DEFAULT_AMI_ID,
            instance_profile_arn=DEFAULT_ROLE_ARN,
            instance_type=DEFAULT_INSTANCE_TYPE,
            tags=DEFAULT_TAGS):
        key_pair_name = key_pair_name or \
            EcsManager._create_key_pair(EcsManager.DEFAULT)
        cluster_name = cluster_name or \
            EcsManager._create_cluster(EcsManager.DEFAULT)
        security_group_id = security_group_id or \
            EcsManager._create_security_group(EcsManager.DEFAULT)
        log_group_name = log_group_name or \
            EcsManager._create_log_group(EcsManager.DEFAULT)
        user_data = '\n'.join([
            '#!/bin/bash',
            'echo ECS_CLUSTER={} >> /etc/ecs/ecs.config'.format(
                cluster_name
            )])
        expanded_tags = [{
                            'Key': key,
                            'Value': tags[key]
                        } for key in tags]
        response = boto3.client('ec2').run_instances(
            ImageId=ami_id,
            MinCount=1,
            MaxCount=1,
            InstanceType=instance_type,
            KeyName=key_pair_name,
            UserData=user_data,
            NetworkInterfaces=[
                {
                    'DeviceIndex': 0,
                    'AssociatePublicIpAddress': True,
                    'Groups': [security_group_id]
                }
            ],
            IamInstanceProfile={
                'Arn': instance_profile_arn
            },
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': expanded_tags
                }
            ]
        )

        instance_id = response['Instances'][0]['InstanceId']
        state = 'pending'
        t = 0
        while state != 'running':
            if state != 'pending':
                raise RuntimeError('Instance %s has unexpected state'
                                   % (instance_id, state))
            logging.warn('%s: Instance %s not yet running; state is still %s',
                         t, instance_id, state)
            time.sleep(1)
            state = EcsManager._get_state(instance_id)
            t += 1
            if t > 120:
                raise RuntimeError('Instance %s still not running' % instance_id)
        return namedtuple('AwsIds',
                          ['key_pair_name',
                           'security_group_id',
                           'cluster_name',
                           'instance_id',
                           'log_group_name'])(
            key_pair_name=key_pair_name,
            security_group_id=security_group_id,
            cluster_name=cluster_name,
            instance_id=instance_id,
            log_group_name=log_group_name
        )

    @staticmethod
    def _get_state(instance_id):
        response = boto3.client('ec2').describe_instances(
            InstanceIds=[instance_id]
        )
        return response['Reservations'][0]['Instances'][0]['State']['Name']

    def _run_task(self, task_name, instance_resource):
        response = None
        t = 0
        while not response:
            # Note that the instance may be up, but not the Docker engine.
            # ie: This waiter is not sufficient:
            # self.instance.wait_until_running()
            #
            # This may take more than a minute.
            # logging.basicConfig(level=logging.DEBUG)
            try:
                response = self._ecs_client.run_task(
                    cluster=self._cluster_name,
                    taskDefinition=task_name
                )
            except StandardError as e:
                expected = (
                    'An error occurred (InvalidParameterException) '
                    'when calling the RunTask operation: '
                    'No Container Instances were found in your cluster.'
                )
                if expected not in e.message:
                    raise e
                logging.debug("%s: Got the expected 'InvalidParameterException': %s", t, e)
                time.sleep(1)
                t += 1
        if response.get('failures'):
            raise RuntimeError(response['failures'])
        task = response['tasks'][0]
        task_arn = task['taskArn']

        t = 0
        while task['lastStatus'] != task['desiredStatus']:
            logging.warning('%s: lastStatus: %s / desiredStatus: %s',
                            task_arn,
                            task['lastStatus'],
                            task['desiredStatus'])
            # And now wait again for Docker...
            time.sleep(1)
            response = self._ecs_client.describe_tasks(
                cluster=self._cluster_name,
                tasks=[task_arn]
            )
            task = response['tasks'][0]
            t += 1
            if t > self.TIMEOUT:
                raise RuntimeError(
                    'After {}s, still waiting for task "{}" to enter "{}" from "{}"'
                    .format(t, task_name, task['desiredStatus'], task['lastStatus']))
        # TODO: Container may or may not still be running;
        # Was there a reason I wanted to return the port here?
        # task['containers'][0]['networkBindings'][0]['hostPort']

    def run(self, image_name, cmd, **kwargs):
        """
        Start a specified Docker image, and returns the output.
        "image_name" may (and in fact, should) include a version.
        """

        # ECS anticipates multiple containers coming together to constitute
        # a task, but for now we just have one container per task.
        # For now, using the same names for both...
        task_name = re.sub(r':.*', '', image_name)

        # Defaults to listing only the active tasks
        response = self._ecs_client.list_task_definitions(
            familyPrefix=task_name)
        task_definition_arns = response['taskDefinitionArns']
        count = len(task_definition_arns)

        if count > 1:
            raise StandardError(
                'Expected a single task definition for %s; instead we have %s'
                % (task_name, task_definition_arns))
        elif count < 1:
            response = self._ecs_client.register_task_definition(
                family=task_name,
                containerDefinitions=[{
                    'name': task_name,
                    'image': image_name,
                    'portMappings': [
                        {
                            'containerPort': 80,
                            'protocol': 'tcp'
                            # host port will be assigned
                        },
                    ],
                    'logConfiguration': {
                        'logDriver': 'awslogs',
                        'options': {
                            'awslogs-group': self._log_group_name,
                            'awslogs-region': EcsManager.DEFAULT_REGION
                            # 'awslogs-stream-prefix': EcsManager.PREFIX
                        }
                    },

                    # TODO: We'll want this to be configurable
                    # At least one required:
                    'memory': 100,  # Hard limit
                    'memoryReservation': 50,  # Soft limit
                }]
            )
            assert(response['taskDefinition']['status'] == 'ACTIVE')

        instance_resource = boto3.resource('ec2').Instance(self._instance_id)
        self._run_task(task_name, instance_resource)

        # Read the logs:
        logs_client = boto3.client('logs')
        log_streams = []
        while len(log_streams) == 0:
            logging.warning('Waiting for log streams...')
            time.sleep(1)
            response = logs_client.describe_log_streams(logGroupName=self._log_group_name)
            log_streams = response['logStreams']

        # Not confident this is universally true...
        assert len(log_streams) == 1, \
            'Expected exactly one stream, not {}'.format(log_streams)
        stream_names = [
            description['logStreamName'] for description in log_streams
        ]
        response = logs_client.get_log_events(
                logGroupName=self._log_group_name,
                logStreamName=stream_names[0])
        log_events = response['events']
        return log_events

    def get_url(self, container_name):
        raise NotImplementedError()

    def list(self, filters={}):
        response = self._ecs_client.list_container_instances()
        if response.get('nextToken'):
            raise NotImplementedError('TODO: Iterate to collect all instances')

        # TODO: If we do anything with these, we need to return EcsContainers instead.
        return response['containerInstanceArns']


class EcsContainer(BaseContainer):

    def remove(self):
        raise NotImplementedError()

    def logs(self):
        raise NotImplementedError()


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Create (or destroy) all necessary AWS resources. ' +
                    'If creating, output the new IDs.')
    parser.add_argument('--destroy-ec2', dest='ec2_id')
    parsed = parser.parse_args()
    if parsed.ec2_id:
        # TODO: cleanup
        print('TODO: delete {}'.format(parsed.ec2_id))
    else:
        aws_ids = EcsManager.create_instance()
        # These variables are looked for during test runs.
        print('export AWS_INSTANCE_ID={}'.format(aws_ids.instance_id))
        print('export AWS_KEY_PAIR_NAME={}'.format(aws_ids.key_pair_name))
        print('export AWS_SECURITY_GROUP_ID={}'.format(aws_ids.security_group_id))
        print('export AWS_CLUSTER_NAME={}'.format(aws_ids.cluster_name))
        print('export AWS_LOG_GROUP_NAME={}'.format(aws_ids.log_group_name))
