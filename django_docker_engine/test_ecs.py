import unittest
import boto3
import logging
import time
import pprint
import re
import datetime
import requests
from botocore import exceptions

logging.basicConfig(level=logging.INFO)


class EcsTests(unittest.TestCase):
    """
    This only exercises the AWS ECS SDK:
    It does not test any of our own code!
    Probably not useful once what I've learned here has been integrated.
    """
    def setUp(self):
        logging.info('setUp')
        self.ecs_client = boto3.client('ecs')
        self.ec2_client = boto3.client('ec2')
        self.logs_client = boto3.client('logs')
        self.ec2_resource = boto3.resource('ec2')

        prefix = 'django_docker_'
        timestamp = re.sub(r'\D', '_', str(datetime.datetime.now()))
        self.key_pair_name = prefix + timestamp
        self.cluster_name = prefix + timestamp
        self.log_group_name = prefix + timestamp
        self.security_group_name = prefix + timestamp
        self.security_group_id = self.create_security_group()
        self.instance = None

        self.logs_client.create_log_group(logGroupName=self.log_group_name)

    def tearDown(self):
        logging.info('tearDown')
        instance_arns = self.ecs_client.list_container_instances(
            cluster=self.cluster_name
        )['containerInstanceArns']
        for instance_arn in instance_arns:
            self.ecs_client.deregister_container_instance(
                cluster=self.cluster_name,
                containerInstance=instance_arn, # NOT just the the instance ID
                force=True)
        self.ec2_client.delete_key_pair(KeyName=self.key_pair_name)
        self.instance.terminate()
        self.logs_client.delete_log_group(logGroupName=self.log_group_name)

        # TODO: deregister_task requires revision
        # response = self.ecs_client.deregister_task_definition()

        t = 0
        while True:
            try:
                t += 1
                time.sleep(1)
                self.ec2_client.delete_security_group(GroupName=self.security_group_name)
                break
            except exceptions.ClientError as e:
                logging.info('{}: {}'.format(t, e.message))

        t = 0
        while True:
            try:
                t += 1
                time.sleep(1)
                self.ecs_client.delete_cluster(cluster=self.cluster_name)
                break
            except StandardError as e:
                logging.info('{}: {}'.format(t, e.message))

    def create_security_group(self):
        response = self.ec2_client.create_security_group(
            GroupName=self.security_group_name,
            Description='Security group for tests'
        )
        security_group_id = response['GroupId']
        security_group = self.ec2_resource.SecurityGroup(security_group_id)

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
        security_group.reload()
        permissions = security_group.ip_permissions
        logging.info(permissions)
        self.assertEqual(len(permissions), 2)
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
        while task['lastStatus'] not in [desired_status, 'STOPPED']:
            time.sleep(1)
            response = self.ecs_client.describe_tasks(
                cluster=self.cluster_name,
                tasks=[task_arn]
            )
            task = response['tasks'][0]
            logging.info("%s: status=%s", t, task['lastStatus'])
            t += 1

        logging.info(pprint.pformat(task))
        # If the container stops, networkBindings may not be available.
        bindings = task['containers'][0].get('networkBindings')
        return bindings[0]['hostPort']

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
                'logConfiguration': {
                    'logDriver': 'awslogs',
                    'options': {
                        'awslogs-group': self.log_group_name,
                        'awslogs-region': 'us-east-1',
                        'awslogs-stream-prefix': 'test_prefix'
                    }
                },
                'image': 'nginx:latest',
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
                    'AssociatePublicIpAddress': True,
                    'Groups': [self.security_group_id]
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

        # Not sure when exactly it gets a public IP,
        # but it is not immediately available above.
        self.instance.reload()
        ip = self.instance.public_ip_address

        url_1 = 'http://%s:%s/' % (ip, port_1)
        logging.info('url: %s', url_1)

        response = requests.get(url_1)
        self.assertIn('Welcome to nginx', response.text)

        no_such_file = 'foobar'
        response = requests.get(url_1 + no_such_file)
        self.assertIn('404 Not Found', response.text)

        response = self.logs_client.describe_log_streams(logGroupName=self.log_group_name)
        stream_descriptions = response['logStreams']
        stream_names = [
            description['logStreamName'] for description in stream_descriptions
        ]

        # Not confident this is universally true, but true right now?
        self.assertEqual(len(stream_names), 1)

        log_events = []
        t = 0
        while len(log_events) < 2:
            logging.info('%s: logs are empty: %s', t, log_events)
            t += 1
            time.sleep(1)
            response = self.logs_client.get_log_events(
                logGroupName=self.log_group_name,
                logStreamName=stream_names[0])
            log_events = response['events']
        self.assertIn('"GET / HTTP/1.1" 200', log_events[0]['message'])
        self.assertIn('"GET /%s HTTP/1.1" 404' % no_such_file, log_events[1]['message'])

        logging.info('run_task, 2nd time (fast)')
        port_2 = self.run_task(task_name)

        url_2 = 'http://%s:%s/' % (ip, port_2)
        logging.info('url: %s', url_2)

        self.assertNotEquals(port_1, port_2)
        response = requests.get(url_2)
        self.assertIn('Welcome to nginx', response.text)
