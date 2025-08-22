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

        return queryset.filter(project__uuid=project_uuid).select_related(
            "user", "project"
        )

    # TODO: Safe guard against editing user memberships for projects other than this one
    # if the queryset filter is ever removed by accident and tests fail.

    # The edit button won't be displayed unless users are owners of the project.
    # The add and detail view needs to be restricted to owners of the project as well.
