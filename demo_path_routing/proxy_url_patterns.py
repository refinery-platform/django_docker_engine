from django_docker_engine.proxy import Proxy
from django_docker_engine.docker_utils import DockerClientSpec

spec = DockerClientSpec('/tmp/django-docker-data', do_input_json_envvar=True)
urlpatterns = Proxy(spec).url_patterns()
