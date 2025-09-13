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
from django.views.generic import DetailView, ListView

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
from app.editor_ui.views.base_views import CustomCreateView, CustomUpdateView
from app.projects.models import Project


class ProjectCreateView(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    CreatedByUserMixin,
    ProjectOwnerMembershipMixin,
    BreadCrumbsMixin,
    CustomCreateView,
):
    form_class = ProjectCreateForm
    template_name = "editor_ui/projects/project_create.html"

    # required by PermissionRequiredMixin
    permission_required = ["projects.add_project"]

    # required by CustomCreateView
    model_display_name = "Project"

    # required by breadcrumbsMixin
    breadcrumb = "None"

    def get_success_url(self):
        return reverse(
            "editor_ui:projects:detail",
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

    # required by get_queryset method
    project_roles_required = ["editor", "owner"]

    # required by BreadCrumbsMixin
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

        qs = qs.order_by("name")

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

    # required by ProjectMembershipRequiredMixin
    project_roles_required = ["editor", "owner"]

    # required by BreadCrumbsMixin
    breadcrumb_field = "name"

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
    BreadCrumbsMixin,
    CustomUpdateView,
):
    model = Project
    form_class = ProjectUpdateForm
    template_name = "editor_ui/projects/project_update.html"
    slug_field = "uuid"
    slug_url_kwarg = "project_uuid"

    # required by ProjectOwnerMembershipMixin
    project_roles_required = ["owner"]

    # required by CustomUpdateView
    model_display_name = "Project"

    # required by BreadCrumbsMixin
    breadcrumb = None

    def get_success_url(self):
        return reverse(
            "editor_ui:projects:detail",
            kwargs={"project_uuid": self.object.uuid},
        )
