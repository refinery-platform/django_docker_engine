import re
from django.conf import settings


class HostnameRoutingMiddleware():

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
