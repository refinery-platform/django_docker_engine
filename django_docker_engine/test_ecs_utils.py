import unittest
import boto3
import logging
import time
import pprint
import re
import datetime
import requests

logging.basicConfig(level=logging.INFO)


class EcsTests(unittest.TestCase):
    def setUp(self):
        logging.info('setUp')
        self.ecs_client = boto3.client('ecs')
        self.ec2_client = boto3.client('ec2')
        self.ec2_resource = boto3.resource('ec2')

        timestamp = re.sub(r'\D', '_', str(datetime.datetime.now()))
        self.key_pair_name = 'test_django_docker_{}'.format(timestamp)
        self.cluster_name = 'test_cluster_{}'.format(timestamp)
        self.security_group_name = 'test_security_group_{}'.format(timestamp)

        self.instance = None

    def tearDown(self):
        logging.info('tearDown')
        self.ec2_client.delete_key_pair(KeyName=self.key_pair_name)
        self.instance.terminate()
        # TODO: self.ec2_client.delete_security_group(GroupName=self.security_group_name)
        # self.ecs_client.delete_cluster(cluster=self.cluster_name)
        # Cleaning up is good, but I get this error:
        # The Cluster cannot be deleted while Container Instances are active or draining.

    def create_security_group(self):
        response = self.ec2_client.create_security_group(
            GroupName=self.security_group_name,
            Description='Security group for tests'
        )
        security_group_id = response['GroupId']
        security_group = self.ec2_resource.SecurityGroup(security_group_id)
        security_group.authorize_ingress(
            IpProtocol='tcp',
            # http://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_definition_parameters.html
            # Ephermal port range has changed in different versions;
            # This is a super-set.
            FromPort=32768,
            ToPort=65535
            # TODO: Exclude 51678 to protect ECS Container Agent.
        )
        return security_group_id

    def run_task(self, task_name):
        response = None
        t = 0
        while not response:
            # Note that the instance may be up, but not the Docker engine.
            # ie: This waiter is not sufficient:
            # self.instance.wait_until_running()
            #
            # This may take more than a minute.
            try:
                response = self.ecs_client.run_task(
                    cluster=self.cluster_name,
                    taskDefinition=task_name
                )
            except Exception as e:
                logging.info("%s: Expect 'InvalidParameterException': %s", t, e)
                time.sleep(1)
                t += 1
        task = response['tasks'][0]
        task_arn = task['taskArn']
        desired_status = task['desiredStatus']

        logging.info('describe_tasks, until it is running')

        t = 0
        while task['lastStatus'] != desired_status:
            time.sleep(1)
            response = self.ecs_client.describe_tasks(
                cluster=self.cluster_name,
                tasks=[task_arn]
            )
            task = response['tasks'][0]
            logging.info("%s: status=%s", t, task['lastStatus'])
            t += 1

        logging.debug(pprint.pformat(task))
        return task['containers'][0]['networkBindings'][0]['hostPort']

    def test_create_cluster(self):
        logging.info('create_cluster')

        response = self.ecs_client.create_cluster(clusterName=self.cluster_name)
        self.assertEqual(response['cluster']['status'], 'ACTIVE')

        logging.info('register_task_definition')

        task_name = 'test_task'
        response = self.ecs_client.register_task_definition(
            family=task_name,
            containerDefinitions=[{
                'name': 'my_container',

                # This is the smallest httpd I could find, but not
                # proportionately faster: bottleneck may not be download.
                'image': 'fnichol/uhttpd:latest',
                'portMappings': [
                    {
                        'containerPort': 80,
                        'protocol': 'tcp'
                        # host port will be assigned
                    },
                ],

                # At least one required:
                'memory': 100,  # Hard limit
                'memoryReservation': 50,  # Soft limit
            }]
        )
        self.assertEqual(response['taskDefinition']['status'], 'ACTIVE')

        logging.info('create_key_pair')

        response = self.ec2_client.create_key_pair(KeyName=self.key_pair_name)
        self.assertEqual(response['KeyName'], self.key_pair_name)

        logging.info('run_instances')

        response = self.ec2_client.run_instances(
            ImageId='ami-275ffe31',
            # us-east-1: amzn-ami-2016.09.g-amazon-ecs-optimized
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.nano',
            KeyName=self.key_pair_name,
            UserData='\n'.join([
                '#!/bin/bash',
                'echo ECS_CLUSTER={} >> /etc/ecs/ecs.config'.format(self.cluster_name)]),
            NetworkInterfaces=[
                {
                    'DeviceIndex': 0,
                    'AssociatePublicIpAddress': True
                }
            ],
            IamInstanceProfile={
                # TODO: A new user will not already have this profile;
                # TODO: Should we create it?
                'Arn': 'arn:aws:iam::100836861126:instance-profile/ecsInstanceRole',
                # 'Name': 'optional?'
            }
        )
        self.assertEqual(response['Instances'][0]['State']['Name'], 'pending')

        instance_id = response['Instances'][0]['InstanceId']
        self.instance = boto3.resource('ec2').Instance(instance_id)

        logging.info('run_task, 1st time (slow)')

        port_1 = self.run_task(task_name)
        self.instance.reload()
        ip = self.instance.public_ip_address
        url_1 = 'http://%s:%s/' % (ip, port_1)
        logging.info('url: %s', url_1)

        logging.info('run_task, 2nd time (fast)')

        port_2 = self.run_task(task_name)
        url_2 = 'http://%s:%s/' % (ip, port_2)
        logging.info('url: %s', url_2)

        self.assertNotEquals(port_1, port_2)

        response = requests.get(url_1)
        logging.info(response.text)

        # TODO: deregister_task requires revision
        # response = self.ecs_client.deregister_task_definition()
