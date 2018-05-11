from django.core.exceptions import PermissionDenied

from django_docker_engine.proxy import Proxy


class AuthProxy(Proxy, object):

    def _proxy_view(self, request, container_name, url):
        if request.user.is_authenticated:
            return super(AuthProxy, self)._proxy_view(
                request, container_name, url)
        else:
            raise PermissionDenied()
