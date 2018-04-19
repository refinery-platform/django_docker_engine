import os

from django import forms

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'upload')


class LaunchForm(forms.Form):
    unique_name = forms.CharField()

    tool = forms.ChoiceField(
        widget=forms.Select,
        choices=(
            ('scottx611x/refinery-developer-vis-tool:v0.0.7', 'debugger'),
            ('mccalluc/heatmap_scatter_dash:v0.1.8', 'heatmap'),
            ('mccalluc/lineup_refinery:v0.0.8', 'tabular')
        )
    )

    input = forms.ChoiceField(
        widget=forms.Select,
        choices=((f, f) for f in os.listdir(UPLOAD_DIR))
    )
