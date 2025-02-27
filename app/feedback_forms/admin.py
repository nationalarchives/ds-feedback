from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet

from app.feedback_forms.models import FeedbackForm, PathPattern
from app.prompts.admin import PROMPT_TYPES, PromptAdmin
from app.prompts.models import Prompt
from app.utils.admin import (
    HideReadOnlyOnCreationAdmin,
    IsDisabledCheckboxForm,
    SetCreatedByOnCreationAdmin,
    SetDisabledByWhenDisabledAdmin,
)


class FeedbackFormForm(IsDisabledCheckboxForm):
    class Meta:
        model = FeedbackForm
        fields = "__all__"


class PathPatternFormSet(BaseInlineFormSet):
    def clean(self):
        cleaned_data = super().clean()

        patterns = set()
        for form in self.forms:
            if form.cleaned_data and "pattern" in form.cleaned_data:
                # Propagate project from feedback_form
                instance: PathPattern = form.instance
                instance.project = form.cleaned_data["feedback_form"].project
                form.full_clean()

                # Ensure multiple new PathPatterns cannot share the same pattern.
                if instance.pattern in patterns:
                    if not form.has_error("pattern"):
                        form.add_error(
                            "pattern",
                            ValidationError(
                                "You cannot use the same pattern twice in a project."
                            ),
                        )
                patterns.add(instance.pattern)

        return cleaned_data


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
        id = request.resolver_match.kwargs.get("object_id")
        query_set = super().get_queryset(request)
        query_set = query_set.select_related(
            "created_by", "disabled_by", "project"
        )
        # Prefetch only changelist page
        if not id:
            query_set = query_set.prefetch_related(
                "path_patterns__created_by",
                "prompts__disabled_by",
                "prompts__created_by",
            )
        return query_set

    # Set created_by for new PathPatterns
    def save_formset(self, request, form, formset, change):
        # Set created_by for new PathPatterns and Prompts
        if formset.model == PathPattern or formset.model == Prompt:
            for form in formset.forms:
                instance = form.instance
                if instance.pk is None:
                    instance.created_by = request.user

        # Set disabled_by for disabled Prompts
        if formset.model == Prompt:
            for form in formset.forms:
                prompt: Prompt = form.instance
                if prompt.disabled_at and not prompt.disabled_by:
                    prompt.disabled_by = request.user
                if not prompt.disabled_at:
                    prompt.disabled_by = None

        super().save_formset(request, form, formset, change)

        # Save selected prompt type for multi-table inheritance
        if formset.model == Prompt:
            for form in formset.forms:
                prompt = form.instance
                if not form.cleaned_data.get("id") and prompt.id:
                    PromptModel = PROMPT_TYPES[form.cleaned_data["prompt_type"]]
                    specific_prompt = PromptModel(prompt_ptr_id=prompt.id)
                    specific_prompt.__dict__.update(prompt.__dict__)
                    specific_prompt.save()


admin.site.register(FeedbackForm, FeedbackFormAdmin)
