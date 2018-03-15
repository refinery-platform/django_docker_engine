import os
import re
import subprocess
from abc import ABCMeta, abstractmethod
from datetime import datetime
from distutils import dir_util

import docker

from base import BaseManager


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


class DockerEngineManager(BaseManager):

    def __init__(
            self,
            data_dir,
            root_label,
            client=docker.from_env(),
            pem=None,
            ssh_username=None
    ):
        self._base_url = client.api.base_url
        self._containers_client = client.containers
        self._images_client = client.images
        self._data_dir = data_dir
        self._root_label = root_label

        remote_host = self._get_base_url_remote_host()
        if remote_host:
            self.host_files = _RemoteHostFiles(
                host=remote_host,
                pem=pem,
                ssh_username=ssh_username)
        elif self._is_base_url_local():
            self.host_files = _LocalHostFiles()
        else:
            raise RuntimeError(
                'Unexpected client base_url: %s', self._base_url)

    def _get_base_url_remote_host(self):
        remote_host_match = re.match(r'^http://([^:]+):\d+$', self._base_url)
        if remote_host_match:
            return remote_host_match.group(1)

    def _is_base_url_local(self):
        return self._base_url in [
            'http+docker://' + host for host in ['localunixsocket', 'localhost']
        ]

    def run(self, image_name, cmd, **kwargs):
        # In particular, passing "environment" as a kwarg
        # will set environment variables.
        return self._containers_client.run(image_name, cmd, **kwargs)

    def pull(self, image_name, version="latest"):
        return self._images_client.pull("{}:{}".format(image_name, version))

    def get_url(self, container_name):
        remote_host = self._get_base_url_remote_host()
        if remote_host:
            host = remote_host
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
        return self._containers_client.list(all=True, filters=filters)

    def mkdtemp(self):
        timestamp = re.sub(r'\W', '_', str(datetime.now()))
        tmp_dir = os.path.join(self._data_dir, timestamp)
        self.host_files.mkdir_p(tmp_dir)
        return tmp_dir


class _HostFiles:
    __metaclass__ = ABCMeta

    @abstractmethod
    def write(self, path, content):
        raise NotImplementedError()

    @abstractmethod
    def mkdir_p(self, path):
        raise NotImplementedError()


class _LocalHostFiles(_HostFiles):
    def __init__(self):
        pass

    def write(self, path, content):
        with open(path, 'w') as file:
            file.write(content)
            file.write('\n')
            # TODO: For consistency with heredoc in _RemoteHostFiles, add a newline...
            # I don't think this hurts with JSON, but not ideal.

    def mkdir_p(self, path):
        dir_util.mkpath(path)


class _RemoteHostFiles(_HostFiles):
    # TODO: Try again with paramiko: https://github.com/paramiko/paramiko/issues/959
    def __init__(self, host, pem, ssh_username=None,
                 strict_host_key_checking=False):
        self.host = host
        self.pem = pem
        self.ssh_username = ssh_username
        self.strict_host_key_checking = strict_host_key_checking

    def _exec(self, command):
        cmd_tokens = ['ssh']
        if not self.strict_host_key_checking:
            cmd_tokens.append('-oStrictHostKeyChecking=no')
        if self.pem:
            cmd_tokens.extend(['-i', self.pem])
        if self.ssh_username:
            cmd_tokens.append('{}@{}'.format(self.ssh_username, self.host))
        else:
            cmd_tokens.append(self.host)
        cmd_tokens.append(command)
        subprocess.check_call(cmd_tokens)

    def write(self, path, content):
        self._exec(
            "cat > {} <<'END_CONTENT'\n{}\nEND_CONTENT".format(path, content))

    def mkdir_p(self, path):
        self._exec('mkdir -p {}'.format(path))

# TODO: At some point we need to be more abstract,
#       instead of using the SDK responses directly...
# class DockerEngineContainer(BaseContainer):
#
#     def remove(self):
#         raise NotImplementedError()
#
#     def logs(self):
#         raise NotImplementedError()
