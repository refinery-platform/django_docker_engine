import unittest
from django_docker_engine.proxy import NullLogger, Proxy
from django.test import RequestFactory


class ProxyTests(unittest.TestCase):

    def test_proxy_please_wait(self):
        title = 'test-title'
        body = 'test-body'
        proxy = Proxy(
            '/tmp/django-docker-engine-test',
            logger=NullLogger(),
            please_wait_title=title,
            please_wait_body=body
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

        self.assertIn('<title>'+title+'</title>', response.content)
        self.assertIn(body, response.content)
        self.assertIn('http-equiv="refresh"', response.content)
