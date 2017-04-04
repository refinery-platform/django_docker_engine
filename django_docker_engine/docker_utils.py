import docker
import json
import os
import re
from datetime import datetime
from time import time


class DockerClientWrapper():
    ROOT_LABEL = 'io.github.refinery-project.django_docker_engine'

    def run(self, image_name, cmd=None, **kwargs):
        """
        Wraps the SDK's run() method.
        """
        if (':' not in image_name):
            image_name += ':latest'
            # Without tag the SDK pulls every version; not what I expected.
            # https://github.com/docker/docker-py/issues/1510
        labels = kwargs.get('labels') or {}
        labels.update({DockerClientWrapper.ROOT_LABEL: 'true'})
        kwargs['labels'] = labels
        client = docker.from_env()
        return client.containers.run(image_name, cmd, **kwargs)

    def lookup_container_port(self, container_name):
        """
        Given the name of a container, returns the host port mapped to port 80.
        """
        client = docker.from_env()
        container = client.containers.get(container_name)
        return container.\
            attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']

    def purge_by_label(self, label):
        """
        Removes all containers matching the label.
        """
        client = docker.from_env()
        for container in client.containers.list(filters={'label': label}):
            # TODO: Confirm that it belongs to me
            container.remove(force=True)

    def purge_inactive(self, seconds):
        """
        Removes containers which do not have recent log entries.
        """
        client = docker.from_env()
        for container in client.containers.list():
            # TODO: Confirm that it belongs to me
            if not self.__is_active(container, seconds):
                container.remove(force=True)

    def __is_active(self, container, seconds):
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

    def __init__(self, image_name, container_name,
                 input={},
                 container_input_path='/tmp/input.json',
                 labels={}):
        self.image_name = image_name
        self.container_name = container_name
        self.container_input_path = container_input_path
        self.input = input
        self.labels = labels

    def __mkdtemp(self):
        # mkdtemp is the obvious way to do this, but
        # the resulting directory is not visible to Docker.
        # Tried chmod, but that didn't help.
        base = '/tmp/django-docker'
        try:
            os.mkdir(base)
        except BaseException:
            pass  # May already exist
        timestamp = re.sub(r'\W', '_', str(datetime.now()))
        dir = os.path.join(base, timestamp)
        os.mkdir(dir)
        return dir

    def run(self):
        host_input_dir = self.__mkdtemp()
        # Host filename is arbitrary.
        host_input_path = os.path.join(host_input_dir, 'input.json')
        with open(host_input_path, 'w') as file:
            file.write(json.dumps(self.input))
        volume_spec = {
            host_input_path: {
                # Path inside container might need to be configurable?
                'bind': self.container_input_path,
                'mode': 'ro'}}
        ports_spec = {'80/tcp': None}
        client = DockerClientWrapper()
        client.run(self.image_name,
                   name=self.container_name,
                   detach=True,
                   volumes=volume_spec,
                   ports=ports_spec,
                   labels=self.labels)
        # Metadata on the returned container object (like the assigned port)
        # is not complete, so we do a redundant lookup.
        return client.lookup_container_port(self.container_name)
