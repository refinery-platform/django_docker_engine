import re
import subprocess
import sys

import docker


def _get_hostname():
    client = docker.from_env()
    docker_v = [int(i) for i in client.info()['ServerVersion'].split('.')[:2]]
    # Additions here must also be added to ALLOWED_HOSTS in settings.py.
    # https://docs.docker.com/docker-for-mac/networking/
    if docker_v >= [18, 3] and sys.platform == 'darwin':
        return 'host.docker.internal'
    # https://docs.docker.com/v17.06/docker-for-mac/networking/
    elif docker_v >= [17, 6] and sys.platform == 'darwin':
        return 'docker.for.mac.localhost'
    elif sys.platform == 'darwin':
        raise Exception('Not sure of hostname for docker {} on {}'.format(
            docker_v, sys.platform
        ))
    else:
        # https://stackoverflow.com/a/31328031
        lines = subprocess.check_output(
            ['ip', 'addr', 'show', 'docker0']).decode('utf-8').splitlines()
        host_lines = [line for line in lines if line.endswith('docker0')]
        assert len(host_lines) == 1, 'No docker0 line in {}'.format(lines)
        match = re.search(r'\d+\.\d+\.\d+\.\d+', host_lines[0])
        assert match, 'No IP in "{}", from: {}'.format(
            host_lines[0], host_lines)
        return match.group(0)


_HOSTNAME = _get_hostname()


def hostname():
    # 'localhost' will just point to the container, not to the host.
    # The best way of doing this seems to have changed over time.
    # In the future, I hope this will be simplified.

    return _HOSTNAME
