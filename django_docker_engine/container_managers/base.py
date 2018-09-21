import abc
import sys

if sys.version_info >= (3, 4):  # pragma: no cover
    ABC = abc.ABC
else:
    ABC = abc.ABCMeta('ABC', (), {})


class BaseManager(ABC):  # pragma: no cover
    """
    This provides an interface which satisfies both local and remote Docker use.
    The methods are based on a subset of those provided by
    https://docker-py.readthedocs.io/en/stable/containers.html
    and implementers should return the same kind of results as the the SDK returns.

    The plan is to write a wrapper for AWS ECS which will conform to the same
    interface.
    """

    @abc.abstractmethod
    def run(self, image_name, cmd, **kwargs):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_url(self, container_name):
        raise NotImplementedError()

    @abc.abstractmethod
    def list(self, filters={}):
        raise NotImplementedError()
