## class DockerClientWrapper
### lookup_container_port(self, container_name)
Given the name of a container, returns the host port mapped to port 80.
### purge_by_label(self, label)
Removes all containers matching the label.
### purge_inactive(self, seconds)
Removes containers which do not have recent log entries.
### run(self, image_name, cmd=None, **kwargs)
Wraps the SDK's run() method.
### ROOT_LABEL = 'io.github.refinery-project.django_docker_engine'
## class DockerContainerSpec
### __init__(self, image_name, container_name, input={}, container_input_path='/tmp/input.json', labels={})
### run(self)
