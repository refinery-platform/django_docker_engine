import unittest
import boto3

class EcsTests(unittest.TestCase):
    def setUp(self):
        self.client = boto3.client('ecs')

    def tearDown(self):
        pass

    def test_create_cluster(self):
        NAME = 'foo'
        response = self.client.create_cluster(clusterName=NAME)
        self.assertEqual(response['cluster']['status'], 'ACTIVE')
        #print response
        response = self.client.delete_cluster(cluster=NAME)
        self.assertEqual(response['cluster']['status'], 'INACTIVE')
        #print response