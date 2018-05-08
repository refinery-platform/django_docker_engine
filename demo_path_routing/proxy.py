from django_docker_engine.proxy import Proxy


class AuthProxy(Proxy, object):

    def _proxy_view(self, request, container_name, url):
        assert hasattr(request, 'user')
        return super(AuthProxy, self)._proxy_view(
            request, container_name, url
        )
