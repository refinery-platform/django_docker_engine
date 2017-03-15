from django.conf.urls import patterns, url
from httpproxy.views import HttpProxy
from docker_engine_app import views

urlpatterns = patterns('',
    url(r'^proxy_any_host/(?P<host>[^/]*)/(?P<url>.*)$',
        lambda request, host, url:
            HttpProxy.as_view(base_url='http://{}/'.format(host))(request, url=url)
        ),
)

