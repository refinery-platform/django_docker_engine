import os

from django import forms

from .tools import tools

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'upload')


class LaunchForm(forms.Form):
    container_name = forms.CharField()
    tool = forms.ChoiceField(
        widget=forms.Select,
        choices=tuple((k, k) for k in tools)
    )


class UploadForm(forms.Form):
    file = forms.FileField()
