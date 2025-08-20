from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import (
    Count,
    Q,
)
from django.urls import reverse
from django.views.generic import DetailView, ListView

from app.editor_ui.forms import (
    ProjectForm,
)
from app.editor_ui.mixins import CreatedByUserMixin, SuperuserRequiredMixin
from app.editor_ui.views.base_views import BaseCreateView
from app.projects.models import Project


class ProjectCreateView(
    CreatedByUserMixin,
    SuperuserRequiredMixin,
    LoginRequiredMixin,
    BaseCreateView,
):
    model = Project
    form_class = ProjectForm
    object_name = "Project"

    def get_success_url(self):
        return reverse(
            "editor_ui:project_detail",
            kwargs={"project_uuid": self.object.uuid},
        )


class ProjectListView(
    LoginRequiredMixin,
    ListView,
):
    model = Project
    template_name = "editor_ui/projects/project_list.html"
    context_object_name = "projects"
    required_project_roles = ["editor", "owner"]

    def get_queryset(self):
        """
        Filter objects to only those where the user has one of the `required_project_roles`
        """
        user = self.request.user
        qs = super().get_queryset()

        if user.is_superuser:
            return qs

        filter_kwargs = {
            "projectmembership__user": user,
            "projectmembership__role__in": self.required_project_roles,
        }

        return qs.filter(**filter_kwargs).distinct()

class ProjectDetailView(SuperuserRequiredMixin, LoginRequiredMixin, DetailView):
    model = Project
    template_name = "editor_ui/projects/project_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "project_uuid"

    def get_queryset(self):
        return (
            Project.objects.all()
            .select_related("owned_by")
            .annotate(
                forms_count=Count(
                    "feedback_forms",
                    filter=Q(feedback_forms__disabled_at=None),
                    distinct=True,
                ),
                responses_count=Count(
                    "feedback_forms__responses",
                    filter=Q(feedback_forms__disabled_at=None),
                    distinct=True,
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        context["forms_count"] = project.forms_count
        context["responses_count"] = project.responses_count

        return context
