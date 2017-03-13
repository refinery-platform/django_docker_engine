from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello, world. You're at the docker index.")

def detail(request, image_id):
    return HttpResponse("You're looking at model %s." % image_id)