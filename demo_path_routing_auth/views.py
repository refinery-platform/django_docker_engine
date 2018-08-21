import json
import os
import re
from sys import version_info

from django import forms
from django.contrib import auth
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.http import require_POST

from django_docker_engine.docker_utils import (DockerClientRunWrapper,
                                               DockerClientSpec,
                                               DockerContainerSpec)

from .forms import LaunchForm, UploadForm
from .tools import tools
from .utils import hostname

if version_info >= (3,):
    from urllib.parse import urlparse
else:
    from urlparse import urlparse


client = DockerClientRunWrapper(
    DockerClientSpec(None, do_input_json_envvar=True))
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'upload')

OUTSIDE_URLS = [
    'https://s3.amazonaws.com/pkerp/public/gene_annotations.short.db',
    'https://s3.amazonaws.com/pkerp/public/cnv_short.hibed',
    'https://beta.stemcellcommons.org'
    '/media/file_store/22/e3/raw_data_qualimapReport.zip',
    'https://rawgit.com/igvteam/igv/master/test/data/gff/NC_009084.gff'
]


def index(request):
    launch_form = LaunchForm()
    # TODO: Pass this info through the constructor
    try:
        port = request.get_port()
    except AttributeError:  # Django 1.8.19
        port = request.get_host().replace('localhost:', '')
    url_field_choices = (
        [('http://{}:{}/upload/{}'.format(hostname(), port, name), name)
         for name in os.listdir(UPLOAD_DIR) if not name.startswith('.')] +
        [(url, os.path.basename(urlparse(url).path)) for url in OUTSIDE_URLS]
    )
    name_to_url = {
        name: url for (url, name) in url_field_choices
    }
    launch_form.fields['urls'] = forms.ChoiceField(
        widget=forms.SelectMultiple,
        choices=url_field_choices
    )
    launch_form.initial['urls'] = [
        name_to_url.get(request.GET.get('uploaded'))]

    context = {
        'container_names': [container.name for container in client.list()],
        'launch_form': launch_form,
        'upload_form': UploadForm(),
        'default_parameters_json': json.dumps({
            k: v['default_parameters']
            for k, v in tools.items()
        }),
        'default_urls_json': json.dumps({
            k: [name_to_url[f] for f in v['default_files']]
            for k, v in tools.items()
        })
    }
    if hasattr(request, 'user'):
        context['user'] = request.user
        # TODO: Why is this needed?
        # Template worked without it, but user login status was wrong.
    return render(request, 'index.html', context)


@require_POST
def login(request):
    user = auth.authenticate(username='fake-username',
                             password='fake-password')
    if user is not None:
        auth.login(request, user)
        return HttpResponseRedirect('/')


@require_POST
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/')


@require_POST
def launch(request):
    form = LaunchForm(request.POST)
    if not form.is_valid():
        raise ValidationError(form.errors)

    post = form.cleaned_data
    input_urls = post['urls']
    tool_spec = tools[post['tool']]

    container_name = post['container_name']
    container_path = '/docker/{}/'.format(container_name)
    input_data = tool_spec['input'](input_urls, container_path)
    input_data['parameters'] = json.loads(post['parameters_json'])

    if post.get('show_input'):
        return HttpResponse(json.dumps(input_data), content_type='application/json')

    container_spec = DockerContainerSpec(
        container_name=container_name,
        image_name=tool_spec['image'],
        input=input_data,
        extra_directories=input_data.get('extra_directories') or [],
        container_port=input_data.get('container_port') or 80,
    )
    client.run(container_spec)
    return HttpResponseRedirect(container_path)


@require_POST
def kill(request, name):
    container = client.list(filters={'name': name})[0]
    client.kill(container)
    return HttpResponseRedirect('/')


def upload(request, name):
    valid_re = r'^[a-zA-Z0-9_.-]+$'

    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if not form.is_valid():
            raise ValidationError(form.errors)
        file = request.FILES['file']
        assert re.match(valid_re, file.name),\
            'Name must match {}'.format(valid_re)
        fullpath = os.path.join(UPLOAD_DIR, file.name)
        with open(fullpath, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        return HttpResponseRedirect('/?uploaded={}'.format(file.name))

    else:
        assert re.match(valid_re, name)
        fullpath = os.path.join(UPLOAD_DIR, name)
        if not os.path.isfile(fullpath):
            raise Http404()
        else:
            with open(fullpath, 'rb') as f:
                return HttpResponse(f.read(), content_type='text/plain')
