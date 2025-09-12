from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator

from app.editor_ui.validators import validate_path_pattern
from app.feedback_forms.models import FeedbackForm, PathPattern
from app.projects.models import Project, ProjectMembership
from app.prompts.models import (
    BinaryPrompt,
    Prompt,
    RangedPrompt,
    RangedPromptOption,
    TextPrompt,
)

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
            "name": forms.TextInput(),
            "domain": forms.URLInput(),
            "retention_period_days": forms.Select(),
        }
        validators = {
            "domain": [URLValidator()],
        }
        help_texts = {
            "name": "Enter a memorable name for your project",
            "domain": "Enter the full URL this project will target (for example, https://www.nationalarchives.gov.uk/)",
            "retention_period_days": "Select a retention period for feedback responses. Responses in your project will be deleted when they reach this age.",
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
            "retention_period_days",
        ]
        widgets = {
            "name": forms.TextInput(),
            "domain": forms.URLInput(),
            "retention_period_days": forms.Select(),
        }
        help_texts = {
            "name": "Enter a memorable name for your project",
            "domain": "Enter the full URL this project will target (for example, https://www.nationalarchives.gov.uk/)",
            "retention_period_days": "Select a retention period for feedback responses. Responses in your project will be deleted when they reach this age.",
        }

    def clean_domain(self):
        domain = self.cleaned_data.get("domain")
        url_validator(domain)
        return domain


class FeedbackFormForm(forms.ModelForm):
    is_published = forms.BooleanField(
        required=False,
        initial=True,
        label="Publish this feedback form",
        help_text="Check this box to publish the feedback form. Published forms will be visible externally via the API",
        widget=forms.CheckboxInput(attrs={"text": "Publish"}),
    )

    class Meta:
        model = FeedbackForm
        fields = [
            "name",
            "is_published",
        ]
        widgets = {
            "name": forms.TextInput(),
        }
        help_texts = {
            "name": "Enter a memorable name for this feedback form",
        }


class PathPatternForm(forms.ModelForm):
    pattern_with_wildcard = forms.CharField(
        widget=forms.TextInput(),
        label="Path pattern",
        help_text="Enter a path pattern",
    )

    class Meta:
        model = PathPattern
        fields = [
            "pattern_with_wildcard",
        ]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        if instance:
            initial = kwargs.get("initial", {})
            initial["pattern_with_wildcard"] = instance.pattern_with_wildcard
            kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def clean_pattern_with_wildcard(self):
        pattern = self.cleaned_data.get("pattern_with_wildcard")
        validate_path_pattern(pattern)

        return pattern


class PromptForm(forms.ModelForm):
    PROMPT_TYPES = [
        (name, cls.field_label) for name, cls in Prompt.PROMPT_MAP.items()
    ]

    prompt_type = forms.ChoiceField(
        choices=PROMPT_TYPES,
        widget=forms.Select(),
        required=True,
        label="Question Type",
        help_text="Select the type of question you want to create",
    )

    is_published = forms.BooleanField(
        required=False,
        initial=True,
        label="Publish this prompt",
        help_text="Published prompts will be available externally for published feedback forms",
        widget=forms.CheckboxInput(attrs={"text": "Publish"}),
    )

    class Meta:
        model = Prompt
        fields = [
            "text",
        ]
        labels = {
            "text": "Question text",
        }
        widgets = {
            "text": forms.TextInput(),
        }
        help_texts = {"text": "Enter the question text to display to users"}


class PromptUpdateForm(forms.ModelForm):
    def __init_subclass__(cls, **kwargs):
        """Automatically register subclasses in the PROMPT_MAP."""
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "Meta") and hasattr(cls.Meta, "model"):
            PROMPT_FORM_MAP[cls.Meta.model] = cls

    is_published = forms.BooleanField(
        required=False,
        initial=True,
        label="Publish this prompt",
        help_text="Published prompts will be available externally for published feedback forms",
        widget=forms.CheckboxInput(attrs={"text": "Publish"}),
    )

    class Meta:
        model = Prompt
        fields = [
            "text",
            "order",
            "is_published",
        ]
        labels = {
            "text": "Question text",
            "order": "Question order",
        }
        widgets = {
            "text": forms.TextInput(),
            "order": forms.NumberInput(attrs={"class": "tna-text-input"}),
        }
        help_texts = {
            "text": "Enter the question text to display to users",
            "order": "Enter the order in which this question will appear in the feedback form",
        }


class TextPromptUpdateForm(PromptUpdateForm):
    class Meta:
        model = TextPrompt
        fields = [
            "text",
            "order",
            "max_length",
            "is_published",
        ]
        labels = {
            **PromptUpdateForm.Meta.labels,
            "max_length": "Maximum length of the response",
        }
        widgets = {
            **PromptUpdateForm.Meta.widgets,
            "max_length": forms.NumberInput(attrs={"class": "tna-text-input"}),
        }
        help_texts = {
            **PromptUpdateForm.Meta.help_texts,
            "max_length": "Enter the maximum number of characters allowed in answer",
        }


class BinaryPromptUpdateForm(PromptUpdateForm):
    class Meta:
        model = BinaryPrompt
        fields = [
            "text",
            "order",
            "positive_answer_label",
            "negative_answer_label",
            "is_published",
        ]
        labels = {
            **PromptUpdateForm.Meta.labels,
            "positive_answer_label": "Positive answer text",
            "negative_answer_label": "Negative answer text",
        }
        widgets = {
            **PromptUpdateForm.Meta.widgets,
            "positive_answer_label": forms.TextInput(),
            "negative_answer_label": forms.TextInput(),
        }
        help_texts = {
            **PromptUpdateForm.Meta.help_texts,
            "positive_answer_label": "Enter the display text for the positive answer option",
            "negative_answer_label": "Enter the display text for the negative answer option",
        }


class RangedPromptOptionForm(forms.ModelForm):
    class Meta:
        model = RangedPromptOption
        fields = [
            "label",
            "value",
        ]
        labels = {
            "label": "Option label",
            "value": "Option value",
        }
        widgets = {
            "label": forms.TextInput(),
            "value": forms.NumberInput(attrs={"class": "tna-text-input"}),
        }
        help_texts = {
            "label": "Enter the display text for this option",
            "value": "Enter the numeric value for this option",
        }


class RangedPromptUpdateForm(PromptUpdateForm):
    class Meta:
        model = RangedPrompt
        fields = [
            "text",
            "order",
            "is_published",
        ]
        labels = {
            **PromptUpdateForm.Meta.labels,
        }
        widgets = {
            **PromptUpdateForm.Meta.widgets,
        }
        help_texts = {
            **PromptUpdateForm.Meta.help_texts,
        }


class ProjectMembershipCreateForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(),
        label="User Email",
        help_text="Enter the email address of the user you want to add to the project.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields(["email", "role"])

    def clean_email(self):
        email = self.cleaned_data.get("email")

        try:
            user = get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            raise forms.ValidationError(
                "No user account found for this email address."
            )

        self.cleaned_data["user_obj"] = user
        return email

    class Meta:
        model = ProjectMembership
        fields = [
            "email",
            "role",
        ]
        widgets = {
            "email": forms.TextInput(),
            "role": forms.Select(),
        }
        help_texts = {"role": "Select the role you want to assign to the user."}


class ProjectMembershipUpdateForm(forms.ModelForm):
    class Meta:
        model = ProjectMembership
        fields = [
            "role",
        ]
        widgets = {
            "role": forms.Select(),
        }
        help_texts = {"role": "Select the role you want to assign to the user."}
