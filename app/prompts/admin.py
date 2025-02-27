from typing import Type

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet
from django.urls import reverse
from django.utils.safestring import mark_safe

from app.prompts.models import (
    BinaryPrompt,
    Prompt,
    RangedPrompt,
    RangedPromptOption,
    TextPrompt,
)
from app.utils.admin import IsDisabledCheckboxForm, disallow_duplicates

ENABLED_PROMPT_LIMIT = 3

PROMPT_TYPES: dict[str, Type[Prompt]] = {
    "TextPrompt": TextPrompt,
    "BinaryPrompt": BinaryPrompt,
    "RangedPrompt": RangedPrompt,
}

PROMPT_TYPE_NAMES = {value: key for key, value in PROMPT_TYPES.items()}

PROMPT_VIEWNAMES = {
    TextPrompt: "admin:prompts_textprompt_change",
    BinaryPrompt: "admin:prompts_binaryprompt_change",
    RangedPrompt: "admin:prompts_rangedprompt_change",
}

PROMPT_LABELS = {
    "TextPrompt": "Text prompt",
    "BinaryPrompt": "Binary prompt",
    "RangedPrompt": "Ranged prompt",
}


class TextPromptForm(IsDisabledCheckboxForm):
    class Meta:
        model = TextPrompt
        fields = "__all__"


class BinaryPromptForm(IsDisabledCheckboxForm):
    class Meta:
        model = BinaryPrompt
        fields = "__all__"


class RangedPromptForm(IsDisabledCheckboxForm):
    class Meta:
        model = RangedPrompt
        fields = "__all__"


class TextPromptAdmin(admin.ModelAdmin):
    model = TextPrompt
    form = TextPromptForm
    extra = 1
    ordering = ["feedback_form", "order"]
    fields = [
        "uuid",
        "feedback_form",
        "order",
        "text",
        "max_length",
        "created_by",
    ]
    readonly_fields = [
        "uuid",
        "feedback_form",
        "order",
        "created_by",
    ]
    list_display = ["text", "feedback_form", "order", "uuid"]
    list_filter = ["feedback_form"]
    search_fields = ["text", "uuid"]

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        query_set = super().get_queryset(request)
        return query_set.select_related("created_by", "disabled_by")


class BinaryPromptAdmin(admin.ModelAdmin):
    model = BinaryPrompt
    form = BinaryPromptForm
    extra = 1
    ordering = ["feedback_form", "order"]
    fields = [
        "uuid",
        "feedback_form",
        "order",
        "text",
        "positive_answer_label",
        "negative_answer_label",
        "created_by",
    ]
    readonly_fields = [
        "uuid",
        "feedback_form",
        "order",
        "created_by",
    ]
    list_display = [
        "text",
        "positive_answer_label",
        "negative_answer_label",
        "feedback_form",
        "order",
        "uuid",
    ]
    list_filter = ["feedback_form"]
    search_fields = [
        "text",
        "positive_answer_label",
        "negative_answer_label",
        "uuid",
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        query_set = super().get_queryset(request)
        return query_set.select_related("created_by", "disabled_by")


class RangedPromptOptionFormSet(BaseInlineFormSet):
    def clean(self):
        cleaned_data = super().clean()

        disallow_duplicates(
            self.forms, "value", "This value is used in another option"
        )
        disallow_duplicates(
            self.forms, "label", "This label is used in another option"
        )

        return cleaned_data


class RangedPromptOptionAdmin(admin.TabularInline):
    model = RangedPromptOption
    formset = RangedPromptOptionFormSet
    extra = 1
    ordering = ["value"]
    fields = [
        "label",
        "value",
    ]


class RangedPromptAdmin(admin.ModelAdmin):
    model = RangedPrompt
    form = RangedPromptForm
    inlines = [RangedPromptOptionAdmin]
    extra = 1
    ordering = ["feedback_form", "order"]
    fields = [
        "uuid",
        "feedback_form",
        "order",
        "text",
        "created_by",
    ]
    readonly_fields = [
        "uuid",
        "feedback_form",
        "order",
        "created_by",
    ]
    list_display = ["text", "options", "feedback_form", "order", "uuid"]
    list_filter = ["feedback_form"]
    search_fields = ["text", "uuid", "options__label"]

    def has_add_permission(self, request, obj=None):
        return False

    def options(self, obj):
        return ", ".join(
            option.label for option in obj.options.all().order_by("value")
        )

    options.short_description = "Path patterns"

    def get_queryset(self, request):
        query_set = super().get_queryset(request)
        # Prefetch only changelist page
        id = request.resolver_match.kwargs.get("object_id")
        if not id:
            query_set = query_set.prefetch_related("options")

        return query_set.select_related("created_by", "disabled_by")


admin.site.register(TextPrompt, TextPromptAdmin)
admin.site.register(BinaryPrompt, BinaryPromptAdmin)
admin.site.register(RangedPrompt, RangedPromptAdmin)


class PromptDetailsWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        # self.instance is added by PromptForm
        if not self.instance.id:
            return ""

        url = reverse(
            PROMPT_VIEWNAMES[type(self.instance)],
            kwargs={"object_id": self.instance.id},
        )
        return mark_safe(f'<a href="{url}">Edit details</a>')


class PromptForm(IsDisabledCheckboxForm):
    prompt_details = forms.CharField(
        widget=PromptDetailsWidget(),
        label="prompt details",
        required=False,
    )
    prompt_type = forms.ChoiceField(
        choices=[
            ("", "Please select..."),
            *PROMPT_LABELS.items(),
        ]
    )

    class Meta:
        model = Prompt
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            # Pass instance to widget to display link to specific Prompt
            self.fields["prompt_details"].widget.instance = self.instance

            # For existing prompts set prompt type
            if self.instance.pk:
                self.fields["prompt_type"].initial = PROMPT_TYPE_NAMES[
                    type(self.instance)
                ]
                self.fields["prompt_type"].disabled = True
                self.fields["prompt_type"].required = False


class PromptFormSet(BaseInlineFormSet):
    def clean(self):
        cleaned_data = super().clean()

        # Check for enabled prompts exceeding limit
        count = 0
        for form in self.forms:
            instance: TextPrompt = form.instance

            if instance.text and not instance.disabled_at:
                count += 1

            if count > ENABLED_PROMPT_LIMIT and instance.order is not None:
                form.add_error(
                    "text",
                    ValidationError(
                        f"You cannot have more than {ENABLED_PROMPT_LIMIT} enabled prompts"
                    ),
                )

        disallow_duplicates(
            self.forms, "order", "This order number is used in another prompt"
        )

        return cleaned_data


class PromptAdmin(admin.TabularInline):
    model = Prompt
    form = PromptForm
    formset = PromptFormSet
    extra = 1
    ordering = ["order"]
    fields = [
        "text",
        "prompt_type",
        "prompt_details",
        "order",
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
        return query_set.select_subclasses(
            BinaryPrompt, RangedPrompt, TextPrompt
        ).select_related("created_by", "disabled_by")
