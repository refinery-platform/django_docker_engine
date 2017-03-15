from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    url(r'^docker/', include('django_docker_engine.urls')),
)
