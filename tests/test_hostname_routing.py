from django_docker_engine.middleware.hostname_routing import HostnameRoutingMiddleware
from django.test import RequestFactory
import unittest


class HostnameRoutingTests(unittest.TestCase):

    def test_hostname_routing(self):
        name = 'foobar'
        path = '/barfoo'
        request = RequestFactory().get(
            path,
            HTTP_HOST='{}.docker.localhost'.format(name)
        )
        self.assertEqual(request.path, path)
        HostnameRoutingMiddleware().process_request(request)
        self.assertEqual(request.path, '/docker/{}{}'.format(name, path))
