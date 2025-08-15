from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, F, Prefetch, Q
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView

from app.editor_ui.forms import FeedbackFormForm, ProjectForm
from app.editor_ui.mixins import OwnedByUserMixin, SuperuserRequiredMixin
from app.feedback_forms.models import FeedbackForm
from app.projects.models import Project
from app.prompts.models import Prompt


class ProjectCreateView(
    OwnedByUserMixin, SuperuserRequiredMixin, LoginRequiredMixin, CreateView
):
    model = Project
    form_class = ProjectForm
    template_name = "editor_ui/projects/project_create.html"

    def get_success_url(self):
        return reverse(
            "editor_ui:project_detail", kwargs={"uuid": self.object.uuid}
        )


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "editor_ui/projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        if self.request.user.is_superuser:
            qs = Project.objects.all().select_related("owned_by")
        else:
            qs = Project.objects.filter(owned_by=self.request.user)
        return qs


class ProjectDetailView(SuperuserRequiredMixin, LoginRequiredMixin, DetailView):
    model = Project
    template_name = "editor_ui/projects/project_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        return (
            Project.objects.all()
            .select_related("owned_by")
            .annotate(
                forms_count=Count(
                    "feedback_forms",
                    filter=Q(feedback_forms__disabled_at=None),
                ),
                responses_count=Count(
                    "feedback_forms__responses",
                    filter=Q(feedback_forms__disabled_at=None),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        context["forms_count"] = project.forms_count
        context["responses_count"] = project.responses_count

        return context


class FeedbackFormListView(
    SuperuserRequiredMixin, LoginRequiredMixin, ListView
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

    def get_queryset(self):
        qs = (
            FeedbackForm.objects.all()
            .prefetch_related("path_patterns")
            .select_related("project")
            .annotate(project_uuid=F("project__uuid"))
            .annotate(
                prompts_count=Count("prompts", distinct=True),
            )
        )

        return qs.filter(project__uuid=self.kwargs.get("project_uuid"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_uuid"] = self.kwargs.get("project_uuid")

        return context


class FeedbackFormCreateView(
    OwnedByUserMixin, SuperuserRequiredMixin, LoginRequiredMixin, CreateView
):
    """
    View for creating a new FeedbackForm within a project.

    - Associates the new feedback form with its parent project using the project UUID
      from the URL.
    - Redirects to the new feedback form's detail page upon successful creation.

    Notes:
        Requires superuser access and authentication
        Ownership (created_by, owned_by) is handled by OwnedByUserMixin
    """

    model = FeedbackForm
    form_class = FeedbackFormForm
    template_name = "editor_ui/feedback_forms/feedback_form_create.html"

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


class FeedbackFormDetailView(
    SuperuserRequiredMixin, LoginRequiredMixin, DetailView
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
