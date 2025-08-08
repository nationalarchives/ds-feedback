from django import forms
from django.core.validators import validate_domain_name

from app.projects.models import Project

shared_text_input_attrs = {
    "class": "tna-text-input",
    "type": "text",
    "spellcheck": "false",
    "autocapitalize": "off",
    "autocorrect": "off",
}


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "domain",
            "retention_period_days",
        ]
        widgets = {
            "name": forms.TextInput(attrs={**shared_text_input_attrs}),
            "domain": forms.URLInput(attrs={**shared_text_input_attrs}),
            "retention_period_days": forms.Select(
                attrs={"class": "tna-select"}
            ),
        }

    def clean_domain(self):
        domain = self.cleaned_data.get("domain")
        validate_domain_name(domain)
        return domain
