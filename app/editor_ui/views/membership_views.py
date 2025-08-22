from typing import Any
from django.core.exceptions import PermissionDenied
from django.db.models import BooleanField, Case, When, Value, Q
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)
from django.views.generic import ListView

from app.projects.models import ProjectMembership


class ProjectMembershipListView(LoginRequiredMixin, ListView):
    model = ProjectMembership
    template_name = "editor_ui/projects/project_membership_list.html"
    context_object_name = "members"
    required_project_roles = ["editor", "owner"]

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

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
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

        context["current_user_is_project_member_or_admin"] = (
            current_user_is_member or self.request.user.is_superuser
        )
        context["current_user_is_project_owner_or_admin"] = (
            current_user_is_project_owner or self.request.user.is_superuser
        )

        return context

    def dispatch(self, request, *args, **kwargs):
        project_uuid = self.kwargs.get("project_uuid")

        is_owner = ProjectMembership.objects.filter(
            project__uuid=project_uuid, user=request.user, role="owner"
        ).exists()

        # Only allow owners and admins to edit memberships
        if not is_owner and not self.request.user.is_superuser:
            raise PermissionDenied(
                "You do not have permission to edit memberships for this project."
            )
        return super().dispatch(request, *args, **kwargs)

    # TODO: Safe guard against editing user memberships for projects other than this one
    # if the queryset filter is ever removed by accident and tests fail.

    # The edit button won't be displayed unless users are owners of the project.
    # The add and detail view needs to be restricted to owners of the project as well.
