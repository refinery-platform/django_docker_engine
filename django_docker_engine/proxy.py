from __future__ import print_function

from django.conf.urls import url
from httpproxy.views import HttpProxy
from docker_utils import DockerClientWrapper
from datetime import datetime
from collections import namedtuple

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
    def __init__(self, logger=NullLogger()):
        self.logger = logger

    def url_patterns(self):
        # https://docs.djangoproject.com/en/1.11/topics/http/urls/#named-groups
        return [
            url(
                r'^(?P<container_name>[^/]*)/(?P<container_port>[^/]*)/(?P<url>.*)$',
                self._proxy_view
            ),
        ]

    def _proxy_view(self,
                    request,
                    container_name="",
                    container_port="",
                    url=""):
        self.logger.log(container_name, container_port, url)
        container_url = DockerClientWrapper().lookup_container_url(
            container_name, container_port
        )
        view = HttpProxy.as_view(base_url=container_url)
        return view(request, url=url)
