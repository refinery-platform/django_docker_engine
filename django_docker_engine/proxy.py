from __future__ import print_function

import logging
from django.conf.urls import url
from django.http import HttpResponse
from django.template import Context, Template
from docker.errors import NotFound
from httplib import BadStatusLine
from httpproxy.views import HttpProxy
from docker_utils import DockerClientWrapper
from datetime import datetime
from collections import namedtuple
import socket
import errno
import os

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
    def __init__(self, data_dir, logger=NullLogger(),
                 please_wait_title='Please wait',
                 please_wait_body='<h1>Please wait</h1>'):
        self.data_dir = data_dir
        self.logger = logger

        # Normally, we would use template loaders, but could there be
        # interactions between the configs necessary here and the parent app?
        path = os.path.join(os.path.dirname(__file__), 'please-wait.html')
        template = Template(open(path).read())
        context = Context({
            'title': please_wait_title,
            'body': please_wait_body
        })
        self.content = template.render(context)

    def url_patterns(self):
        return [url(
            r'^(?P<container_name>[^/]*)/(?P<url>.*)$',
            self._proxy_view
        )]

    def _proxy_view(self, request, container_name, url):
        self.logger.log(container_name, url)
        try:
            client = DockerClientWrapper(self.data_dir)
            container_url = client.lookup_container_url(container_name)
            view = HttpProxy.as_view(base_url=container_url)
            return view(request, url=url)
        except (NotFound, BadStatusLine) as e:
            logger.info(
                'Normal transient error. '
                'Container: %s, Exception: %s', container_name, e)
            view = self._please_wait_view_factory().as_view()
            return view(request)
        except socket.error as e:
            if e.errno != errno.ECONNRESET:
                raise
            logger.info(
                'Container not yet listening. '
                'Container: %s, Exception: %s', container_name, e)
            view = self._please_wait_view_factory().as_view()
            return view(request)

    def _please_wait_view_factory(self):
        class PleaseWaitView(View):
            def get(inner_self, request, *args, **kwargs):
                response = HttpResponse(self.content)
                response.status_code = 503
                response.reason_phrase = 'Container not yet available'
                # Non-standard, but more clear than default;
                # Also, before 1.9, this is not set just by changing status code.
                return response
            http_method_named = ['get']
        return PleaseWaitView
