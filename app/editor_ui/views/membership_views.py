from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
)
from django.db import IntegrityError, transaction
from django.db.models import BooleanField, Case, Value, When
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DeleteView, ListView

from app.editor_ui.forms import (
    ProjectMembershipCreateForm,
    ProjectMembershipUpdateForm,
)
from app.editor_ui.mixins import (
    BreadCrumbsMixin,
    ProjectMembershipRequiredMixin,
    ProjectOwnerMembershipMixin,
)
from app.editor_ui.utils import send_email_util
from app.editor_ui.views.base_views import CustomCreateView, CustomUpdateView
from app.projects.models import Project, ProjectMembership


class ProjectMembershipListView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    BreadCrumbsMixin,
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

    breadcrumb = "Project Members"

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

        project_uuid = self.kwargs.get("project_uuid")
        context.update(
            {"project_uuid": project_uuid},
        )

        return context


class ProjectMembershipCreateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    ProjectOwnerMembershipMixin,
    BreadCrumbsMixin,
    CustomCreateView,
):
    form_class = ProjectMembershipCreateForm
    template_name = "editor_ui/projects/project_membership_create.html"
    model_display_name = "Project Membership"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["owner"]
    parent_model = Project
    parent_lookup_kwarg = "project_uuid"

    breadcrumb = None

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
            "editor_ui:projects:memberships:list",
            kwargs={"project_uuid": project_uuid},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # required for form cancel button
        project_uuid = self.kwargs.get("project_uuid")
        context.update(
            {"project_uuid": project_uuid},
        )

        return context


class ProjectMembershipUpdateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    ProjectOwnerMembershipMixin,
    BreadCrumbsMixin,
    CustomUpdateView,
):
    form_class = ProjectMembershipUpdateForm
    template_name = "editor_ui/projects/project_membership_update.html"
    slug_field = "uuid"
    slug_url_kwarg = "membership_uuid"
    model_display_name = "Project Membership"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["owner"]
    parent_model = Project
    parent_lookup_kwarg = "project_uuid"

    breadcrumb = None

    def get_queryset(self):
        # Limit the queryset to memberships of the specified project
        project_uuid = self.kwargs.get("project_uuid")
        return ProjectMembership.objects.filter(
            project__uuid=project_uuid
        ).select_related("user", "project")

    def get_success_url(self):
        project_uuid = self.kwargs.get("project_uuid")
        return reverse(
            "editor_ui:projects:memberships:list",
            kwargs={"project_uuid": project_uuid},
        )

    def form_valid(self, form):
        # Ensure there is always at least one owner assigned to a project
        original_role = form.initial.get("role")
        new_role = form.cleaned_data.get("role")

        if original_role == "owner" and new_role != "owner":
            with transaction.atomic():
                memberships = (
                    ProjectMembership.objects.select_for_update().filter(
                        project=self.object.project
                    )
                )

                owners_count = (
                    memberships.filter(role="owner")
                    .exclude(pk=self.object.pk)
                    .count()
                )

                if owners_count == 0:
                    messages.error(
                        self.request,
                        f"Cannot update {self.object.user}. "
                        "Each project must have at least one owner.",
                    )
                    return redirect(
                        "editor_ui:projects:memberships:list",
                        project_uuid=self.object.project.uuid,
                    )

        return super().form_valid(form)


class ProjectMembershipDeleteView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    BreadCrumbsMixin,
    DeleteView,
):
    model = ProjectMembership
    template_name = "editor_ui/projects/project_membership_confirm_delete.html"
    slug_field = "uuid"
    slug_url_kwarg = "membership_uuid"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["owner"]
    parent_model = Project
    parent_lookup_kwarg = "project_uuid"

    breadcrumb = None

    def get_queryset(self):
        project_uuid = self.kwargs.get("project_uuid")
        return ProjectMembership.objects.filter(
            project__uuid=project_uuid
        ).select_related("user", "project")

    def get_success_url(self):
        # If a user left the project, redirect to the project list
        if self.object.user == self.request.user:
            return reverse("editor_ui:projects:list")
        # Otherwise, redirect to the project members list
        project_uuid = self.kwargs.get("project_uuid")
        return reverse(
            "editor_ui:projects:memberships:list",
            kwargs={"project_uuid": project_uuid},
        )

    def dispatch(self, request, *args, **kwargs):
        """
        Allow users to delete their own membership if they are an editor.
        Otherwise, require owner role.
        """
        self.object = self.get_object()
        object_user = self.object.user
        authenticated_user = request.user

        # Bypass role checks for self-deleting users
        if object_user == authenticated_user:
            self.project_roles_required = ["editor", "owner"]
        else:
            self.project_roles_required = ["owner"]

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Ensure there is always at least one owner assigned to a project
        owners_count = ProjectMembership.objects.filter(
            project=self.object.project, role="owner"
        ).count()

        if self.object.role == "owner":
            with transaction.atomic():
                memberships = (
                    ProjectMembership.objects.select_for_update().filter(
                        project=self.object.project
                    )
                )

                owners_count = (
                    memberships.filter(role="owner")
                    .exclude(pk=self.object.pk)
                    .count()
                )

                if owners_count == 0:
                    messages.error(
                        self.request,
                        f"Cannot remove {self.object.user}. Each project must have at least one owner.",
                    )
                    return redirect(
                        "editor_ui:projects:memberships:list",
                        project_uuid=self.object.project.uuid,
                    )

        return super().form_valid(form)
