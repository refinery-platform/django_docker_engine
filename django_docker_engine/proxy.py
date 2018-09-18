import errno
import logging
import os
import socket
import traceback
from collections import namedtuple
from sys import version_info

from django.conf.urls import url
from django.http import HttpResponse
from django.template.backends.django import DjangoTemplates
from django.views.decorators.csrf import csrf_exempt as csrf_exempt_decorator
from django.views.defaults import page_not_found
from django.views.generic.base import View
from docker.errors import NotFound
from revproxy.views import ProxyView
from urllib3.exceptions import MaxRetryError

from django_docker_engine.historian import NullHistorian

from .container_managers.docker_engine import DockerEngineManagerError
from .docker_utils import DockerClientWrapper

if version_info >= (3,):
    from http.client import BadStatusLine
    from urllib.error import HTTPError
else:
    from httplib import BadStatusLine
    from urllib2 import HTTPError

logging.basicConfig()
logger = logging.getLogger(__name__)

UrlPatterns = namedtuple('UrlPatterns', ['urlpatterns'])


class _AnonUser():
    # TODO: This is a hack. Waiting for fix for
    # https://github.com/TracyWebTech/django-revproxy/issues/86
    # https://github.com/TracyWebTech/django-revproxy/pull/92
    def get_username(self):
        return 'anonymous'

    def is_active(self):
        return True


class Proxy():
    def __init__(self,
                 historian=NullHistorian(),
                 please_wait_title='Please wait',
                 please_wait_body_html='<h1>Please wait</h1>',
                 csrf_exempt=True,
                 logs_path=None):
        self.historian = historian
        self.csrf_exempt = csrf_exempt
        self.content = self._render({
            'title': please_wait_title,
            'body_html': please_wait_body_html
        })
        self.logs_path = logs_path

    def _render(self, context):
        template_path = os.path.join(
            os.path.dirname(__file__), 'please-wait.html')
        template_code = open(template_path).read()

        # Normally, we would use template loaders, but could there be
        # interactions between the configs necessary here and in the parent app?
        engine = DjangoTemplates({
            'OPTIONS': {}, 'NAME': None, 'DIRS': [], 'APP_DIRS': []
        })
        # All the keys are required, but the values don't seem to matter.
        template = engine.from_string(template_code)

        return template.render(context)

    def url_patterns(self):
        proxy_url = url(
            r'^(?P<container_name>[^/]*)/(?P<url>.*)$',
            csrf_exempt_decorator(self._proxy_view) if self.csrf_exempt
            else self._proxy_view
        )
        if self.logs_path:
            return [
                url(
                    r'^(?P<container_name>[^/]*)/{}$'.format(self.logs_path),
                    csrf_exempt_decorator(self._logs_view) if self.csrf_exempt
                    else self._logs_view
                ),
                proxy_url
            ]
        return [proxy_url]

    def _internal_proxy_view(self, request, container_url, path_url):
        # Any dependencies on the 3rd party proxy should be contained here.
        try:
            view = ProxyView.as_view(
                upstream=container_url,
                add_remote_user=True)
            if not hasattr(request, 'user'):
                request.user = _AnonUser()
            return view(request, path=path_url)
        except MaxRetryError as e:
            logger.info('Normal transient error: %s', e)
            view = self._please_wait_view_factory(e).as_view()
            return view(request)

    def _proxy_view(self, request, container_name, url):
        try:
            client = DockerClientWrapper()
            self.historian.record(
                client.lookup_container_id(container_name), url)
            container_url = client.lookup_container_url(container_name)
            return self._internal_proxy_view(request, container_url, url)
        except (DockerEngineManagerError, NotFound, BadStatusLine) as e:
            # TODO: Can we reproduce any of these?
            # Make tests if so, and move to _internal_proxy_view
            logger.info(
                'Normal transient error. '
                'Container: %s, Exception: %s', container_name, e)
            view = self._please_wait_view_factory(e).as_view()
            return view(request)
        except socket.error as e:
            if e.errno != errno.ECONNRESET:
                raise
            logger.info(
                'Container not yet listening. '
                'Container: %s, Exception: %s', container_name, e)
            view = self._please_wait_view_factory(e).as_view()
            return view(request)
        except HTTPError as e:
            logger.warn(e)
            return page_not_found(request, e)
            # The underlying error is not necessarily a 404,
            # but this seems ok.

    def _please_wait_view_factory(self, message):
        class PleaseWaitView(View):
            def get(inner_self, request, *args, **kwargs):  # noqa: N805
                response = HttpResponse(self.content)
                response.status_code = 503
                response.reason_phrase = \
                    'Container not yet available: {}'.format(message)
                # There are different failure modes, and including the message
                # lets us make sure we're getting the one we expect.
                return response
            http_method_named = ['get']
        return PleaseWaitView

    def _logs_view(self, request, container_name):
        try:
            logs = DockerClientWrapper().logs(container_name)
        except:
            logs = traceback.format_exc()
        return HttpResponse(logs, content_type='text/plain')
