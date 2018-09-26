from django_docker_engine.proxy import Proxy

urlpatterns = Proxy(
    logs_path='docker-logs'
).url_patterns()
