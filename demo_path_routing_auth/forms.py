from django import forms

from .tools import tools


class UnvalidatedMultipleChoiceField(forms.MultipleChoiceField):
    # Django wants to know at startup what the possible values are,
    # but the user could upload new files. Just skipping validation is fine.
    def validate(self, value):
        pass


class LaunchForm(forms.Form):
    container_name = forms.CharField()
    tool = forms.ChoiceField(
        widget=forms.Select,
        choices=tuple(
            (name, '{}: {}'.format(name, tool.description))
            for name, tool in tools.items())
    )
    urls = UnvalidatedMultipleChoiceField()
    parameters_json = forms.CharField()
    show_input = forms.BooleanField(required=False)


class UploadForm(forms.Form):
    file = forms.FileField()
