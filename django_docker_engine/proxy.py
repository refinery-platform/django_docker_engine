from __future__ import print_function

import logging
from django.conf.urls import url
from django.http import HttpResponse
from docker.errors import NotFound
from httpproxy.views import HttpProxy
from docker_utils import DockerClientWrapper
from datetime import datetime
from collections import namedtuple

try:
    from django.views import View
except ImportError:  # Support older versions of django
    from django.views.generic import View

logging.basicConfig()
logger = logging.getLogger(__name__)

UrlPatterns = namedtuple('UrlPatterns', ['urlpatterns'])


class NullLogger():
    def __init__(self):
        pass

    def log(self, *args):
        pass


class FileLogger():
    # This is not the best for the long term, but it will help us understand our needs.
    def __init__(self, path):
        self.path = path

    def log(self, *args):
        with open(self.path, 'a') as f:
            timestamp = datetime.now().isoformat()
            args_list = list(args)
            args_list.insert(0, timestamp)
            print('\t'.join(args_list), file=f)

    def list(self):
        with open(self.path) as f:
            lines = f.readlines()
        return lines


class Proxy():
    def __init__(self, logger=NullLogger(), please_wait_content='Please wait.'):
        self.logger = logger
        self.content = please_wait_content

    def url_patterns(self):
        return [url(
            r'^(?P<container_name>[^/]*)/(?P<url>.*)$',
            self._proxy_view
        )]

    def _proxy_view(self, request, container_name, url):
        self.logger.log(container_name, url)
        try:
            container_url = DockerClientWrapper().lookup_container_url(container_name)
            view = HttpProxy.as_view(base_url=container_url)
            return view(request, url=url)
        except NotFound:
            view = self._view_factory(self.content).as_view()
            return view(request)

    def _view_factory(self, content):
        # TODO: Is there a less weird way to do this?
        class PleaseWaitView(View):
            def get(self, request, *args, **kwargs):
                response = HttpResponse(content)
                response.status_code = 503
                response.reason_phrase = 'Container not yet available'
                # Non-standard, but more clear than default;
                # Also, before 1.9, this is not set just by changing status code.
                return response
            http_method_named = ['get']
        return PleaseWaitView

