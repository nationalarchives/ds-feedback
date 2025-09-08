from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.db.models import (
    Count,
    Prefetch,
    Q,
)
from django.urls import reverse
from django.views.generic import DetailView, ListView, UpdateView

from app.editor_ui.forms import (
    ProjectCreateForm,
    ProjectUpdateForm,
)
from app.editor_ui.mixins import (
    BreadCrumbsMixin,
    CreatedByUserMixin,
    ProjectMembershipRequiredMixin,
    ProjectOwnerMembershipMixin,
)
from app.editor_ui.views.base_views import BaseCreateView
from app.projects.models import Project


class ProjectCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    CreatedByUserMixin,
    ProjectOwnerMembershipMixin,
    BreadCrumbsMixin,
    BaseCreateView,
):
    form_class = ProjectCreateForm
    object_name = "Project"
    permission_required = ["projects.add_project"]
    breadcrumb = "Create a Project"

    def get_success_url(self):
        return reverse(
            "editor_ui:project_detail",
            kwargs={"project_uuid": self.object.uuid},
        )


class ProjectListView(
    LoginRequiredMixin,
    BreadCrumbsMixin,
    ListView,
):
    model = Project
    template_name = "editor_ui/projects/project_list.html"
    context_object_name = "projects"
    project_roles_required = ["editor", "owner"]

    breadcrumb = "Projects"

    def get_queryset(self):
        """
        Filter objects to only those where the user has one of the `project_roles_required`
        """
        user = self.request.user
        qs = Project.objects.all()

        qs = qs.annotate(
            responses_count=Count(
                "feedback_forms__responses",
                filter=Q(feedback_forms__disabled_at=None),
                distinct=True,
            ),
        )

        if user.is_superuser:
            return qs

        filter_kwargs = {
            "projectmembership__user": user,
            "projectmembership__role__in": self.project_roles_required,
        }

        return qs.filter(**filter_kwargs).distinct()


class ProjectDetailView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    BreadCrumbsMixin,
    DetailView,
):
    model = Project
    template_name = "editor_ui/projects/project_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "project_uuid"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["editor", "owner"]

    breadcrumb = "Project Details"

    def get_queryset(self):
        UserModel = get_user_model()

        return (
            Project.objects.all()
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
            .prefetch_related(
                Prefetch(
                    "members",
                    queryset=UserModel.objects.filter(
                        projectmembership__role="owner"
                    ),
                    to_attr="owner_members",
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        project = self.object
        owners = [str(owner) for owner in getattr(project, "owner_members", [])]

        context.update(
            {
                "forms_count": project.forms_count,
                "responses_count": project.responses_count,
                "owners": ", ".join(owners),
            }
        )

        return context


class ProjectUpdateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    UpdateView,
):
    model = Project
    form_class = ProjectUpdateForm
    template_name = "editor_ui/projects/project_update.html"
    slug_field = "uuid"
    slug_url_kwarg = "project_uuid"

    # ProjectOwnerMembershipMixin mixin attributes
    project_roles_required = ["owner"]

    def get_success_url(self):
        return reverse(
            "editor_ui:project_detail",
            kwargs={"project_uuid": self.object.uuid},
        )
