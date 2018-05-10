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
    elif sys.platform in ['darwin', 'win32']:
        raise Exception('Not sure of hostname for docker {} on {}'.format(
            docker_v, sys.platform
        ))
    else:
        # This wouldn't work on Mac because:
        #  -- "ip" is not installed by default
        #  -- The "docker0" bridge is in the VM, but not on the Mac itself.
        lines = subprocess.check_output(
            ['ip', 'route']).decode('utf-8').splitlines()
        host_lines = [line for line in lines if 'docker0' in line]
        assert len(host_lines) == 1,\
            'Expected exactly 1 "docker0" line in {}'.format(lines)
        ip = host_lines[0].strip().split(' ')[-1]
        assert re.match(r'\d+\.\d+\.\d+\.\d+', ip),\
            'Last element not ip: {}'.format(host_lines[0])
        return ip


_HOSTNAME = _get_hostname()


def hostname():
    # 'localhost' will just point to the container, not to the host.
    # The best way of doing this seems to have changed over time.
    # In the future, I hope this will be simplified.

    return _HOSTNAME
