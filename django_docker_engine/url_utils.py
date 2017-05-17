from django.conf.urls import url
from httpproxy.views import HttpProxy
from docker_utils import DockerClientWrapper

def proxy_url():
    return url(
        r'^(?P<container_name>[^/]*)/(?P<url>.*)$',
        _proxy_view
    )

def _proxy_view(request, container_name, url):
    container_url = DockerClientWrapper().lookup_container_url(container_name)
    view = HttpProxy.as_view(base_url=container_url)
    return view(request, url=url)