from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet
from django.utils import timezone

from app.feedback_forms.models import FeedbackForm, PathPattern
from app.utils.admin import (
    HideReadOnlyOnCreationAdmin,
    SetCreatedByOnCreationAdmin,
    SetDisabledByWhenDisabledAdmin,
)


class FeedbackFormForm(forms.ModelForm):
    is_disabled = forms.BooleanField(
        label="Disabled", required=False, initial=False
    )

    class Meta:
        model = FeedbackForm
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.disabled_at:
            self.fields["is_disabled"].initial = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data["is_disabled"] and not instance.disabled_at:
            instance.disabled_at = timezone.now()
        if not self.cleaned_data["is_disabled"]:
            instance.disabled_at = None

        if commit:
            instance.save()
        return instance


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


class FeedbackFormAdmin(
    HideReadOnlyOnCreationAdmin,
    SetCreatedByOnCreationAdmin,
    SetDisabledByWhenDisabledAdmin,
):
    form = FeedbackFormForm
    inlines = [PathPatternInline]
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
    list_display = ["name", "project", "patterns", "uuid"]
    list_filter = ["project"]
    search_fields = ["name", "uuid", "path_patterns__pattern"]

    def patterns(self, obj):
        return ", ".join(pattern.pattern for pattern in obj.path_patterns.all())

    patterns.short_description = "Path patterns"

    # Fetch path patterns for list view
    def get_queryset(self, request):
        query_set = super().get_queryset(request)
        return query_set.prefetch_related("path_patterns")

    # Set created_by for new PathPatterns
    def save_formset(self, request, form, formset, change):
        if formset.model == PathPattern:
            for form in formset.forms:
                path_pattern: PathPattern = form.instance
                if path_pattern.pk is None:
                    path_pattern.created_by = request.user

        super().save_formset(request, form, formset, change)


admin.site.register(FeedbackForm, FeedbackFormAdmin)
