import docker

class DockerClient():

    def run(self, image_name, cmd, **kwargs):
        if (not ':' in image_name):
            image_name += ':latest'
            # SDK pull without tag pulls every version; not what I expected.
            # https://github.com/docker/docker-py/issues/1510
        client = docker.from_env()
        return client.containers.run(image_name, cmd, **kwargs)