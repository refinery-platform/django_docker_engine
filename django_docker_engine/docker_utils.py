import json
import logging
import os
from datetime import datetime
from shutil import rmtree
from time import time

import docker.errors

from django_docker_engine.container_managers import docker_engine
from django_docker_engine.historian import FileHistorian

logging.basicConfig()
logger = logging.getLogger(__name__)


class DockerContainerSpec():

    def __init__(self, image_name, container_name,
                 input={},  # noqa: A002
                 container_input_path='/tmp/input.json',
                 extra_directories=[],
                 labels={},
                 container_port=80,
                 cpus=0.5,
                 mem_reservation_mb=None):
        self.image_name = image_name
        self.container_name = container_name
        self.container_input_path = container_input_path
        self.extra_directories = extra_directories
        self.input = input
        self.labels = labels
        self.container_port = container_port
        self.cpus = cpus
        self.mem_reservation_mb = mem_reservation_mb

    def __repr__(self):
        kwargs = ', '.join(
            ['{}={}'.format(a, repr(getattr(self, a)))
             for a in dir(self)
             if not a.startswith('_')])
        name = self.__class__.__name__
        return '{}({})'.format(name, kwargs)


class DockerClientSpec():

    def __init__(self,
                 do_input_json_envvar=False,
                 input_json_url=None):
        assert do_input_json_envvar or input_json_url,\
            'Input must be provided to the container '\
            'as an environment variable containing json '\
            'or an environment variable containing a url pointing to json'
        # Both can be specified: The container needs to be able
        # to read from at least one specified source. Limitations:
        # - do_input_json_envvar:
        #   Creates potentially problematic huge envvar
        # - input_json_url:
        #   World-readable URL could be an unwanted leak
        self.do_input_json_envvar = do_input_json_envvar
        self.input_json_url = input_json_url


_DEFAULT_MANAGER = docker_engine.DockerEngineManager
_DEFAULT_LABEL = 'io.github.refinery-project.django_docker_engine'
_MEM_RESERVATION_MB = '.mem_reservation_mb'


class DockerClientWrapper(object):

    def __init__(self,
                 historian=None,
                 manager_class=_DEFAULT_MANAGER,
                 root_label=_DEFAULT_LABEL):
        self._historian = FileHistorian() if historian is None else historian
        self._containers_manager = manager_class(root_label)

    def is_live(self, container_name):
        try:
            self._containers_manager.get_url(container_name)
        except (docker_engine.ExpectedPortMissing, docker.errors.NotFound):
            # Other errors could be thrown, but only those that should
            # eventually resolve on their own should be included here.
            return False
        else:
            return True

    def lookup_container_url(self, container_name):
        """
        Given the name of a container, returns the url mapped to the right port.
        """
        return self._containers_manager.get_url(container_name)

    def lookup_container_id(self, container_name):
        return self._containers_manager.get_id(container_name)

    def list(self, filters={}):
        return self._containers_manager.list(filters)

    def logs(self, container_name):
        return self._containers_manager.logs(container_name)

    def history(self, container_name):
        id = self.lookup_container_id(container_name)
        return FileHistorian().list(id)

    @staticmethod
    def kill(container):
        mounts = container.attrs['Mounts']
        container.remove(
            force=True,
            v=True  # Remove volumes associated with the container
        )
        for mount in mounts:
            source = mount['Source']
            target = source if os.path.isdir(
                source) else os.path.dirname(source)
            rmtree(
                target,
                ignore_errors=True
            )

    def _kill_lru(self, need_to_free):
        '''
        Kill least-recently-used containers until need_to_free reserved memory
        has been freed. Runs asynchronously: When this returns, the containers
        are still running, but will shut down shortly.
        '''
        container_ids = [container.id for container in self.list()]
        # TODO: Historian class should be parameterized.
        lru_sorted = self._historian.sort_lru(container_ids)
        memory_freed = 0
        while memory_freed < need_to_free:
            if len(lru_sorted) == 0:
                logger.warn('No more containers to kill, but we still do not '
                            'have the requested memory; Starting anyway!')
                break
            next_id = lru_sorted.pop(0)
            next_container = self._containers_manager.get_container(next_id)
            mem_reservation_mb = self._mem_reservation_mb(next_container)
            memory_freed += mem_reservation_mb
            self.kill(next_container)
            logger.warn(
                'Killed {} to free up {}MB: {}MB freed so far. '
                'Need to free {}.'.format(
                    next_container.name, mem_reservation_mb, memory_freed,
                    need_to_free))

    def _mem_reservation_mb(self, container):
        return int(container.labels.get(_DEFAULT_LABEL + _MEM_RESERVATION_MB))

    def _total_mem_reservation_mb(self):
        containers = self.list()
        return sum(
            self._mem_reservation_mb(container) for container in containers
        )

    def _purge(self, label=None, seconds=None):
        # TODO: Remove. kill_lru should be used instead.
        for container in self.list({'label': label} if label else {}):
            # TODO: Confirm that the container belongs to me
            if seconds and self._is_active(container, seconds):
                continue
            self.kill(container)

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

    def pull(self, image_name, version="latest"):
        self._containers_manager.pull(image_name, version=version)


