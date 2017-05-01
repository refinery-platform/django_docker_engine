import json
import os
import re
import logging
import subprocess
import tempfile
import paramiko
from abc import ABCMeta, abstractmethod
from datetime import datetime
from time import time
from container_managers import docker_engine


class DockerClientWrapper():
    def __init__(self,
                 manager=docker_engine.DockerEngineManager(),
                 root_label='io.github.refinery-project.django_docker_engine'):
        self._containers_manager = manager
        self.root_label = root_label

    def run(self, image_name, cmd=None, **kwargs):
        """
        Wraps the SDK's run() method.
        """
        if (':' not in image_name):
            image_name += ':latest'
            # Without tag the SDK pulls every version; not what I expected.
            # https://github.com/docker/docker-py/issues/1510
        labels = kwargs.get('labels') or {}
        labels.update({self.root_label: 'true'})
        kwargs['labels'] = labels
        return self._containers_manager.run(image_name, cmd, **kwargs)

    def lookup_container_url(self, container_name):
        """
        Given the name of a container, returns the url mapped to port 80.
        """
        return self._containers_manager.get_url(container_name)

    def list(self, filters={}):
        return self._containers_manager.list(filters)

    def purge_by_label(self, label):
        """
        Removes all containers matching the label.
        """
        for container in self.list({'label': label}):
            # TODO: Confirm that it belongs to me
            container.remove(force=True)

    def purge_inactive(self, seconds):
        """
        Removes containers which do not have recent log entries.
        """
        for container in self.list():
            # TODO: Confirm that it belongs to me
            if not self._is_active(container, seconds):
                container.remove(force=True)

    def _is_active(self, container, seconds):
        utc_start_string = container.attrs['State']['StartedAt']
        utc_start = datetime.strptime(
            utc_start_string[:19], '%Y-%m-%dT%H:%M:%S')
        utc_now = datetime.utcnow()
        seconds_since_start = (utc_now - utc_start).total_seconds()
        if seconds_since_start < seconds:
            return True
        else:
            recent_log = container.logs(since=int(time() - seconds))
            # Doesn't work with non-integer values:
            # https://github.com/docker/docker-py/issues/1515
            return recent_log != ''


class DockerContainerSpec():

    def __init__(self, image_name, container_name, manager,
                 input={},
                 container_input_path='/tmp/input.json',
                 labels={}):
        self.manager = manager
        self.image_name = image_name
        self.container_name = container_name
        self.container_input_path = container_input_path
        self.input = input
        self.labels = labels

        # TODO: perhaps instead of embedding a HostFiles object here,
        # it would make more sense for the manager to offer those operations?
        # Then we wouldn't need to access the _base_url here.
        remote_host_match = re.match(r'^http://([^:]+):\d+$', manager._base_url)
        if remote_host_match:
            self.host_files = RemoteHostFiles(remote_host_match.group(1), manager.pem)
        elif manager._base_url == 'http+docker://localunixsocket':
            self.host_files = LocalHostFiles()
        else:
            raise RuntimeError('Unexpected client base_url: %s', self._base_url)


    def _mkdtemp(self):
        base = '/tmp/django-docker'
        timestamp = re.sub(r'\W', '_', str(datetime.now()))
        dir = os.path.join(base, timestamp)
        self.host_files.mkdir_p(dir)
        return dir

    def _write_input_to_host(self):
        host_input_dir = self._mkdtemp()
        # The host filename "input.json" is arbitrary.
        host_input_path = os.path.join(host_input_dir, 'input.json')
        content = json.dumps(self.input)
        self.host_files.write(host_input_path, content)
        return host_input_path

    def run(self):
        host_input_path = self._write_input_to_host()
        volume_spec = {
            host_input_path: {
                # Path inside container might need to be configurable?
                'bind': self.container_input_path,
                'mode': 'ro'}}
        ports_spec = {'80/tcp': None}
        client = DockerClientWrapper(manager=self.manager)
        client.run(self.image_name,
                   name=self.container_name,
                   detach=True,
                   volumes=volume_spec,
                   ports=ports_spec,
                   labels=self.labels)
        # Metadata on the returned container object (like the assigned port)
        # is not complete, so we do a redundant lookup.
        return client.lookup_container_url(self.container_name)


class HostFiles:
    __metaclass__ = ABCMeta

    @abstractmethod
    def write(self, path, content):
        raise NotImplementedError()

    @abstractmethod
    def mkdir_p(self, path):
        raise NotImplementedError()

class LocalHostFiles(HostFiles):
    def __init__(self):
        pass

    def write(self, path, content):
        with open(path, 'w') as file:
            file.write(content)

    def mkdir_p(self, path):
        try:
            os.mkdir(os.path.basename(path))
        except BaseException:
            pass  # May already exist
        os.mkdir(path)

class RemoteHostFiles(HostFiles):
    def __init__(self, host, pem):
        self.host = host
        self.pem = pem

    def _exec(self, command):
        key = paramiko.RSAKey.from_private_key_file(self.pem)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.host, username='ec2-user', pkey=key)
        stdin, stdout, stderr = client.exec_command(command)
        logging.info('command: %s', command)
        logging.info('STDOUT: %s', stdout.read())
        logging.info('STDERR: %s', stderr.read())

    def write(self, path, content):
        (os_handle, temp_path) = tempfile.mkstemp()
        with open(temp_path, 'w') as f:
            f.write(content)
        subprocess.check_call([
            'scp',
            '-o', 'StrictHostKeyChecking=no',
            '-i', self.pem,
            temp_path,
            'ec2-user@{}:{}'.format(self.host, path)
        ])
        # TODO: If we chmod locally, are permissions preserved?
        self._exec('chmod 644 {}'.format(path))
        os.unlink(temp_path)

    def mkdir_p(self, path):
        self._exec('mkdir -p {}'.format(path))
