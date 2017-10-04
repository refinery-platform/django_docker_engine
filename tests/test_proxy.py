import unittest
from django_docker_engine.proxy import Proxy
from django.test import RequestFactory
import re
from datetime import datetime
from django_docker_engine.historian import FileHistorian


class ProxyTests(unittest.TestCase):

    def test_proxy_please_wait(self):
        history_path = '/tmp/django-docker-history-{}'.format(
            re.sub(r'\D', '-', str(datetime.now()))
        )
        historian = FileHistorian(history_path)
        title_text = 'test-title'
        body_html = '<p>test-body</p>'
        proxy = Proxy(
            '/tmp/django-docker-engine-test',
            historian=historian,
            please_wait_title='<'+title_text+'>',
            please_wait_body_html=body_html
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

        # Title is escaped
        self.assertIn('<title>&lt;'+title_text+'&gt;</title>', response.content)
        # Body is not escaped
        self.assertIn(body_html, response.content)

        self.assertIn('http-equiv="refresh"', response.content)

        self.assertEqual(
            [line.split('\t')[1:] for line in historian.list()],
            [['fake-container', 'fake-url\n']]
        )
