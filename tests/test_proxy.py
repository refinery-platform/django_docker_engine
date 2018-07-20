import re
import unittest
from datetime import datetime

from django.test import RequestFactory
from mock import mock

from django_docker_engine.historian import FileHistorian
from django_docker_engine.proxy import Proxy


class CSRFTests(unittest.TestCase):

    def setUp(self):
        self.fake_get_kwargs = {
            'request': RequestFactory().get('/fake-url'),
            'container_name': 'fake-container',
            'url': 'fake-url'
        }
        self.fake_post_kwargs = {
            'request': RequestFactory().post('/fake-url'),
            'container_name': 'fake-container',
            'url': 'fake-url'
        }

    def _check_proxy_csrf(self, csrf_exempt=True):
        with mock.patch("django_docker_engine.proxy.csrf_exempt_decorator") \
                as csrf_exempt_mock:
            Proxy(csrf_exempt=csrf_exempt).url_patterns()
            assert csrf_exempt_mock.called == csrf_exempt

    def test_csrf_exempt_default_true(self):
        self._check_proxy_csrf()

    def test_csrf_exempt_false(self):
        self._check_proxy_csrf(csrf_exempt=False)


class ProxyTests(unittest.TestCase):

    def test_proxy_please_wait(self):
        history_path = '/tmp/django-docker-history-{}'.format(
            re.sub(r'\D', '-', str(datetime.now()))
        )
        historian = FileHistorian(history_path)
        title_text = 'test-title'
        body_html = '<p>test-body</p>'
        proxy = Proxy(
            historian=historian,
            please_wait_title='<' + title_text + '>',
            please_wait_body_html=body_html,
            logs_path='docker-logs'
        )
        urlpatterns = proxy.url_patterns()
        self.assertEqual(len(urlpatterns), 2)

        response = urlpatterns[-1].callback(
            request=RequestFactory().get('/fake-url'),
            container_name='fake-container',
            url='fake-url'
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn('Container not yet available', response.reason_phrase)
        self.assertIn(
            '404 Client Error: Not Found ("No such container: fake-container")',
            response.reason_phrase
        )

        self.assertIn('<title>&lt;' + title_text +
                      '&gt;</title>', str(response.content))  # Title escaped
        self.assertIn(body_html, str(response.content))  # Body not escaped
        self.assertIn('http-equiv="refresh"', str(response.content))

        self.assertEqual(
            [line.split('\t')[1:] for line in historian.list()],
            [['fake-container', 'fake-url\n']]
        )

        # The doctests handle the case where a container has been started.
        logs_response = urlpatterns[0].callback(
            request=RequestFactory().get('/fake-url'),
            container_name='fake-container'
        )
        self.assertIn('Traceback (most recent call last)',
                      str(logs_response.content))
        self.assertIn('No such container: fake-container',
                      str(logs_response.content))
