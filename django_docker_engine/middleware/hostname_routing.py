import re

class HostnameRoutingMiddleware():
    def process_request(self, request):
        # TODO: Move these to config:
        host_suffix = '.docker.localhost'
        path_prefix = '/docker/'

        request_host_and_port = request.META['HTTP_HOST']
        request_host = re.sub(r':\d+$', '', request_host_and_port)
        if request_host.endswith(host_suffix):
            container_name = request_host[0:-len(host_suffix)]
            request.path_info = path_prefix + container_name + request.path_info
            request.path = path_prefix + container_name + request.path
            # Munging the HTTP_HOST itself does not seem to be necessary for now.

        return None