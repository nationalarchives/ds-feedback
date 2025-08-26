from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import BooleanField, Case, Value, When
from django.urls import reverse
from django.views.generic import ListView

from app.editor_ui.forms import ProjectMembershipCreateForm
from app.editor_ui.mixins import (
    ProjectMembershipRequiredMixin,
    ProjectOwnerMembershipMixin,
)
from app.editor_ui.views.base_views import BaseCreateView
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
            if not is_owner and not is_editor:
                raise PermissionDenied(
                    "You do not have permission to edit memberships for this project."
                )
        return super().dispatch(request, *args, **kwargs)


class ProjectMembershipCreateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    ProjectOwnerMembershipMixin,
    BaseCreateView,
):
    model = ProjectMembership
    form_class = ProjectMembershipCreateForm
    template_name = "editor_ui/create.html"
    object_name = "Project Membership"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["editor", "owner"]
    parent_model = Project
    parent_lookup_kwarg = "project_uuid"

    def form_valid(self, form):
        project_uuid = self.kwargs.get("project_uuid")
        user = self.request.user

        # Ensure only project owners can add memberships
        roles = ProjectMembership.objects.filter(
            project__uuid=project_uuid, user=user
        ).values_list("role", flat=True)
        is_owner = "owner" in roles

        if not self.request.user.is_superuser:
            if not is_owner:
                raise PermissionDenied(
                    "You do not have permission to add memberships for this project."
                )

        project = Project.objects.get(uuid=project_uuid)
        form.instance.project = project
        form.instance.created_by = user
        form.instance.user = form.cleaned_data["user_obj"]

        try:
            return super().form_valid(form)
        except IntegrityError:
            form.add_error(
                "email", "This user is already a member of the project."
            )
            return self.form_invalid(form)

    def get_success_url(self):
        project_uuid = self.kwargs.get("project_uuid")
        return reverse(
            "editor_ui:project_memberships",
            kwargs={"project_uuid": project_uuid},
        )
