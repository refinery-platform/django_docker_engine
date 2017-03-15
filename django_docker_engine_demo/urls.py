from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
                       url(r'^docker/', include('django_docker_engine.urls')),
                       )
