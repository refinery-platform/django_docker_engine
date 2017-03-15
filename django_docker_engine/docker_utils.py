import docker


class DockerClient():

    def run(self, image_name, cmd=None, **kwargs):
        if (':' not in image_name):
            image_name += ':latest'
            # SDK pull without tag pulls every version; not what I expected.
            # https://github.com/docker/docker-py/issues/1510
        client = docker.from_env()
        return client.containers.run(image_name, cmd, **kwargs)

    def lookup_container_port(self, container_name):
        client = docker.from_env()
        container = client.containers.get(container_name)
        return container.\
            attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
