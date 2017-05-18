import json
import os
from datetime import datetime
from time import time
from container_managers import docker_engine


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


class DockerClientWrapper():

    def __init__(self,
                 manager=docker_engine.DockerEngineManager(),
                 root_label='io.github.refinery-project.django_docker_engine'):
        self._containers_manager = manager
        self.root_label = root_label

    def _write_input_to_host(self, input):
        host_input_dir = self._containers_manager.mkdtemp()
        # The host filename "input.json" is arbitrary.
        host_input_path = os.path.join(host_input_dir, 'input.json')
        content = json.dumps(input)
        self._containers_manager.host_files.write(host_input_path, content)
        return host_input_path

    def run(self, container_spec):
        """
        Run a given ContainerSpec. Returns the url for the container,
        in contrast to the underlying method, which returns the logs.
        """
        image_name = container_spec.image_name
        if (':' not in image_name):
            image_name += ':latest'
            # Without tag the SDK pulls every version; not what I expected.
            # https://github.com/docker/docker-py/issues/1510

        # TODO: With the tmp volumes in the other branch, this will change.
        # It's untidy right now, but let it be until that merge.
        volume_spec = [{
            'host': self._write_input_to_host(container_spec.input),
            'bind': container_spec.container_input_path}]
        volumes = {}
        for volume in volume_spec:
            binding = volume.copy()
            if binding.get('mode'):
                raise RuntimeError('"mode" should not be provided on {}'.format(volume))
            host_directory = binding.pop('host', None)
            if host_directory:
                binding['mode'] = 'ro'  # For now, this is true.
            else:
                binding['mode'] = 'rw'  # In contrast, this will *always* be true.
                host_directory = self._containers_manager.mkdtemp()
                volumes[host_directory] = binding

        labels = container_spec.labels
        labels.update({self.root_label: 'true'})

        self._containers_manager.run(
            image_name,
            name=container_spec.container_name,
            ports={'80/tcp': None},
            cmd=None,
            detach=True,
            labels=labels,
            volumes=volumes
        )
        return self.lookup_container_url(container_spec.container_name)

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
