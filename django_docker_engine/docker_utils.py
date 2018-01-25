import json
import logging
import os
from datetime import datetime
from time import time
from container_managers import docker_engine
from shutil import rmtree

logging.basicConfig()
logger = logging.getLogger(__name__)


class DockerContainerSpec():

    def __init__(self, image_name, container_name,
                 input={},
                 container_input_path='/tmp/input.json',
                 extra_directories=[],
                 labels={},
                 container_port=80,
                 cpus=0.5):
        self.image_name = image_name
        self.container_name = container_name
        self.container_input_path = container_input_path
        self.extra_directories = extra_directories
        self.input = input
        self.labels = labels
        self.container_port = container_port
        self.cpus = cpus


class DockerClientWrapper():

    def __init__(self,
                 data_dir,
                 manager_class=docker_engine.DockerEngineManager,
                 root_label='io.github.refinery-project.django_docker_engine'):
        self._containers_manager = manager_class(data_dir, root_label)
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
            # Without a tag the SDK pulls every version; not what I expected.
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
        labels.update({
            self.root_label: 'true',
            self.root_label + '.port': str(container_spec.container_port)
        })

        self._containers_manager.run(
            image_name,
            name=container_spec.container_name,
            ports={'{}/tcp'.format(container_spec.container_port): None},
            cmd=None,
            detach=True,
            labels=labels,
            volumes=volumes,
            nano_cpus=int(container_spec.cpus * 1e9)
        )
        return self.lookup_container_url(container_spec.container_name)

    def lookup_container_url(self, container_name):
        """
        Given the name of a container, returns the url mapped to the right port.
        """
        return self._containers_manager.get_url(container_name)

    def list(self, filters={}):
        return self._containers_manager.list(filters)

    def pull(self, image_name, version="latest"):
        self._containers_manager.pull(image_name, version=version)

    # TODO: Just make this the public method?
    def _purge(self, label=None, seconds=None):
        for container in self.list({'label': label} if label else {}):
            # TODO: Confirm that the container belongs to me
            if seconds and self._is_active(container, seconds):
                continue
            mounts = container.attrs['Mounts']
            container.remove(force=True)
            for mount in mounts:
                source = mount['Source']
                target = source if os.path.isdir(
                    source) else os.path.dirname(source)
                rmtree(
                    target,
                    ignore_errors=True
                )

    def purge_by_label(self, label):
        """
        Removes all containers matching the label.
        """
        self._purge(label=label)

    def purge_inactive(self, seconds):
        """
        Removes containers which do not have recent log entries.
        """
        self._purge(seconds=seconds)

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
            # Logs are empty locally, but must contain something on travis?
            # Doesn't work with non-integer values:
            # https://github.com/docker/docker-py/issues/1515
            return recent_log != ''

    def _get_data_dir(self):
        return self._containers_manager._data_dir
