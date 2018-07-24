from django import forms

from .tools import tools


class UnvalidatedMultipleChoiceField(forms.MultipleChoiceField):
    # Django wants to know at startup what the possible values are,
    # but the user could upload new files. Just skipping validation is fine.
    def validate(self, value):
        pass


class LaunchForm(forms.Form):
    container_name = forms.CharField()
    files = UnvalidatedMultipleChoiceField()
    tool = forms.ChoiceField(
        widget=forms.Select,
        choices=tuple((k, k) for k in tools)
    )
    show_input = forms.BooleanField(required=False)


class UploadForm(forms.Form):
    file = forms.FileField()
