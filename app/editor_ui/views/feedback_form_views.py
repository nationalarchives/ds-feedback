from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.aggregates import StringAgg
from django.db.models import (
    Count,
    F,
    Prefetch,
)
from django.urls import reverse
from django.views.generic import DetailView, ListView

from app.editor_ui.forms import (
    FeedbackFormForm,
)
from app.editor_ui.mixins import (
    CreatedByUserMixin,
    ProjectMembershipRequiredMixin,
)
from app.editor_ui.views.base_views import BaseCreateView
from app.feedback_forms.models import FeedbackForm
from app.projects.models import Project
from app.prompts.models import (
    Prompt,
)


class FeedbackFormCreateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    CreatedByUserMixin,
    BaseCreateView,
):
    """
    View for creating a new FeedbackForm within a project.

    - Associates the new feedback form with its parent project using the project UUID
      from the URL.
    - Redirects to the new feedback form's detail page upon successful creation.

    Notes:
        Requires superuser access and authentication
        Ownership (created_by, owned_by) is handled by CreatedByUserMixin
    """

    model = FeedbackForm
    form_class = FeedbackFormForm
    object_name = "Feedback Form"
    required_project_roles = ["editor", "owner"]

    def form_valid(self, form):
        """
        Associates the feedback form with its parent project using the project UUID.
        """
        instance = form.save(commit=False)
        instance.project = Project.objects.get(
            uuid=self.kwargs.get("project_uuid")
        )

        return super().form_valid(form)

    def get_success_url(self):
        feedback_form_uuid = self.object.uuid
        project_uuid = self.object.project.uuid

        return reverse(
            "editor_ui:project__feedback_form_detail",
            kwargs={
                "project_uuid": project_uuid,
                "feedback_form_uuid": feedback_form_uuid,
            },
        )


class FeedbackFormListView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    ListView,
):
    """
    Displays a list of feedback forms for a given project.

    - Fetches all feedback forms associated with parent project.
    - Prefetches related path patterns and project data.
    - Annotates each feedback form with its project UUID and prompt count.
    - Passes the project UUID to the context for use in links.
    """

    model = FeedbackForm
    template_name = "editor_ui/feedback_forms/feedback_form_list.html"
    context_object_name = "feedback_forms"
    required_project_roles = ["editor", "owner"]

    def get_queryset(self):
        qs = (
            FeedbackForm.objects.all()
            .prefetch_related("path_patterns")
            .select_related("project")
            .annotate(project_uuid=F("project__uuid"))
            .annotate(
                prompts_count=Count("prompts", distinct=True),
                path_patterns_str=StringAgg(
                    "path_patterns__pattern", delimiter=", ", distinct=True
                ),
            )
        )

        return qs.filter(project__uuid=self.kwargs.get("project_uuid"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_uuid"] = self.kwargs.get("project_uuid")

        return context


class FeedbackFormDetailView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    DetailView,
):
    """
    Displays the details of a single FeedbackForm, including its prompts and path
    patterns.

    - Fetches the feedback form by UUID and prefetches related path patterns and
      prompts.
    - Passes project UUID, path patterns, and ordered prompts to the template context.
    """

    model = FeedbackForm
    template_name = "editor_ui/feedback_forms/feedback_form_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "feedback_form_uuid"
    context_object_name = "feedback_form"
    required_project_roles = ["editor", "owner"]

    def get_queryset(self):
        return (
            FeedbackForm.objects.all()
            .prefetch_related("path_patterns")
            .prefetch_related(
                Prefetch(
                    "prompts",
                    queryset=Prompt.objects.select_subclasses().select_related(
                        "created_by"
                    ),
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "project_uuid": self.kwargs.get("project_uuid"),
                "path_patterns": self.object.path_patterns.all(),
                "prompts": self.object.prompts.select_subclasses().order_by(
                    "order"
                ),
            }
        )
        return context
