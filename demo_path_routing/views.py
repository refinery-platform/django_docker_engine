import os
import re

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from django_docker_engine.docker_utils import (
    DockerClientRunWrapper, DockerClientSpec, DockerContainerSpec)

from .forms import LaunchForm

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'upload')
client_spec = DockerClientSpec(None, do_input_json_envvar=True)
client = DockerClientRunWrapper(client_spec)


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
            container_name = form.cleaned_data['unique_name']
            container_spec = DockerContainerSpec(
                image_name=form.cleaned_data['tool'],
                container_name=container_name)
            client.run(container_spec)
            return HttpResponseRedirect('/docker/{}/'.format(container_name))


def kill(request, name):
    if request.method == 'POST':
        container = client.list(filters={'name': name})[0]
        container.remove(
            force=True,
            v=True  # Remove volumes associated with the container
        )
        return HttpResponseRedirect('/')


def upload(request, name):
    assert request.get_host() in ['localhost', '127.0.0.1'], \
        'This should only be used for demos on localhost.'
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
