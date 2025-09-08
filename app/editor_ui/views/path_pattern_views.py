from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.urls import reverse
from django.views.generic import UpdateView

from app.editor_ui.forms import (
    PathPatternForm,
)
from app.editor_ui.mixins import (
    BreadCrumbsMixin,
    CreatedByUserMixin,
    ProjectMembershipRequiredMixin,
)
from app.editor_ui.views.base_views import BaseCreateView, CustomUpdateView
from app.feedback_forms.models import FeedbackForm, PathPattern
from app.projects.models import Project


class PathPatternCreateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    CreatedByUserMixin,
    BreadCrumbsMixin,
    BaseCreateView,
):
    form_class = PathPatternForm
    object_name = "Path Pattern"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["editor", "owner"]
    parent_model = FeedbackForm
    parent_lookup_kwarg = "feedback_form_uuid"

    breadcrumb = "Create a Path Pattern"

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.feedback_form = FeedbackForm.objects.get(
            uuid=self.kwargs.get("feedback_form_uuid")
        )
        instance.project = Project.objects.get(
            uuid=self.kwargs.get("project_uuid")
        )
        instance.pattern_with_wildcard = form.cleaned_data[
            "pattern_with_wildcard"
        ]

        try:
            response = super().form_valid(form)
        except IntegrityError:
            form.add_error(
                "pattern_with_wildcard",
                "This pattern already exists for this project. Please use a different pattern.",
            )
            return self.form_invalid(form)

        return response

    def get_success_url(self):
        feedback_form_uuid = self.object.feedback_form.uuid
        project_uuid = self.object.project.uuid

        return reverse(
            "editor_ui:project__feedback_form_detail",
            kwargs={
                "project_uuid": project_uuid,
                "feedback_form_uuid": feedback_form_uuid,
            },
        )

    def get_context_data(self, **kwargs):
        """
        Adds the object name to the template context for generic form rendering.

        The object name is used by the generic create template to display
        appropriate headings and labels.
        """
        context = super().get_context_data(**kwargs)
        context["object_name"] = "Path Pattern"
        return context


class PathPatternUpdateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    CustomUpdateView,
):
    model = PathPattern
    form_class = PathPatternForm
    template_name = "editor_ui/path_patterns/path_pattern_update.html"
    slug_field = "uuid"
    slug_url_kwarg = "path_pattern_uuid"

    model_display_name = "Path Pattern"

    # ProjectOwnerMembershipMixin mixin attributes
    project_roles_required = ["editor", "owner"]

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.pattern_with_wildcard = form.cleaned_data[
            "pattern_with_wildcard"
        ]

        try:
            response = super().form_valid(form)
        except IntegrityError:
            form.add_error(
                "pattern_with_wildcard",
                "This pattern already exists for this project. Please use a different pattern.",
            )
            return self.form_invalid(form)

        return response

    def get_success_url(self):
        return reverse(
            "editor_ui:project__feedback_form_detail",
            kwargs={
                "project_uuid": self.object.feedback_form.project.uuid,
                "feedback_form_uuid": self.object.feedback_form.uuid,
            },
        )
