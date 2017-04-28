import docker
from base import BaseManager, BaseContainer


class DockerEngineManager(BaseManager):

    def __init__(self, client=docker.from_env()):
        self._containers_client = client.containers

    def run(self, image_name, cmd, **kwargs):
        return self._containers_client.run(image_name, cmd, **kwargs)

    def get_url(self, container_name):
        container = self._containers_client.get(container_name)
        port = container. \
            attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
        return 'http://localhost:{}'.format(port)

    def list(self, filters={}):
        return self._containers_client.list(filters=filters)


class DockerEngineContainer(BaseContainer):

    def remove(self):
        raise NotImplementedError()

    def logs(self):
        raise NotImplementedError()
