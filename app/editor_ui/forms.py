from email import message

from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator

from app.api.models import ProjectAPIAccess
from app.api.types import APIAccessLifespan, APIRole
from app.feedback_forms.models import FeedbackForm, PathPattern
from app.projects.models import Project, ProjectMembership
from app.prompts.models import (
    BinaryPrompt,
    Prompt,
    RangedPrompt,
    RangedPromptOption,
    TextPrompt,
)

shared_text_input_attrs = {
    "class": "tna-text-input",
    "type": "text",
    "spellcheck": "false",
    "autocapitalize": "off",
    "autocorrect": "off",
}

url_validator = URLValidator(
    schemes=["https"],
    message="Please enter a valid URL starting with https://",
)

PROMPT_FORM_MAP = {}


class ProjectCreateForm(forms.ModelForm):
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
        validators = {
            "domain": [URLValidator()],
        }
        help_texts = {
            "name": "A memorable name for your project",
            "domain": "Enter the full URL this project will target, e.g. https://example.com",
            "retention_period_days": "Data older than this will be periodically deleted",
        }

    def clean_domain(self):
        domain = self.cleaned_data.get("domain")
        url_validator(domain)
        return domain


class ProjectUpdateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "domain",
        ]
        widgets = {
            "name": forms.TextInput(attrs={**shared_text_input_attrs}),
            "domain": forms.URLInput(attrs={**shared_text_input_attrs}),
        }
        help_texts = {
            "name": "A memorable name for your project",
            "domain": "The full URL this project will target, e.g. https://example.com",
        }

    def clean_domain(self):
        domain = self.cleaned_data.get("domain")
        url_validator(domain)
        return domain


class FeedbackFormForm(forms.ModelForm):
    is_disabled = forms.BooleanField(
        required=False,
        initial=False,
        label="Disable this feedback form",
        help_text="Disabled feedback forms won't be shown to users",
        widget=forms.CheckboxInput(attrs={"class": "tna-checkbox"}),
    )

    class Meta:
        model = FeedbackForm
        fields = [
            "name",
            "is_disabled",
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


class PromptUpdateForm(forms.ModelForm):
    def __init_subclass__(cls, **kwargs):
        """Automatically register subclasses in the PROMPT_MAP."""
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "Meta") and hasattr(cls.Meta, "model"):
            PROMPT_FORM_MAP[cls.Meta.model] = cls

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
            "order",
            "is_disabled",
        ]
        widgets = {
            "text": forms.TextInput(attrs={**shared_text_input_attrs}),
            "order": forms.NumberInput(attrs={"class": "tna-text-input"}),
        }
        help_texts = {
            "text": "The prompt to display to users",
            "order": "The order in which this prompt appears",
        }


class TextPromptUpdateForm(PromptUpdateForm):
    class Meta:
        model = TextPrompt
        fields = [
            "text",
            "order",
            "max_length",
            "is_disabled",
        ]
        widgets = {
            **PromptUpdateForm.Meta.widgets,
            "max_length": forms.NumberInput(attrs={"class": "tna-text-input"}),
        }
        help_texts = {
            **PromptUpdateForm.Meta.help_texts,
            "max_length": "The maximum length of the response",
        }


class BinaryPromptUpdateForm(PromptUpdateForm):
    class Meta:
        model = BinaryPrompt
        fields = [
            "text",
            "order",
            "positive_answer_label",
            "negative_answer_label",
            "is_disabled",
        ]
        widgets = {
            **PromptUpdateForm.Meta.widgets,
            "positive_answer_label": forms.TextInput(
                attrs={**shared_text_input_attrs}
            ),
            "negative_answer_label": forms.TextInput(
                attrs={**shared_text_input_attrs}
            ),
        }
        help_texts = {
            **PromptUpdateForm.Meta.widgets,
            "positive_answer_label": "The label for the positive answer option",
            "negative_answer_label": "The label for the negative answer option",
        }


class RangedPromptOptionForm(forms.ModelForm):
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


class RangedPromptUpdateForm(PromptUpdateForm):
    class Meta:
        model = RangedPrompt
        fields = [
            "text",
            "order",
            "is_disabled",
        ]
        widgets = {
            **PromptUpdateForm.Meta.widgets,
        }
        help_texts = {
            **PromptUpdateForm.Meta.help_texts,
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
        widgets = {
            "email": forms.TextInput(attrs={**shared_text_input_attrs}),
            "role": forms.Select(attrs={"class": "tna-select"}),
        }
        help_texts = {"role": "Select the role you want to assign to the user."}


class ProjectMembershipUpdateForm(forms.ModelForm):
    class Meta:
        model = ProjectMembership
        fields = [
            "role",
        ]
        widgets = {
            "role": forms.Select(attrs={"class": "tna-select"}),
        }
        help_texts = {"role": "Select the role you want to assign to the user."}


class ProjectAPIAccessCreateForm(forms.ModelForm):
    grantee_email = forms.EmailField(
        widget=forms.EmailInput(attrs={**shared_text_input_attrs}),
        label="User Email",
        help_text="Enter the email address of the user to grant API access to.",
        required=False,
    )

    lifespan_days = forms.ChoiceField(
        choices=APIAccessLifespan.choices,
        widget=forms.Select(attrs={"class": "tna-select"}),
        label="Access Duration",
        help_text="How long the API access should remain active.",
    )

    def __init__(self, *args, user=None, project=None, **kwargs):
        self.user = user
        self.project = project
        self.has_owner_access = False
        super().__init__(*args, **kwargs)

        project_owner_ids = [
            membership.user.id
            for membership in ProjectMembership.objects.select_related(
                "user"
            ).filter(project=project, role="owner")
        ]

        if user and (user.is_superuser or user.id in project_owner_ids):
            self.has_owner_access = True
        else:
            # Only super-users and project owners can grant access to other users.
            # Grantee Email is hidden for other users.
            del self.fields["grantee_email"]

    def clean_grantee_email(self):
        grantee_email = self.cleaned_data.get("grantee_email")

        if not grantee_email:
            return grantee_email

        try:
            user = get_user_model().objects.get(email=grantee_email)

            # Check if user has access to the project
            if not self.project.members.filter(id=user.id).exists():
                raise forms.ValidationError(
                    "User must be a member of this project to receive API access."
                )

        except get_user_model().DoesNotExist:
            raise forms.ValidationError("User not found.")

        self.cleaned_data["grantee_user"] = user
        return grantee_email

    def clean(self):
        cleaned_data = super().clean()

        if not self.has_owner_access:
            cleaned_data["grantee_user"] = self.user

        return cleaned_data

    class Meta:
        model = ProjectAPIAccess
        fields = [
            "grantee_email",
            "lifespan_days",
        ]
