import docker
import re
from base import BaseManager
import logging
import paramiko
from abc import ABCMeta, abstractmethod
from distutils import dir_util


class DockerEngineManager(BaseManager):

    def __init__(self, client=docker.from_env(), pem='django_docker_cloudformation.pem'):
        self._base_url = client.api.base_url
        self._containers_client = client.containers
        self.pem = pem

        remote_host_match = re.match(r'^http://([^:]+):\d+$', self._base_url)
        if remote_host_match:
            self.host_files = _RemoteHostFiles(remote_host_match.group(1), self.pem)
        elif self._base_url == 'http+docker://localunixsocket':
            self.host_files = _LocalHostFiles()
        else:
            raise RuntimeError('Unexpected client base_url: %s', self._base_url)

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
    def __init__(self, host, pem):
        key = paramiko.RSAKey.from_private_key_file(pem)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname=host, username='ec2-user', pkey=key)

    def _exec(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        logging.info('command: %s', command)
        logging.info('STDOUT: %s', stdout.read())
        logging.info('STDERR: %s', stderr.read())

    def write(self, path, content):
        self._exec("cat > {} <<'END_CONTENT'\n{}\nEND_CONTENT".format(path, content))

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
