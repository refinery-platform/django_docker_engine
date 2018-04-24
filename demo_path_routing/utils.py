import sys

import docker


def hostname():
    # 'localhost' will just point to the container, not to the host.
    # The best way of doing this seems to have changed over time.
    # In the future, I hope this will be simplified.
    client = docker.from_env()
    docker_v = [int(i) for i in client.info()['ServerVersion'].split('.')[:2]]
    # Additions here must also be added to ALLOWED_HOSTS in settings.py.
    # https://docs.docker.com/docker-for-mac/networking/
    if docker_v >= [18, 3] and sys.platform == 'darwin':
        return 'host.docker.internal'
    # https://docs.docker.com/v17.06/docker-for-mac/networking/
    elif docker_v >= [17, 6] and sys.platform == 'darwin':
        return 'docker.for.mac.localhost'
    else:
        raise Exception('Not sure of hostname for docker {} on {}'.format(
            docker_v, sys.platform
        ))
