import re

import docker

from .base import BaseManager


class DockerEngineManagerError(Exception):
    pass


class NoPortLabel(DockerEngineManagerError):
    pass


class NoPortsOpen(DockerEngineManagerError):
    pass


class ExpectedPortMissing(DockerEngineManagerError):
    pass


class MisconfiguredPort(DockerEngineManagerError):
    pass


class PossiblyOutOfDiskSpace(DockerEngineManagerError):
    # TODO: Can we find a way to determine if disk space is really the problem?
    pass


class DockerEngineManager(BaseManager):
    """
    Manages interactions with a Docker Engine, running locally, or on a remote
    host.
    """

    def __init__(
            self,
            root_label,
            client=docker.from_env(),
    ):
        """
        :param string root_label:
        :param client: The default behavior matches that of the Docker CLI:
        The DOCKER_HOST environment variable specifies where the Docker Engine
        is. To override this, create a DockerClient with the correct base_url
        and provide it here.
        """
        self._base_url = client.api.base_url
        self._containers_client = client.containers
        self._images_client = client.images
        self._volumes_client = client.volumes
        self._root_label = root_label

    def _get_base_url_remote_host(self):
        remote_host_match = re.match(r'^http://([^:]+):\d+$', self._base_url)
        if remote_host_match:
            return remote_host_match.group(1)

    def _is_base_url_local(self):
        return self._base_url in [
            'http+docker://' + host for host in
            ['localunixsocket', 'localhost']
        ]

    def run(self, image_name, cmd, **kwargs):
        """
        :param image_name:
        :param cmd:
        :param kwargs:
        :return:
        """
        try:
            return self._containers_client.run(image_name, cmd, **kwargs)
        except docker.errors.ImageNotFound as e:
            raise PossiblyOutOfDiskSpace(e)

    def pull(self, image_name, version="latest"):
        """
        :param image_name:
        :param version:
        :return:
        """
        full_name = "{}:{}".format(image_name, version)
        try:
            return self._images_client.pull(full_name)
        except docker.errors.ImageNotFound as e:
            raise PossiblyOutOfDiskSpace(e)

    def create_volume(self):
        return self._volumes_client.create(driver='local')

    def get_id(self, container_name):
        """
        :param container_name:
        :return: container id
        """
        return self._containers_client.get(container_name).id

    def get_container(self, container_name_or_id):
        """
        :param container_name:
        :return: container id
        """
        return self._containers_client.get(container_name_or_id)

    def get_url(self, container_name):
        """
        :param container_name:
        :return: container url
        """
        remote_host = self._get_base_url_remote_host()
        if remote_host:
            host = remote_host  # pragma: no cover
        elif self._is_base_url_local():
            host = 'localhost'
        else:
            raise RuntimeError(
                'Unexpected client base_url: %s', self._base_url)
        container = self._containers_client.get(container_name)

        port_key = self._root_label + '.port'
        try:
            container_port = container.attrs['Config']['Labels'][port_key]
        except KeyError:
            raise NoPortLabel(
                'On container {}, no label with key {}'.format(
                    container_name, port_key
                )
            )

        settings = container.attrs['NetworkSettings']
        port_infos = settings['Ports']
        if port_infos is None:
            raise NoPortsOpen(
                'Container {} has no ports: {}'.format(
                    container_name, settings
                )
            )

        try:
            http_port_info = port_infos['{}/tcp'.format(container_port)]
        except KeyError:
            raise ExpectedPortMissing(
                'On container {}, port {} is not available, but these are: {}'.format(
                    container_name, container_port, port_infos
                )
            )

        if http_port_info is None:
            raise MisconfiguredPort(
                'On container {}, port {} is misconfigured; port info: {}'.format(
                    container_name, container_port, port_infos
                )
            )

        # TODO: Can we produce this condition in a test?
        assert len(http_port_info) == 1
        port_number = http_port_info[0]['HostPort']
        return 'http://{}:{}'.format(host, port_number)

    def list(self, filters={}):
        """
        :param dict filters: Filters as described for the SDK:
        https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.list
        :return: List of Docker SDK Containers
        """  # noqa
        return self._containers_client.list(all=True, filters=filters)

    def logs(self, container_name):
        """
        :param container_name:
        :return: STDOUT and STDERR from the Docker container
        """
        container = self._containers_client.get(container_name)
        return container.logs(timestamps=True)


# TODO: At some point we need to be more abstract,
#       instead of using the SDK responses directly...
# class DockerEngineContainer(BaseContainer):
#
#     def remove(self):
#         raise NotImplementedError()
#
#     def logs(self):
#         raise NotImplementedError()
