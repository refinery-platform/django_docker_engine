import unittest
from django_docker_engine.proxy import NullLogger, Proxy
from django.test import RequestFactory


class ProxyTests(unittest.TestCase):

    def test_proxy_please_wait(self):
        content = 'please-wait-test-message'
        proxy = Proxy(
            '/tmp/django-docker-engine-test',
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

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.reason_phrase, 'Container not yet available')
        self.assertEqual(response.content, content)
