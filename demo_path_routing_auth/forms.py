from django import forms

from .tools import tools
import os

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'upload')


class UnvalidatedMultipleChoiceField(forms.MultipleChoiceField):
    # Django wants to know at startup what the possible values are,
    # but the user could upload new files. Skipping validation is
    # easier than actually doing it the right way.
    def validate(self, value):
        pass


class LaunchForm(forms.Form):
    container_name = forms.CharField()
    data = UnvalidatedMultipleChoiceField()
    tool = forms.ChoiceField(
        widget=forms.Select,
        choices=tuple((k, k) for k in tools)
    )
    show_input = forms.BooleanField(required=False)


class UploadForm(forms.Form):
    file = forms.FileField()
