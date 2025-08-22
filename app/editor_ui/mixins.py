from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.shortcuts import get_object_or_404

from app.projects.models import Project, ProjectMembership


class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser


class CreatedByUserMixin:
    """
    Mixin to automatically set ownership fields on model instances created via a form.
    """

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.created_by = self.request.user

        return super().form_valid(form)


class ProjectOwnerMembershipMixin:
    """
    Mixin to automatically create a ProjectMembership for the user as the project owner
    when a Project is created.
    """

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        instance = self.object

        if isinstance(instance, Project):
            ProjectMembership.objects.get_or_create(
                user=user,
                project=instance,
                created_by=user,
                defaults={"role": "owner"},
            )

        return response


class ProjectMembershipRequiredMixin:
    """
    Mixin to restrict access to views based on project membership and required roles.

    - For CreateView/ListView, expects 'project_uuid' in URL kwargs.
    - Project CreateView/ListView currently handled by views
    - Set `required_project_roles` as a class attribute (e.g., ["editor"]).
    """

    required_project_roles = None
    project_url_kwarg = "project_uuid"

    def get_project(self, kwargs=None):
        """
        Returns the Project instance to check permissions against.
        """
        # Accept kwargs as an argument for testing
        if kwargs is None:
            kwargs = self.kwargs

        project_uuid = self.kwargs.get(self.project_url_kwarg)
        if not project_uuid:
            raise ImproperlyConfigured(
                f"No project UUID found in URL kwargs (expected '{self.project_url_kwarg}')."
            )

        return get_object_or_404(Project, uuid=project_uuid)

    def dispatch(self, request, *args, **kwargs):
        """
        Checks if the current user has the required project membership roles before
        allowing access to the view.

        - Raises ImproperlyConfigured if `required_project_roles` is not set.
        - Allows superusers to bypass project membership checks.
        - Retrieves the relevant project instance (directly or via relation).
        - Denies access with PermissionDenied if the user does not have the required
          role(s) in the project.
        - Otherwise, proceeds with the normal dispatch process.
        """
        if not self.required_project_roles:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} requires 'required_project_roles' to be "
                "set as a tuple or list."
            )

        user = request.user
        if user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        project = self.get_project()
        roles = self.required_project_roles

        if not ProjectMembership.objects.filter(
            user=user, project=project, role__in=roles
        ).exists():
            raise PermissionDenied(
                "You do not have permission for this project."
            )

        return super().dispatch(request, *args, **kwargs)
