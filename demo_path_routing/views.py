import re
import os

from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.conf import settings

from .forms import LaunchForm


def index(request):
    if request.method == 'POST':
        form = LaunchForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect('/docker/container-id-goes-here/')
    else:
        context = {
            'package': __package__,
            'launch_form': LaunchForm()
        }
        return render(request, 'index.html', context)

def upload(request, name):
    assert settings.DEBUG, 'This should only be used for off-line demos'
    if request.method == 'POST':
        pass
    else:
        assert re.match(r'^\w+(\.\w+)*$', name)
        fullpath = os.path.join(os.path.dirname(__file__), 'upload', name)
        if not os.path.isfile(fullpath):
            raise Http404()
        else:
            with open(fullpath) as f:
                return HttpResponse(f.read(), content_type='text/plain')



