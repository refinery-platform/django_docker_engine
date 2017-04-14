from django.conf.urls import url
from httpproxy.views import HttpProxy
from docker_utils import DockerClientWrapper

urlpatterns = [
    # During development, it's useful to be able to test proxying,
    # without also needing to start a container.
    # url(r'^proxy_any_host/(?P<host>[^/]*)/(?P<url>.*)$',
    #     lambda request, host, url:
    #         HttpProxy.as_view(
    #             base_url='http://{}/'.format(host)
    #         )(request, url=url)
    # ),

    url(r'^(?P<container_name>[^/]*)/(?P<url>.*)$',
        lambda request, container_name, url:
        HttpProxy.as_view(
            base_url=DockerClientWrapper().lookup_container_url(container_name)
        )(request, url=url)
        )
]
