from base import BaseManager, BaseContainer


class EcsManager(BaseManager):

    def run(self, image_name, cmd, **kwargs):
        raise NotImplementedError()

    def get(self, container_name):
        raise NotImplementedError()

    def list(self, filters={}):
        raise NotImplementedError()


class EcsContainer(BaseContainer):

    def remove(self):
        raise NotImplementedError()

    def logs(self):
        raise NotImplementedError()
