from django.http import HttpResponse
from django.template import loader


def index(request):
    context = {
        'package': __package__,
    }
    template = loader.get_template('index.html')
    return HttpResponse(template.render(context, request))

