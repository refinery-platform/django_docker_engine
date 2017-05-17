from django.conf.urls import include, url
from django_docker_engine.proxy import Proxy

django_docker_engine_urls = include('django_docker_engine.urls')

urlpatterns = [url(r'^docker/', django_docker_engine_urls)]
