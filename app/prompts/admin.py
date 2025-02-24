from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet
from django.utils import timezone

from app.prompts.models import TextPrompt

ENABLED_PROMPT_LIMIT = 3


class TextPromptForm(forms.ModelForm):
    is_disabled = forms.BooleanField(
        label="Disabled", required=False, initial=False
    )

    class Meta:
        model = TextPrompt
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.disabled_at:
            self.fields["is_disabled"].initial = True

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data["is_disabled"] and not self.instance.disabled_at:
            self.instance.disabled_at = timezone.now()
        if not self.cleaned_data["is_disabled"]:
            self.instance.disabled_at = None

        return cleaned_data


class TextPromptFormSet(BaseInlineFormSet):

    def clean(self):
        cleaned_data = super().clean()

        # Check for enabled prompts exceeding limit
        count = 0
        for form in self.forms:
            instance: TextPrompt = form.instance

            if not instance.disabled_at:
                count += 1

            if count > ENABLED_PROMPT_LIMIT and instance.order is not None:
                form.add_error(
                    "text",
                    ValidationError(
                        f"You cannot have more than {ENABLED_PROMPT_LIMIT} enabled prompts"
                    ),
                )

        # Check for duplicate order numbers in enabled prompts
        orders = set()
        for form in self.forms:
            if form.cleaned_data and "order" in form.cleaned_data:
                instance: TextPrompt = form.instance

                if instance.order in orders:
                    form.add_error(
                        "order",
                        ValidationError(
                            "This order number is used in another prompt"
                        ),
                    )

                orders.add(instance.order)

        return cleaned_data


class TextPromptAdmin(admin.TabularInline):
    model = TextPrompt
    form = TextPromptForm
    formset = TextPromptFormSet
    extra = 1
    ordering = ["order"]
    fields = [
        "text",
        "feedback_form",
        "order",
        "max_length",
        "is_disabled",
        "disabled_by",
        "created_by",
    ]
    readonly_fields = [
        "disabled_by",
        "created_by",
    ]
    list_display = ["text", "feedback_form", "order"]
    list_filter = ["feedback_form"]
    search_fields = ["text", "uuid"]

    def get_queryset(self, request):
        query_set = super().get_queryset(request)
        return query_set.select_related("created_by", "disabled_by")
