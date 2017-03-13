from django.conf.urls import patterns, url

from docker_engine_app import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^(?P<image_id>\d+)/$', views.detail, name='detail'),
)