## class DockerClientWrapper
### __init__(self, data_dir, manager_class=<class 'django_docker_engine.container_managers.docker_engine.DockerEngineManager'>, root_label='io.github.refinery-project.django_docker_engine')
### list(self, filters={})
### lookup_container_url(self, container_name)
Given the name of a container, returns the url mapped to port 80.
### pull(self, image_name, version='latest')
### purge_by_label(self, label)
Removes all containers matching the label.
### purge_inactive(self, seconds)
Removes containers which do not have recent log entries.
### run(self, container_spec)
Run a given ContainerSpec. Returns the url for the container,
in contrast to the underlying method, which returns the logs.
## class DockerContainerSpec
### __init__(self, image_name, container_name, input={}, container_input_path='/tmp/input.json', extra_directories=[], labels={})
