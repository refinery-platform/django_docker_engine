from django import forms

class LaunchForm(forms.Form):
    tool = forms.ChoiceField(
        widget=forms.Select,
        choices=(
            ('scottx611x/refinery-developer-vis-tool:v0.0.7', 'debugger'),
            ('mccalluc/heatmap_scatter_dash:v0.1.8', 'heatmap'),
            ('mccalluc/lineup_refinery:v0.0.8', 'tabular')
        ))
