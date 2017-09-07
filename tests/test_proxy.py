import unittest
from django_docker_engine.proxy import NullLogger, Proxy
from django.test import RequestFactory


class ProxyTests(unittest.TestCase):

    def test_proxy(self):
        content = 'please-wait-test-message'
        proxy = Proxy(
            logger=NullLogger(),
            please_wait_content=content
        )
        urlpatterns = proxy.url_patterns()
        self.assertEquals(len(urlpatterns), 1)

        response = urlpatterns[0].callback(
            request=RequestFactory().get('/fake-url'),
            container_name='fake-container',
            url='fake-url'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, content)
