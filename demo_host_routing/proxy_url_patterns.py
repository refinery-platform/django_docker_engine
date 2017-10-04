from django_docker_engine.proxy import Proxy, FileLogger
import settings

urlpatterns = Proxy(FileLogger(settings.PROXY_LOG)).url_patterns()
