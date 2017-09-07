import unittest
from django_docker_engine.proxy import NullLogger, Proxy


class ProxyTests(unittest.TestCase):

    def test_proxy(self):
        urlpatterns = Proxy(NullLogger()).url_patterns()
        self.assertEquals(len(urlpatterns), 1)