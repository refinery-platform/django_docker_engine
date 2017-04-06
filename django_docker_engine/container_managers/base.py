from abc import ABCMeta, abstractmethod

"""
This provides an interface which satisfies both local and remote Docker use.
The methods are based on a subset of those provided by
https://docker-py.readthedocs.io/en/stable/containers.html
and implementers should return the same kind of results as the the SDK returns.

The plan is to write a wrapper for AWS ECS which will conform to the same
interface.
"""


class BaseManager:

    __metaclass__ = ABCMeta

    @abstractmethod
    def run(self, image_name, cmd, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def get(self, container_name):
        raise NotImplementedError()

    @abstractmethod
    def list(self, filters={}):
        raise NotImplementedError()


class BaseContainer:

    __metaclass__ = ABCMeta

    @abstractmethod
    def remove(self):
        raise NotImplementedError()

    @abstractmethod
    def logs(self):
        raise NotImplementedError()
