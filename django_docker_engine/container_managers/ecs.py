import boto3
import logging
import datetime
import re
import time
from base import BaseManager, BaseContainer


class EcsManager(BaseManager):

    # us-east-1: amzn-ami-2016.09.g-amazon-ecs-optimized
    DEFAULT_AMI_ID = 'ami-275ffe31'
    DEFAULT_ROLE_ARN = \
        'arn:aws:iam::100836861126:instance-profile/ecsInstanceRole'

    def __init__(
            self,
            prefix='django_docker_',
            key_pair_name=None,
            cluster_name=None,
            security_group_id=None,
            instance_id=None,
            instance_profile_arn=DEFAULT_ROLE_ARN,
            ami_id=DEFAULT_AMI_ID):
        """
        Specify a key pair, cluster, and security group to use,
        or new ones will be created with names based on the given prefix.
        """
        self._ecs_client = boto3.client('ecs')
        self._ec2_client = boto3.client('ec2')
        self._ec2_resource = boto3.resource('ec2')

        self._instance_profile_arn = instance_profile_arn
        self._ami_id = ami_id

        timestamp = re.sub(r'\D', '_', str(datetime.datetime.now()))
        default = prefix + timestamp

        self._key_pair_name = key_pair_name or \
            self._create_key_pair(default)
        self._cluster_name = cluster_name or \
            self._create_cluster(default)
        self._security_group_id = security_group_id or \
            self._create_security_group(default)
        self._instance_id = instance_id or \
            self._create_instance()

    def _create_key_pair(self, key_pair_name):
        response = self._ec2_client.create_key_pair(KeyName=key_pair_name)
        assert(response['KeyName'] == key_pair_name)
        return key_pair_name

    def _create_cluster(self, cluster_name):
        response = self._ecs_client.create_cluster(clusterName=cluster_name)
        assert(response['cluster']['status'] == 'ACTIVE')
        return cluster_name

    def _create_security_group(self, security_group_name):
        response = self._ec2_client.create_security_group(
            GroupName=security_group_name,
            Description='Security group for tests'
        )
        security_group_id = response['GroupId']
        security_group = self._ec2_resource.SecurityGroup(security_group_id)

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

    def _create_instance(self):
        user_data = '\n'.join([
            '#!/bin/bash',
            'echo ECS_CLUSTER={} >> /etc/ecs/ecs.config'.format(
                self._cluster_name
            )])
        response = self._ec2_client.run_instances(
            ImageId=self._ami_id,
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.nano',
            KeyName=self._key_pair_name,
            UserData=user_data,
            NetworkInterfaces=[
                {
                    'DeviceIndex': 0,
                    'AssociatePublicIpAddress': True,
                    'Groups': [self._security_group_id]
                }
            ],
            IamInstanceProfile={
                'Arn': self._instance_profile_arn
            }
        )
        assert(response['Instances'][0]['State']['Name'] == 'pending')
        return response['Instances'][0]['InstanceId']

    def _run_task(self, task_name, instance_resource):
        response = None
        t = 0
        while not response:
            # Note that the instance may be up, but not the Docker engine.
            # ie: This waiter is not sufficient:
            # self.instance.wait_until_running()
            #
            # This may take more than a minute.
            logging.basicConfig(level=logging.DEBUG)
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
                logging.debug("%s: Expect 'InvalidParameterException': %s", t, e)
                time.sleep(1)
                t += 1
        task = response['tasks'][0]
        task_arn = task['taskArn']
        desired_status = task['desiredStatus']

        t = 0
        while task['lastStatus'] != desired_status:
            # And now wait again for Docker...
            time.sleep(1)
            response = self._ecs_client.describe_tasks(
                cluster=self._cluster_name,
                tasks=[task_arn]
            )
            task = response['tasks'][0]
            t += 1
        return task['containers'][0]['networkBindings'][0]['hostPort']

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

                    # TODO: We'll want this to be configurable
                    # At least one required:
                    'memory': 100,  # Hard limit
                    'memoryReservation': 50,  # Soft limit
                }]
            )
            assert(response['taskDefinition']['status'] == 'ACTIVE')

        instance_resource = boto3.resource('ec2').Instance(self._instance_id)
        self._run_task(task_name, instance_resource)

        raise NotImplementedError('TODO: get CloudWatch logs')

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
