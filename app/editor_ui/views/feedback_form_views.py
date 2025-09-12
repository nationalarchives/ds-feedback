from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.aggregates import StringAgg
from django.db.models import (
    Count,
    F,
    Prefetch,
)
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DeleteView, DetailView, ListView

from app.editor_ui.forms import (
    FeedbackFormForm,
)
from app.editor_ui.mixins import (
    BreadCrumbsMixin,
    CreatedByUserMixin,
    ProjectMembershipRequiredMixin,
)
from app.editor_ui.views.base_views import CustomCreateView, CustomUpdateView
from app.feedback_forms.models import FeedbackForm
from app.projects.models import Project
from app.prompts.models import (
    Prompt,
)


class FeedbackFormCreateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    CreatedByUserMixin,
    BreadCrumbsMixin,
    CustomCreateView,
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

    form_class = FeedbackFormForm
    template_name = "editor_ui/feedback_forms/feedback_form_create.html"

    # required by ProjectMembershipRequiredMixin
    parent_model = Project
    parent_lookup_kwarg = "project_uuid"
    project_roles_required = ["editor", "owner"]

    # required by CustomCreateView
    model_display_name = "Feedback form"

    # required by BreadCrumbsMixin
    breadcrumb = None

    def form_valid(self, form):
        """
        Associates the feedback form with its parent project using the project UUID.
        """
        instance = form.save(commit=False)
        instance.project = Project.objects.get(
            uuid=self.kwargs.get("project_uuid")
        )
        # If the feedback form should be unpublished, set the disabled timestamp
        if form.cleaned_data.get("is_published") is False:
            instance.disabled_at = timezone.now()
            instance.disabled_by = self.request.user

        return super().form_valid(form)

    def get_success_url(self):
        feedback_form_uuid = self.object.uuid
        project_uuid = self.object.project.uuid

        return reverse(
            "editor_ui:projects:feedback_forms:detail",
            kwargs={
                "project_uuid": project_uuid,
                "feedback_form_uuid": feedback_form_uuid,
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # required for form cancel button
        project_uuid = self.kwargs.get("project_uuid")
        context.update(
            {"project_uuid": project_uuid},
        )

        return context


class FeedbackFormListView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    BreadCrumbsMixin,
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

    # required by ProjectMembershipRequiredMixin
    parent_model = Project
    parent_lookup_kwarg = "project_uuid"
    project_roles_required = ["editor", "owner"]

    # required by BreadCrumbsMixin for breadcrumb name
    breadcrumb = "Feedback forms"

    def get_queryset(self):
        qs = (
            FeedbackForm.objects.all()
            .prefetch_related("path_patterns")
            .select_related("project")
            .annotate(project_uuid=F("project__uuid"))
            .annotate(
                prompts_count=Count("prompts", distinct=True),
                path_patterns_str=StringAgg(
                    "path_patterns__pattern", delimiter=", "
                ),
            )
        )

        return qs.filter(project__uuid=self.kwargs.get("project_uuid"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {"project_uuid": self.kwargs.get("project_uuid")},
        )

        return context


class FeedbackFormDetailView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    BreadCrumbsMixin,
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
    context_object_name = "feedback_form"
    slug_field = "uuid"
    slug_url_kwarg = "feedback_form_uuid"

    # required by ProjectMembershipRequiredMixin
    project_roles_required = ["editor", "owner"]

    # required by BreadCrumbsMixin
    breadcrumb_field = "name"

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


class FeedbackFormUpdateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    BreadCrumbsMixin,
    CustomUpdateView,
):
    model = FeedbackForm
    form_class = FeedbackFormForm
    template_name = "editor_ui/feedback_forms/feedback_form_update.html"
    slug_field = "uuid"
    slug_url_kwarg = "feedback_form_uuid"

    # required by CustomUpdateView
    model_display_name = "Feedback form"

    # required by ProjectMembershipRequiredMixin
    project_roles_required = ["editor", "owner"]

    # required by BreadCrumbsMixin
    breadcrumb = None

    def get_initial(self):
        initial = super().get_initial()
        initial["is_published"] = not bool(self.object.disabled_at)
        return initial

    def form_valid(self, form):
        instance = form.save(commit=False)
        if form.cleaned_data.get("is_published") is False:
            instance.disabled_at = timezone.now()
            instance.disabled_by = self.request.user
        else:
            instance.disabled_at = None
            instance.disabled_by = None

        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "editor_ui:projects:feedback_forms:detail",
            kwargs={
                "project_uuid": self.object.project.uuid,
                "feedback_form_uuid": self.object.uuid,
            },
        )


class FeedbackFormDeleteView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    BreadCrumbsMixin,
    DeleteView,
):
    model = FeedbackForm
    template_name = "editor_ui/feedback_forms/feedback_form_delete.html"
    slug_field = "uuid"
    slug_url_kwarg = "feedback_form_uuid"

    # required by ProjectMembershipRequiredMixin
    parent_model = Project
    parent_lookup_kwarg = "project_uuid"
    project_roles_required = ["editor", "owner"]

    # required by BreadCrumbsMixin
    breadcrumb = None

    def get_queryset(self):
        project_uuid = self.kwargs.get("project_uuid")
        return FeedbackForm.objects.filter(
            project__uuid=project_uuid
        ).select_related("project")

    def get_success_url(self):
        project_uuid = self.kwargs.get("project_uuid")
        return reverse(
            "editor_ui:projects:feedback_forms:list",
            kwargs={"project_uuid": project_uuid},
        )
