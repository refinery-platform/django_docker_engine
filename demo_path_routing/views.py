import os
import re

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from django_docker_engine.docker_utils import (DockerClientRunWrapper,
                                               DockerClientSpec,
                                               DockerContainerSpec)

from .forms import LaunchForm
from .tools import tools

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'upload')
client_spec = DockerClientSpec(None, do_input_json_envvar=True)
client = DockerClientRunWrapper(client_spec)


def _hostname():
    # 'localhost' will just point to the container, not to the host.
    # The best way of doing this seems to have changed over time.
    # In the future, I hope this will be simplified.
    import docker
    import sys
    client = docker.from_env()
    docker_v = [int(i) for i in client.info()['ServerVersion'].split('.')[:2]]
    # Additions here must also be added to ALLOWED_HOSTS in settings.py.
    # https://docs.docker.com/docker-for-mac/networking/
    if docker_v >= [18, 3]:
        return 'host.docker.internal'
    # https://docs.docker.com/v17.06/docker-for-mac/networking/
    elif docker_v >= [17, 6] and sys.platform == 'darwin':
        return 'docker.for.mac.localhost'
    else:
        raise Exception('Not sure how to determine hostname')


HOSTNAME = _hostname()


def index(request):
    context = {
        'container_names': [container.name for container in client.list()],
        'launch_form': LaunchForm()
    }
    return render(request, 'index.html', context)


def launch(request):
    if request.method == 'POST':
        form = LaunchForm(request.POST)
        if form.is_valid():
            post = form.cleaned_data

            input_url = 'http://{}:{}/upload/{}'.format(
                HOSTNAME, request.get_port(), post['input_file'])
            tool_spec = tools[post['tool']]

            container_name = post['unique_name']
            container_path = '/docker/{}/'.format(container_name)
            container_spec = DockerContainerSpec(
                container_name=container_name,
                image_name=tool_spec['image'],
                input=tool_spec['input'](input_url, container_path))
            client.run(container_spec)
            return HttpResponseRedirect(container_path)


def kill(request, name):
    if request.method == 'POST':
        container = client.list(filters={'name': name})[0]
        container.remove(
            force=True,
            v=True  # Remove volumes associated with the container
        )
        return HttpResponseRedirect('/')


def upload(request, name):
    if not settings.DEBUG:
        raise Exception('Should only be used for local demos')
    if request.method == 'POST':
        # TODO
        pass
    else:
        assert re.match(r'^\w+(\.\w+)*$', name)
        fullpath = os.path.join(UPLOAD_DIR, name)
        if not os.path.isfile(fullpath):
            raise Http404()
        else:
            with open(fullpath) as f:
                return HttpResponse(f.read(), content_type='text/plain')
