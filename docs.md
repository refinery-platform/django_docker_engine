## class DockerClientRunWrapper(DockerClientWrapper)
### Method resolution order:
DockerClientRunWrapper
DockerClientWrapper
__builtin__.object
### __init__(self, docker_client_spec, manager_class=<class 'django_docker_engine.container_managers.docker_engine.DockerEngineManager'>, root_label='io.github.refinery-project.django_docker_engine', pem=None, ssh_username=None)
### run(self, container_spec)
Run a given ContainerSpec. Returns the url for the container,
in contrast to the underlying method, which returns the logs.
### Methods inherited from DockerClientWrapper:
### list(self, filters={})
### lookup_container_url(self, container_name)
Given the name of a container, returns the url mapped to the right port.
### pull(self, image_name, version='latest')
### purge_by_label(self, label)
Removes all containers matching the label.
### purge_inactive(self, seconds)
Removes containers which do not have recent log entries.
### Data descriptors inherited from DockerClientWrapper:
### __dict__
dictionary for instance variables (if defined)
### __weakref__
list of weak references to the object (if defined)
## class DockerClientSpec
### __init__(self, data_dir, do_input_json_file=False, do_input_json_envvar=False, input_json_url=None)
## class DockerClientWrapper(__builtin__.object)
### __init__(self, manager_class=<class 'django_docker_engine.container_managers.docker_engine.DockerEngineManager'>, root_label='io.github.refinery-project.django_docker_engine')
### list(self, filters={})
### lookup_container_url(self, container_name)
Given the name of a container, returns the url mapped to the right port.
### pull(self, image_name, version='latest')
### purge_by_label(self, label)
Removes all containers matching the label.
### purge_inactive(self, seconds)
Removes containers which do not have recent log entries.
### __dict__
dictionary for instance variables (if defined)
### __weakref__
list of weak references to the object (if defined)
## class DockerContainerSpec
### __init__(self, image_name, container_name, input={}, container_input_path='/tmp/input.json', extra_directories=[], labels={}, container_port=80, cpus=0.5)
