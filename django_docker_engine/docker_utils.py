import json
import logging
import os
from datetime import datetime
from time import time
from container_managers import docker_engine


logging.basicConfig()
logger = logging.getLogger(__name__)


class DockerContainerSpec():

    def __init__(self, image_name, container_name,
                 input={},
                 container_input_path='/tmp/input.json',
                 extra_directories=[],
                 labels={}):
        self.image_name = image_name
        self.container_name = container_name
        self.container_input_path = container_input_path
        self.extra_directories = extra_directories
        self.input = input
        self.labels = labels


class DockerClientWrapper():

    def __init__(self,
                 manager=docker_engine.DockerEngineManager(),
                 root_label='io.github.refinery-project.django_docker_engine'):
        self._containers_manager = manager
        self.root_label = root_label

    def _make_directory_on_host(self):
        return self._containers_manager.mkdtemp()

    def _write_input_to_host(self, input):
        host_input_dir = self._make_directory_on_host()
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

        for directory in container_spec.extra_directories:
            assert os.path.isabs(directory), \
                "Specified path: `{}` is not absolute".format(directory)
            volume_spec.append({'bind': directory})

        volumes = {}
        for volume in volume_spec:
            binding = volume.copy()
            if binding.get('mode'):
                raise RuntimeError(
                    '"mode" should not be provided on {}'.format(volume))
            host_directory = binding.pop('host', None)
            if host_directory:
                binding['mode'] = 'ro'  # For now, this is true.
            else:
                # In contrast, this will *always* be true.
                binding['mode'] = 'rw'
                host_directory = self._make_directory_on_host()

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

    def pull(self, image_name, version="latest"):
        self._containers_manager.pull(image_name, version=version)

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
        logger.warn('purge_inactive')
        for container in self.list():
            logger.warn('container: %s', container)
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
            logger.warn('seconds_since_start < seconds')
            return True
        else:
            recent_log = container.logs(since=int(time() - seconds))
            # Logs are empty locally, but must contain something on travis?
            logger.warn('logs: [%s]', recent_log)
            # Doesn't work with non-integer values:
            # https://github.com/docker/docker-py/issues/1515
            return recent_log != ''
