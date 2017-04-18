import json
import os
import re
from datetime import datetime
from time import time
from container_managers import local as local_manager


class DockerClientWrapper():
    def __init__(self,
                 manager=local_manager.LocalManager(),
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

    def __init__(self, image_name, container_name,
                 input={},
                 container_input_path='/tmp/input.json',
                 labels={},
                 manager=None):
        if not manager:
            raise RuntimeError('"manager" is required')
        self.manager = manager
        self.image_name = image_name
        self.container_name = container_name
        self.container_input_path = container_input_path
        self.input = input
        self.labels = labels

    def _mkdtemp(self):
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
        host_input_dir = self._mkdtemp()
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
