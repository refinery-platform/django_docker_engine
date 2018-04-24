from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^$', views.index),
    url(r'^launch/$', views.launch),
    url(r'^kill/(.*)$', views.kill),
    url(r'^upload/(.*)$', views.upload),
    url(r'^docker/', include(__package__ + '.proxy_url_patterns'))
]
