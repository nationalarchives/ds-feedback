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
from app.utils.admin import (
    IsDisabledCheckboxForm,
    IsDisabledHiddenCheckboxForm,
    SetDisabledByWhenDisabledAdmin,
    disallow_duplicates,
)

ENABLED_PROMPT_LIMIT = 3

PROMPT_LABELS = {
    TextPrompt.__name__: "Text prompt",
    BinaryPrompt.__name__: "Binary prompt",
    RangedPrompt.__name__: "Ranged prompt",
}


PROMPT_VIEWNAMES: dict[Type[Prompt], str] = {
    TextPrompt: "admin:prompts_textprompt_change",
    BinaryPrompt: "admin:prompts_binaryprompt_change",
    RangedPrompt: "admin:prompts_rangedprompt_change",
}


def get_prompt_viewname(prompt):
    """
    Gets the viewname for a prompt instance
    """
    return PROMPT_VIEWNAMES[type(prompt)]


class TextPromptForm(IsDisabledHiddenCheckboxForm):
    class Meta:
        model = TextPrompt
        fields = "__all__"


class BinaryPromptForm(IsDisabledHiddenCheckboxForm):
    class Meta:
        model = BinaryPrompt
        fields = "__all__"


class RangedPromptForm(IsDisabledHiddenCheckboxForm):
    class Meta:
        model = RangedPrompt
        fields = "__all__"


class TextPromptAdmin(SetDisabledByWhenDisabledAdmin):
    model = TextPrompt
    form = TextPromptForm
    extra = 1
    ordering = ["feedback_form", "order"]
    fields = [
        "uuid",
        "feedback_form",
        "order",
        "is_disabled",
        "disabled",
        "text",
        "max_length",
        "created_by",
    ]
    readonly_fields = [
        "uuid",
        "feedback_form",
        "order",
        "disabled",
        "created_by",
    ]
    list_display = ["text", "feedback_form", "order", "uuid"]
    list_filter = ["feedback_form"]
    search_fields = ["text", "uuid"]

    def disabled(self, instance):
        return "Yes" if instance.disabled_at else "No"

    disabled.short_description = "Disabled"

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        query_set = super().get_queryset(request)
        return query_set.select_related("created_by", "disabled_by")


class BinaryPromptAdmin(SetDisabledByWhenDisabledAdmin):
    model = BinaryPrompt
    form = BinaryPromptForm
    extra = 1
    ordering = ["feedback_form", "order"]
    fields = [
        "uuid",
        "feedback_form",
        "order",
        "is_disabled",
        "disabled",
        "text",
        "positive_answer_label",
        "negative_answer_label",
        "created_by",
    ]
    readonly_fields = [
        "uuid",
        "feedback_form",
        "order",
        "disabled",
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

    def disabled(self, instance):
        return "Yes" if instance.disabled_at else "No"

    disabled.short_description = "Disabled"

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        query_set = super().get_queryset(request)
        return query_set.select_related("created_by", "disabled_by")


class RangedPromptOptionFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        disallow_duplicates(
            self.forms, "value", "This value is used in another option"
        )
        disallow_duplicates(
            self.forms, "label", "This label is used in another option"
        )


class RangedPromptOptionAdmin(admin.TabularInline):
    model = RangedPromptOption
    formset = RangedPromptOptionFormSet
    extra = 1
    ordering = ["value"]
    fields = [
        "label",
        "value",
    ]


class RangedPromptAdmin(SetDisabledByWhenDisabledAdmin):
    model = RangedPrompt
    form = RangedPromptForm
    inlines = [RangedPromptOptionAdmin]
    extra = 1
    ordering = ["feedback_form", "order"]
    fields = [
        "uuid",
        "feedback_form",
        "order",
        "is_disabled",
        "disabled",
        "text",
        "created_by",
    ]
    readonly_fields = [
        "uuid",
        "feedback_form",
        "order",
        "disabled",
        "created_by",
    ]
    list_display = ["text", "options", "feedback_form", "order", "uuid"]
    list_filter = ["feedback_form"]
    search_fields = ["text", "uuid", "options__label"]

    def disabled(self, instance):
        return "Yes" if instance.disabled_at else "No"

    disabled.short_description = "Disabled"

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
            get_prompt_viewname(self.instance),
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
                self.fields["prompt_type"].initial = type(
                    self.instance
                ).__name__
                self.fields["prompt_type"].disabled = True
                self.fields["prompt_type"].required = False


class PromptFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        # Check for enabled prompts exceeding limit
        count = 0
        for form in self.forms:
            instance: TextPrompt = form.instance

            if not instance.disabled_at:
                if instance.text:
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
