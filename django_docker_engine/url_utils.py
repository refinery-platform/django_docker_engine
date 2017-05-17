from __future__ import print_function

from django.conf.urls import url
from httpproxy.views import HttpProxy
from docker_utils import DockerClientWrapper
from datetime import datetime

def proxy_url():
    return url(
        r'^(?P<container_name>[^/]*)/(?P<url>.*)$',
        _proxy_view
    )

def _log(container_name, url):
    with open('/tmp/refinery.txt', 'a') as f:
        timestamp = datetime.now().isoformat()
        print('\t'.join([timestamp, container_name, url]), file=f)

def _proxy_view(request, container_name, url):
    _log(container_name, url)
    container_url = DockerClientWrapper().lookup_container_url(container_name)
    view = HttpProxy.as_view(base_url=container_url)
    return view(request, url=url)