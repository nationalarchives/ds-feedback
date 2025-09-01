from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.views.generic import ListView

from app.api.models import ProjectAPIAccess
from app.editor_ui.mixins import (
    BreadCrumbsMixin,
    ProjectMembershipRequiredMixin,
)
from app.projects.models import Project


class APIAccessListView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    BreadCrumbsMixin,
    ListView,
):
    """
    Displays a list of API access entries for a given project.
    
    - Editor users can only see their own API access entries
    - Owner users and superusers can see all API access entries for the project
    - Fetches all API access entries associated with parent project
    - Annotates each entry with project UUID for use in links
    """

    model = ProjectAPIAccess
    template_name = "editor_ui/api_access/api_access_list.html"
    context_object_name = "api_accesses"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["editor", "owner"]
    parent_model = Project
    parent_lookup_kwarg = "project_uuid"

    breadcrumb = "API Access"

    def get_queryset(self):
        qs = (
            ProjectAPIAccess.objects.all()
            .select_related("project", "grantee", "created_by")
            .annotate(project_uuid=F("project__uuid"))
        )

        project_qs = qs.filter(project__uuid=self.kwargs.get("project_uuid"))

        # Editor users can only see their own API access entries
        if not (self.request.user.is_superuser or 
                self.request.user in self.get_parent_object().owners.all()):
            project_qs = project_qs.filter(grantee=self.request.user)

        return project_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_uuid"] = self.kwargs.get("project_uuid")
        return context