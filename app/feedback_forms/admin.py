from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet
from django.urls import reverse
from django.utils.html import format_html

from app.feedback_forms.models import FeedbackForm, PathPattern
from app.prompts.models import Prompt, TextPrompt
from app.utils.admin import (
    HideReadOnlyOnCreationAdmin,
    IsDisabledCheckboxForm,
    SetCreatedByOnCreationAdmin,
    SetDisabledByWhenDisabledAdmin,
    disallow_duplicates,
)

ENABLED_PROMPT_LIMIT = 3

PROMPT_LABELS = {
    TextPrompt.__name__: "Text prompt",
    BinaryPrompt.__name__: "Binary prompt",
    RangedPrompt.__name__: "Ranged prompt",
}


class FeedbackFormForm(IsDisabledCheckboxForm):
    class Meta:
        model = FeedbackForm
        fields = "__all__"


class PathPatternFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        # Propagate project from FeedbackForm to PathPattern
        for form in self.forms:
            if "feedback_form" in form.cleaned_data:
                feedback_form = form.cleaned_data["feedback_form"]
                form.instance.project_id = feedback_form.project_id
                # Run validation again to check project/pattern uniqueness
                form.full_clean()

        disallow_duplicates(
            self.forms,
            "pattern",
            "You cannot use the same pattern twice in a project.",
        )


class PathPatternInline(admin.TabularInline):
    formset = PathPatternFormSet
    model = PathPattern
    extra = 1
    ordering = ["pattern"]
    fields = [
        "pattern",
        "created_by",
    ]
    readonly_fields = [
        "created_by",
    ]

    def get_queryset(self, request):
        query_set = super().get_queryset(request)
        return query_set.select_related("created_by")


class PromptDetailsWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        # self.instance is added by PromptForm
        if not self.instance.id:
            return ""

        url = reverse(
            self.instance.get_viewname(),
            kwargs={"object_id": self.instance.id},
        )
        return format_html('<a href="{url}">Edit details</a>', url=url)


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
                self.fields["prompt_type"].initial = (
                    self.instance._meta.model_name
                )
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
        return query_set.select_subclasses().select_related(
            "created_by", "disabled_by"
        )


class FeedbackFormAdmin(
    HideReadOnlyOnCreationAdmin,
    SetCreatedByOnCreationAdmin,
    SetDisabledByWhenDisabledAdmin,
):
    form = FeedbackFormForm
    inlines = [PathPatternInline, PromptAdmin]
    ordering = ["name"]
    fields = [
        "uuid",
        "name",
        "project",
        "is_disabled",
        "disabled_by",
        "created_by",
    ]
    readonly_fields = [
        "uuid",
        "disabled_by",
        "created_by",
    ]
    list_display = ["name", "project", "patterns", "prompt_count", "uuid"]
    list_filter = ["project"]
    search_fields = ["name", "uuid", "path_patterns__pattern"]

    def patterns(self, obj):
        return ", ".join(pattern.pattern for pattern in obj.path_patterns.all())

    patterns.short_description = "Path patterns"

    def prompt_count(self, obj):
        return obj.prompts.count()

    prompt_count.short_description = "Number of prompts"

    def get_queryset(self, request):
        is_list_page = not request.resolver_match.kwargs.get("object_id")
        query_set = super().get_queryset(request)
        query_set = query_set.select_related(
            "created_by", "disabled_by", "project"
        )
        if is_list_page:
            query_set = query_set.prefetch_related(
                "path_patterns__created_by",
                "prompts__disabled_by",
                "prompts__created_by",
            )
        return query_set

    # Save selected prompt type for multi-table inheritance
    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)

        if formset.model == Prompt:
            for form in formset.forms:
                prompt: Prompt = form.instance
                if not form.cleaned_data.get("id") and prompt.id:
                    PromptModel = Prompt.get_subclass_by_name(
                        form.cleaned_data["prompt_type"]
                    )
                    prompt.create_subclass(PromptModel).save()


admin.site.register(FeedbackForm, FeedbackFormAdmin)
