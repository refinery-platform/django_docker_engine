from django_docker_engine.proxy import Proxy

from django_docker_engine.historian import FileHistorian


urlpatterns = Proxy(
    historian=FileHistorian(),
    logs_path='docker-logs'
).url_patterns()
