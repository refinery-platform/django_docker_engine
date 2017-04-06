import unittest
import boto3
import logging
import time
import pprint

logging.basicConfig(level=logging.INFO)


class EcsTests(unittest.TestCase):
    def setUp(self):
        logging.info('setUp')
        self.ecs_client = boto3.client('ecs')
        self.ec2_client = boto3.client('ec2')
        self.key_pair_name = 'test_django_docker'
        self.cluster_name = 'test_cluster'
        self.instance = None

    def tearDown(self):
        logging.info('tearDown')
        self.ec2_client.delete_key_pair(KeyName=self.key_pair_name)
        self.instance.terminate()
        # self.ecs_client.delete_cluster(cluster=self.cluster_name)
        # Cleaning up is good, but I get this error:
        # The Cluster cannot be deleted while Container Instances are active or draining.

    def run_task(self, task_name):
        response = None
        t = 0
        while not response:
            # This may take 30 seconds.
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
                'image': 'nginx:1.11-alpine',
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

        logging.info(self.instance) # TODO: get IP

        # We still had a race condition with this waiter:
        # The instance may be up, but not the Docker engine.
        # self.instance.wait_until_running()

        logging.info('run_task, 1st time (slow)')

        port_1 = self.run_task(task_name)
        logging.info('port: %s', port_1)

        logging.info('run_task, 2nd time (fast)')

        port_2 = self.run_task(task_name)
        logging.info('port: %s', port_2)

        self.assertNotEquals(port_1, port_2)

        # TODO: deregister_task requires revision
        # response = self.ecs_client.deregister_task_definition()
