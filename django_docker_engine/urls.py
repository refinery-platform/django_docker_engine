from proxy import Proxy, FileLogger

urlpatterns = Proxy(FileLogger('/tmp/django_docker_engine.log')).url_patterns()
