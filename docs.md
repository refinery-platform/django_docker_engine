## class DockerClientWrapper
### __init__(self, manager=<django_docker_engine.container_managers.docker_engine.DockerEngineManager object>, root_label='io.github.refinery-project.django_docker_engine')
### list(self, filters={})
### lookup_container_url(self, container_name)
Given the name of a container, returns the url mapped to port 80.
### purge_by_label(self, label)
Removes all containers matching the label.
### purge_inactive(self, seconds)
Removes containers which do not have recent log entries.
### run(self, image_name, cmd=None, **kwargs)
Wraps the SDK's run() method.
## class DockerContainerSpec
### __init__(self, image_name, container_name, manager, input={}, container_input_path='/tmp/input.json', labels={})
### run(self)
