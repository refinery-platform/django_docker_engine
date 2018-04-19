import os
import re
from uuid import uuid1

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from django_docker_engine.docker_utils import (
     DockerClientRunWrapper, DockerClientSpec, DockerContainerSpec)

from .forms import LaunchForm

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'upload')


def index(request):
    if request.method == 'POST':
        form = LaunchForm(request.POST)
        if form.is_valid():
            client_spec = DockerClientSpec(None, do_input_json_envvar=True)
            client = DockerClientRunWrapper(client_spec)
            container_name = str(uuid1())
            container_spec = DockerContainerSpec(
                image_name=form.cleaned_data['tool'],
                container_name=container_name)
            client.run(container_spec)
            return HttpResponseRedirect('/docker/{}/'.format(container_name))
    else:
        context = {
            'is_debug': settings.DEBUG,
            'package': __package__,
            'launch_form': LaunchForm()
        }
        return render(request, 'index.html', context)


def upload(request, name):
    assert settings.DEBUG, 'This should only be used for off-line demos'
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
