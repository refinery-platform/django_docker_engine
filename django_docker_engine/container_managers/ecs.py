import boto3
import logging
import datetime
import re
import time
from base import BaseManager, BaseContainer


class EcsManager(BaseManager):

    def __init__(self,
                 prefix='django_docker_',
                 key_pair_name=None,
                 cluster_name=None,
                 security_group_id=None,
                 instance_id=None,

                 # TODO: Does something in Refinery need to create this?
                 instance_profile_arn=
                    'arn:aws:iam::100836861126:instance-profile/ecsInstanceRole',

                 # us-east-1: amzn-ami-2016.09.g-amazon-ecs-optimized
                 ami_id='ami-275ffe31'):
        """
        Specify a key pair, cluster, and security group to use,
        or new ones will be created with names based on the given prefix.
        """
        self.__ecs_client = boto3.client('ecs')
        self.__ec2_client = boto3.client('ec2')
        self.__ec2_resource = boto3.resource('ec2')

        self.__instance_profile_arn = instance_profile_arn
        self.__ami_id = ami_id

        timestamp = re.sub(r'\D', '_', str(datetime.datetime.now()))
        default = prefix + timestamp

        self.__key_pair_name = key_pair_name or \
            self.__create_key_pair(default)
        self.__cluster_name = cluster_name or \
            self.__create_cluster(default)
        self.__security_group_id = security_group_id or \
            self.__create_security_group(default)
        self.__instance_id = instance_id or \
            self.__create_instance()

    def __create_key_pair(self, key_pair_name):
        response = self.ec2_client.create_key_pair(KeyName=key_pair_name)
        assert(response['KeyName'] == key_pair_name)
        return key_pair_name

    def __create_cluster(self, cluster_name):
        response = self.__ecs_client.create_cluster(clusterName=cluster_name)
        assert(response['cluster']['status'] == 'ACTIVE')
        return cluster_name

    def __create_security_group(self, security_group_name):
        response = self.ec2_client.create_security_group(
            GroupName=security_group_name,
            Description='Security group for tests'
        )
        security_group_id = response['GroupId']
        security_group = self.__ec2_resource.SecurityGroup(security_group_id)

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

    def __create_instance(self):
        response = self.__ec2_client.run_instances(
            ImageId=self.__ami_id,
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.nano',
            KeyName=self.__key_pair_name,
            UserData='\n'.join([
                '#!/bin/bash',
                'echo ECS_CLUSTER={} >> /etc/ecs/ecs.config'.
                    format(self.__cluster_name)]),
            NetworkInterfaces=[
                {
                    'DeviceIndex': 0,
                    'AssociatePublicIpAddress': True,
                    'Groups': [self.__security_group_id]
                }
            ],
            IamInstanceProfile={
                'Arn': self.__instance_profile_arn
            }
        )
        assert(response['Instances'][0]['State']['Name'] == 'pending')
        return response['Instances'][0]['InstanceId']

    def __run_task(self, task_name, instance_resource):
        response = None
        t = 0
        while not response:
            # Note that the instance may be up, but not the Docker engine.
            # ie: This waiter is not sufficient:
            # self.instance.wait_until_running()
            #
            # This may take more than a minute.
            try:
                response = self.__ecs_client.run_task(
                    cluster=self.__cluster_name,
                    taskDefinition=task_name
                )
            except Exception as e:
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
            response = self.__ecs_client.describe_tasks(
                cluster=self.__cluster_name,
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
        unversioned_image_name = re.sub(r':.*', '', image_name)

        # Defaults to listing only the active tasks
        response = self.__ecs_client.list_task_definitions(
            familyPrefix=unversioned_image_name)
        task_definition_arns = response['taskDefinitionArns']
        count = len(task_definition_arns)

        if count > 1:
            raise StandardError(
                'Expected a single task definition for %s; instead we have %s'
                % (unversioned_image_name, task_definition_arns))
        elif count < 1:
            response = self.__ecs_client.register_task_definition(
                family=unversioned_image_name,
                containerDefinitions=[{
                    'name': unversioned_image_name,
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

        instance_resource = boto3.resource('ec2').Instance(self.__instance_id)
        self.__run_task(image_name, instance_resource)

        # TODO: At this point, local.py returns output from the container,
        # if any, but this is non-trivial under AWS.
        # See: https://github.com/aws/amazon-ecs-agent/issues/9#issuecomment-195637638
        # For now, just return a placeholder

        return 'TODO: Container output placeholder'

    def get_url(self, container_name):
        raise NotImplementedError()

    def list(self, filters={}):
        raise NotImplementedError()


class EcsContainer(BaseContainer):

    def remove(self):
        raise NotImplementedError()

    def logs(self):
        raise NotImplementedError()
