from django import forms

from .tools import tools


class LaunchForm(forms.Form):
    container_name = forms.CharField()
    data = forms.CharField()  # Needs to be in definition to be readable.
    tool = forms.ChoiceField(
        widget=forms.Select,
        choices=tuple((k, k) for k in tools)
    )
    show_input = forms.BooleanField(required=False)


class UploadForm(forms.Form):
    file = forms.FileField()
