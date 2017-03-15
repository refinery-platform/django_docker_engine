from django.conf.urls import patterns, url
from httpproxy.views import HttpProxy
from docker_engine_app import views

urlpatterns = patterns('',
    (r'^higlass/(?P<url>.*)$',
        HttpProxy.as_view(base_url='http://higlass.io/')),
)

