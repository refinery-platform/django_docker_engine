from django.conf.urls import include, url

from . import views


urlpatterns = [
    url(r'^$', views.index),
    url(r'^upload/(.*)$', views.upload),
    url(r'^docker/', include(__package__ + '.proxy_url_patterns'))
]
