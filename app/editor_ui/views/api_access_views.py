from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView

from app.api.models import ProjectAPIAccess
from app.api.types import APIRole
from app.editor_ui.forms import ProjectAPIAccessCreateForm
from app.editor_ui.mixins import (
    BreadCrumbsMixin,
    CreatedByUserMixin,
    ProjectMembershipRequiredMixin,
)
from app.editor_ui.views.base_views import BaseCreateView
from app.projects.models import Project, ProjectMembership


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
        project_uuid = self.kwargs.get("project_uuid")
        project_qs = (
            ProjectAPIAccess.objects.filter(project__uuid=project_uuid)
            .filter(expires_at__gte=timezone.now())
            .select_related("project", "grantee", "created_by")
            .annotate(project_uuid=F("project__uuid"))
        )

        project_owner_ids = [
            membership.user.id
            for membership in ProjectMembership.objects.select_related(
                "user"
            ).filter(project__uuid=project_uuid, role="owner")
        ]

        # Only superusers, and project owners can see API access of other users
        if (
            self.request.user.is_superuser
            or self.request.user.id in project_owner_ids
        ):
            return project_qs

        return project_qs.filter(grantee=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_uuid"] = self.kwargs.get("project_uuid")
        return context


class APIAccessCreateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    CreatedByUserMixin,
    BreadCrumbsMixin,
    BaseCreateView,
):
    """
    View for creating a new ProjectAPIAccess within a project.

    - Editor users can only create API access for themselves
    - Owner users can create API access for any project member
    - All created API access has read-only permissions (explore-responses role)
    - Associates the new API access with its parent project using the project UUID
    """

    form_class = ProjectAPIAccessCreateForm
    object_name = "API Access"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["editor", "owner"]
    parent_model = Project
    parent_lookup_kwarg = "project_uuid"

    breadcrumb = "Create API Access"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "user": self.request.user,
                "project": get_object_or_404(
                    Project, uuid=self.kwargs.get("project_uuid")
                ),
            }
        )
        return kwargs

    def form_valid(self, form):
        """
        Associates the API access with its parent project and sets the role to read-only.
        """
        instance = form.save(commit=False)
        instance.project = Project.objects.get(
            uuid=self.kwargs.get("project_uuid")
        )

        # Set grantee based on user permissions
        if hasattr(form.cleaned_data, "grantee_user"):
            instance.grantee = form.cleaned_data["grantee_user"]
        else:
            # For editor users, grantee is themselves
            instance.grantee = self.request.user

        # Always set role to read-only access
        instance.role = APIRole.EXPLORE_RESPONSES

        return super().form_valid(form)

    def get_success_url(self):
        project_uuid = self.object.project.uuid
        return reverse(
            "editor_ui:project__api_access_list",
            kwargs={"project_uuid": project_uuid},
        )
