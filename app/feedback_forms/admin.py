from django.contrib import admin
from django.forms import BaseInlineFormSet

from app.feedback_forms.models import FeedbackForm, PathPattern
from app.prompts.admin import PROMPT_TYPES, PromptAdmin
from app.prompts.models import Prompt
from app.utils.admin import (
    HideReadOnlyOnCreationAdmin,
    IsDisabledCheckboxForm,
    SetCreatedByOnCreationAdmin,
    SetDisabledByWhenDisabledAdmin,
    disallow_duplicates,
)


class FeedbackFormForm(IsDisabledCheckboxForm):
    class Meta:
        model = FeedbackForm
        fields = "__all__"


class PathPatternFormSet(BaseInlineFormSet):
    def clean(self):
        cleaned_data = super().clean()

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
                prompt = form.instance
                if not form.cleaned_data.get("id") and prompt.id:
                    PromptModel = PROMPT_TYPES[form.cleaned_data["prompt_type"]]
                    prompt.specialise(PromptModel).save()


admin.site.register(FeedbackForm, FeedbackFormAdmin)
