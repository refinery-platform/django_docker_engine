import re

from django.conf import settings


class HostnameRoutingMiddlewareCallable():  # Django 2
    def __init__(self, get_response):
        self.get_response = get_response
        self.middleware = HostnameRoutingMiddleware()

    def __call__(self, request):
        self.middleware.process_request(request)
        return self.get_response(request)


class HostnameRoutingMiddleware():  # Django < 2
    """
    When registered with Django, if an incoming request host ends with
    DJANGO_DOCKER_HOST_SUFFIX, the subdomain is taken as the name of the
    container to route to.
    """

    def process_request(self, request):
        host_suffix = settings.DJANGO_DOCKER_HOST_SUFFIX
        path_prefix = settings.DJANGO_DOCKER_PATH_PREFIX

        request_host_and_port = request.META['HTTP_HOST']
        request_host = re.sub(r':\d+$', '', request_host_and_port)
        if request_host.endswith(host_suffix):
            container_name = request_host[0:-len(host_suffix)]
            # path and path_info seem redundant: Not sure if I'm doing this right.
            request.path_info = path_prefix + container_name + request.path_info
            request.path = path_prefix + container_name + request.path
            # Munging the HTTP_HOST itself does not seem to be necessary for now.

        return None