class DockerClientRunWrapper(DockerClientWrapper):

    def __init__(self,
                 docker_client_spec,
                 manager_class=_DEFAULT_MANAGER,
                 root_label=_DEFAULT_LABEL,
                 ssh_username=None,
                 mem_limit_mb=float('inf')):
        super(DockerClientRunWrapper, self).__init__(
            manager_class=manager_class,
            root_label=root_label
        )
        manager_kwargs = {}
        if ssh_username:
            manager_kwargs['ssh_username'] = ssh_username
        self._containers_manager = manager_class(root_label, **manager_kwargs)
        self.root_label = root_label
        self._do_input_json_envvar = docker_client_spec.do_input_json_envvar
        self._input_json_url = docker_client_spec.input_json_url
        self._mem_limit_mb = mem_limit_mb

    def _make_volume_on_host(self):
        return self._containers_manager.create_volume().name

    def run(self, container_spec):
        """
        Run a given ContainerSpec. Returns the url for the container,
        in contrast to the underlying method, which returns the logs.
        """

        total_mem_reservation_mb = self._total_mem_reservation_mb()
        new_mem_reservation_mb = container_spec.mem_reservation_mb or 0
        # If None (ie, unspecified), treat as 0.

        need_to_free = (
            new_mem_reservation_mb + total_mem_reservation_mb
            - self._mem_limit_mb)
        if need_to_free > 0:
            logger.warn(
                '{}MB requested + {}MB in use - {}MB limit = {}MB > 0'.format(
                    new_mem_reservation_mb,
                    total_mem_reservation_mb,
                    self._mem_limit_mb,
                    need_to_free
                ))
            self._kill_lru(need_to_free)

        image_name = container_spec.image_name
        if (':' not in image_name):
            image_name += ':latest'
            # Without a tag the SDK pulls every version; not what I expected.
            # https://github.com/docker/docker-py/issues/1510

        volume_spec = []

        for directory in container_spec.extra_directories:
            assert os.path.isabs(directory), \
                "Specified path: `{}` is not absolute".format(directory)
            volume_spec.append({'bind': directory})

        volumes = {}
        for volume in volume_spec:
            binding = volume.copy()
            assert not binding.get('mode'), \
                '"mode" should not be provided on {}'.format(volume)
            host_directory = binding.pop('host', None)
            if host_directory:
                # Typically for mounting user input
                binding['mode'] = 'ro'
                volumes[host_directory] = binding
            else:
                # Typically for storing data produced by the app itself
                binding['mode'] = 'rw'
                volume_name = self._make_volume_on_host()
                volumes[volume_name] = binding

        labels = container_spec.labels
        labels.update({
            self.root_label: 'true',
            self.root_label + '.port': str(container_spec.container_port),
            self.root_label + _MEM_RESERVATION_MB: str(container_spec.mem_reservation_mb)
        })

        environment = {}
        if self._do_input_json_envvar:
            environment['INPUT_JSON'] = json.dumps(container_spec.input)
        if self._input_json_url:
            environment['INPUT_JSON_URL'] = self._input_json_url

        self._containers_manager.run(
            image_name,
            name=container_spec.container_name,
            ports={'{}/tcp'.format(container_spec.container_port): None},
            cmd=None,
            detach=True,
            labels=labels,
            volumes=volumes,
            nano_cpus=int(container_spec.cpus * 1e9),
            environment=environment,
            mem_reservation='{}M'.format(new_mem_reservation_mb),
        )
        return self.lookup_container_url(container_spec.container_name)
