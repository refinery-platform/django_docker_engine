import unittest
from mock import mock
from django_docker_engine.proxy import Proxy
from django.test import RequestFactory
import re
from datetime import datetime
from django_docker_engine.historian import FileHistorian


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
    # TODO?
    #     timestamp = re.sub(r'\W', '-', datetime.now().isoformat())
    #     data_dir = '/tmp/django-docker-tests-' + timestamp
    #     self.root_label = 'test-root'
    #     self.manager = DockerEngineManager(data_dir, self.root_label)
    #     self.container_name = timestamp
    #     self.manager.run('nginx:1.10.3-alpine',
    #                      ports={'80/tcp': None},
    #                      detach=True,
    #                      labels={'test-root.port': '80'},
    #                      cmd=None)

    @mock.patch(
        "django_docker_engine.proxy.DockerClientWrapper"
        ".lookup_container_url", return_value="http://example.com"
    )
    def test_csrf_exempt_true(self, url_mock):
        proxy = Proxy(
            '/tmp/django-docker-engine-test',
            csrf_exempt=True
        )
        urlpatterns = proxy.url_patterns()

        with mock.patch("django_docker_engine.proxy.csrf_exempt_decorator") \
                as csrf_decorator_mock:
            urlpatterns[0].callback(**self.fake_get_kwargs)
            self.assertEqual(csrf_decorator_mock.call_count, 1)
            urlpatterns[0].callback(**self.fake_post_kwargs)
            self.assertEqual(csrf_decorator_mock.call_count, 2)

    def test_csrf_exempt_default_false(self):
        proxy = Proxy(
            '/tmp/django-docker-engine-test'
        )
        urlpatterns = proxy.url_patterns()
        with mock.patch("django_docker_engine.proxy.csrf_exempt_decorator") \
                as csrf_decorator_mock:
            get_response = urlpatterns[0].callback(**self.fake_get_kwargs)
            self.assertEqual(get_response.status_code, 503)
            get_response = urlpatterns[0].callback(**self.fake_post_kwargs)
            self.assertEqual(get_response.status_code, 405)
            self.assertEqual(csrf_decorator_mock.call_count, 0)


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
