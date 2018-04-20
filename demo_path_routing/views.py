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
from .utils import hostname

client = DockerClientRunWrapper(
    DockerClientSpec(None, do_input_json_envvar=True))


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
                hostname(), request.get_port(), post['input_file'])
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
        upload_dir = os.path.join(os.path.dirname(__file__), 'upload')
        fullpath = os.path.join(upload_dir, name)
        if not os.path.isfile(fullpath):
            raise Http404()
        else:
            with open(fullpath) as f:
                return HttpResponse(f.read(), content_type='text/plain')
