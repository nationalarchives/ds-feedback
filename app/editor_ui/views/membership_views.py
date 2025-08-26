from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)
from django.core.exceptions import PermissionDenied
from django.db.models import BooleanField, Case, Value, When
from django.views.generic import ListView

from app.editor_ui.mixins import (
    ProjectMembershipRequiredMixin,
)
from app.projects.models import Project, ProjectMembership


class ProjectMembershipListView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    ListView,
):
    model = ProjectMembership
    template_name = "editor_ui/projects/project_membership_list.html"
    context_object_name = "members"
    required_project_roles = ["editor", "owner"]

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["editor", "owner"]
    parent_model = Project
    parent_lookup_kwarg = "project_uuid"

    def get_queryset(self):
        queryset = super().get_queryset()
        project_uuid = self.kwargs.get("project_uuid")
        user = self.request.user

        return (
            queryset.filter(project__uuid=project_uuid)
            .select_related("user", "project")
            .annotate(
                is_current_user=Case(
                    When(user=user, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        project_uuid = self.kwargs.get("project_uuid")

        # Determine if the current user is a member of the project
        current_user_is_member = ProjectMembership.objects.filter(
            project__uuid=project_uuid, user=user
        ).exists()

        current_user_is_project_owner = ProjectMembership.objects.filter(
            project__uuid=project_uuid, user=user, role="owner"
        ).exists()

        context.update(
            {
                "current_user_is_project_member_or_admin": current_user_is_member
                or self.request.user.is_superuser,
                "current_user_is_project_owner_or_admin": current_user_is_project_owner
                or self.request.user.is_superuser,
                "project_uuid": project_uuid,
            }
        )

        return context

    def dispatch(self, request, *args, **kwargs):
        project_uuid = self.kwargs.get("project_uuid")

        # Get the user's roles for the project
        roles = ProjectMembership.objects.filter(
            project__uuid=project_uuid, user=request.user
        ).values_list("role", flat=True)
        is_owner = "owner" in roles
        is_editor = "editor" in roles

        # Ensure only project members can edit membership listing
        if not self.request.user.is_superuser:
            if not is_owner or not is_editor:
                raise PermissionDenied(
                    "You do not have permission to edit memberships for this project."
                )
        return super().dispatch(request, *args, **kwargs)
