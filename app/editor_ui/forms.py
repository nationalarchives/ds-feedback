from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import validate_domain_name

from app.feedback_forms.models import FeedbackForm, PathPattern
from app.projects.models import Project, ProjectMembership
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


class ProjectMembershipCreateForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={**shared_text_input_attrs}),
        label="User Email",
        help_text="Enter the email address of the user you want to assign the permission.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(["email", "role"])

    def clean_email(self):
        email = self.cleaned_data.get("email")

        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            raise forms.ValidationError("User not found.")

        self.cleaned_data["user_obj"] = user
        return email

    class Meta:
        model = ProjectMembership
        fields = [
            "email",
            "role",
        ]

        help_texts = {"role": "Select the role you want to assign to the user."}
