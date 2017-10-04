from django_docker_engine.proxy import Proxy

urlpatterns = Proxy('/tmp/django-docker-data').url_patterns()
