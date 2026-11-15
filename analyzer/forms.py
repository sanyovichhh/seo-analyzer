from django import forms


class WebsiteAnalysisForm(forms.Form):
    url = forms.URLField(
        label="Website URL",
        max_length=2048,
        widget=forms.URLInput(attrs={
            "class": "form-control",
            "placeholder": "https://example.com"
        })
    )