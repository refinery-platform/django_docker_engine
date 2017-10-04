from django.conf.urls import include, url

urlpatterns = [url(r'^docker/', include('django_docker_engine_demo.proxy_url_patterns'))]
