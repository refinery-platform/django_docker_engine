from django_docker_engine.middleware.hostname_routing import HostnameRoutingMiddleware
from django.test import RequestFactory
import unittest


class HostnameRoutingTest(unittest.TestCase):

    def test_hostname_routing(self):
        name = 'foobar'
        request = RequestFactory().get('/', HTTP_HOST='{}.docker.localhost'.format(name))
        self.assertEqual(request.path, '/')
        HostnameRoutingMiddleware().process_request(request)
        self.assertEqual(request.path, '/docker/{}/'.format(name))