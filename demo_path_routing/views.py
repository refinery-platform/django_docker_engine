from django.http import HttpResponse
from django.template import loader
from django.http import HttpResponseRedirect
from django.shortcuts import render

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


