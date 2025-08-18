from django import forms
from django.core.validators import URLValidator, validate_domain_name

from app.feedback_forms.models import FeedbackForm, PathPattern
from app.projects.models import Project
from app.prompts.models import Prompt, RangedPromptOption

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
        help_texts = {
            "name": "A memorable name for your project",
            "domain": "Enter the full domain you project will target, e.g. https://example.com",
            "retention_period_days": "Data older than this will be periodically deleted",
        }

    def clean_domain(self):
        domain = self.cleaned_data.get("domain")
        validate_domain_name(domain)
        return domain


class FeedbackFormForm(forms.ModelForm):
    class Meta:
        model = FeedbackForm
        fields = [
            "name",
        ]
        widgets = {
            "name": forms.TextInput(attrs={**shared_text_input_attrs}),
        }


class PathPatternForm(forms.ModelForm):
    class Meta:
        model = PathPattern
        fields = [
            "pattern",
            "is_wildcard",
        ]
        widgets = {
            "pattern": forms.TextInput(attrs={**shared_text_input_attrs}),
            "is_wildcard": forms.CheckboxInput(attrs={"class": "tna-checkbox"}),
        }


class PromptForm(forms.ModelForm):
    PROMPT_TYPES = [
        (name, cls.field_label) for name, cls in Prompt.PROMPT_MAP.items()
    ]

    prompt_type = forms.ChoiceField(
        choices=PROMPT_TYPES,
        widget=forms.Select(attrs={"class": "tna-select"}),
        required=True,
        label="Question Type",
    )

    is_disabled = forms.BooleanField(
        required=False,
        initial=False,
        label="Disable this prompt",
        help_text="Disabled prompts won't be shown to users",
        widget=forms.CheckboxInput(attrs={"class": "tna-checkbox"}),
    )

    class Meta:
        model = Prompt
        fields = [
            "text",
        ]
        widgets = {
            "text": forms.TextInput(attrs={**shared_text_input_attrs}),
        }
        help_texts = {"text": "The prompt to display to users"}


class RangedPromptOptionsForm(forms.ModelForm):
    class Meta:
        model = RangedPromptOption
        fields = [
            "label",
            "value",
        ]
        widgets = {
            "label": forms.TextInput(attrs={**shared_text_input_attrs}),
            "value": forms.NumberInput(attrs={"class": "tna-text-input"}),
        }
