import docker
import re
from base import BaseManager


class DockerEngineManager(BaseManager):

    def __init__(self, client=docker.from_env(), pem='django_docker_cloudformation.pem'):
        self._base_url = client.api.base_url
        self._containers_client = client.containers
        self.pem = pem

    def run(self, image_name, cmd, **kwargs):
        return self._containers_client.run(image_name, cmd, **kwargs)

    def get_url(self, container_name):
        remote_host_match = re.match(r'^http://([^:]+):\d+$', self._base_url)
        if remote_host_match:
            host = remote_host_match.group(1)
        elif self._base_url == 'http+docker://localunixsocket':
            host = 'localhost'
        else:
            raise RuntimeError('Unexpected client base_url: %s', self._base_url)
        container = self._containers_client.get(container_name)
        port = container. \
            attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
        return 'http://{}:{}'.format(host, port)

    def list(self, filters={}):
        return self._containers_client.list(filters=filters)


# TODO: At some point we need to be more abstract, instead of using the SDK responses directly...
# class DockerEngineContainer(BaseContainer):
#
#     def remove(self):
#         raise NotImplementedError()
#
#     def logs(self):
#         raise NotImplementedError()
