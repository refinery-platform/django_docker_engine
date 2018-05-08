from django_docker_engine.proxy import Proxy


class AuthProxy(Proxy, object):

    def _proxy_view(self, request, container_name, url):
        # TODO: Look at request.user
        print('############## {}'.format(request.user))
        return super(AuthProxy, self)._proxy_view(
            request, container_name, url
        )
