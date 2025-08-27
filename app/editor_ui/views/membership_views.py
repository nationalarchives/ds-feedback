from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)
from django.db import IntegrityError
from django.db.models import BooleanField, Case, Value, When
from django.urls import reverse
from django.views.generic import ListView

from app.editor_ui.forms import ProjectMembershipCreateForm
from app.editor_ui.mixins import (
    ProjectMembershipRequiredMixin,
    ProjectOwnerMembershipMixin,
)
from app.editor_ui.utils import send_email_util
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


class ProjectMembershipCreateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    ProjectOwnerMembershipMixin,
    BaseCreateView,
):
    form_class = ProjectMembershipCreateForm
    object_name = "Project Membership"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["owner"]
    parent_model = Project
    parent_lookup_kwarg = "project_uuid"

    def form_valid(self, form):
        project_uuid = self.kwargs.get("project_uuid")
        user = self.request.user

        project = Project.objects.get(uuid=project_uuid)
        form.instance.project = project
        form.instance.created_by = user
        form.instance.user = form.cleaned_data["user_obj"]

        try:
            response = super().form_valid(form)
        except IntegrityError:
            form.add_error(
                "email", "This user is already a member of the project."
            )
            return self.form_invalid(form)
        else:
            send_email_util(
                subject_template_name="editor_ui/emails/project_membership_subject.txt",
                email_template_name="editor_ui/emails/project_membership_added_email.html",
                context={
                    "project": project,
                    "role": form.cleaned_data["role"],
                    "added_by": user,
                    "new_member": form.instance.user,
                },
                from_email=None,
                to_email=form.instance.user.email,
                request=self.request,
            )

            return response

    def get_success_url(self):
        project_uuid = self.kwargs.get("project_uuid")
        return reverse(
            "editor_ui:project_memberships",
            kwargs={"project_uuid": project_uuid},
        )
