import docker
from base import BaseManager, BaseContainer


class LocalManager(BaseManager):

    def __init__(self):
        self.__client = docker.from_env().containers

    def run(self, image_name, cmd, **kwargs):
        return self.__client.run(image_name, cmd, **kwargs)

    def get_url(self, container_name):
        container = self.__client.get(container_name)
        port = container. \
            attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
        return 'http://localhost:{}'.format(port)

    def list(self, filters={}):
        return self.__client.list(filters=filters)


class LocalContainer(BaseContainer):

    def remove(self):
        raise NotImplementedError()

    def logs(self):
        raise NotImplementedError()
