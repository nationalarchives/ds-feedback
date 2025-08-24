from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.views.generic import DeleteView, DetailView, UpdateView

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
    Restricts view access to users with specific roles on a related Project.

    Usage:

    - For Detail/Update/Delete views: uses `get_object()` and traverses the relationship
      specified by `project_lookup_path_from_parent` (e.g., "project" or
      "feedback_form__project") to find the Project. If the object has a direct FK to
      Project named 'project', you may omit `project_lookup_path_from_parent` (defaults
      to "project").
    - For List/Create views: uses `parent_lookup_kwarg` and `parent_model` to fetch the
      parent object (e.g., a FeedbackForm), then traverses
      `project_lookup_path_from_parent` from that object to find the Project.
    - Set `project_roles_required` to the allowed roles (e.g., ["editor", "owner"]).

    Note: For any nested resource (where the parent is not directly a Project), you must
    set `project_lookup_path_from_parent` to specify the path to the Project.
    """

    project_roles_required = None
    project_lookup_path_from_parent = None
    parent_lookup_kwarg = None
    parent_model = None

    def get_parent_object(self):
        """
        Fetch the parent object using the URL kwarg and model.

        Usage:

        - For list/create views to resolve the object from which to traverse to Project.
        """
        if not self.parent_lookup_kwarg or not self.parent_model:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} needs 'parent_lookup_kwarg' and "
                "'parent_model'."
            )

        lookup_value = self.kwargs.get(self.parent_lookup_kwarg)

        if not lookup_value:
            raise ImproperlyConfigured(
                f"Missing '{self.parent_lookup_kwarg}' in URL kwargs."
            )

        return self.parent_model.objects.get(uuid=lookup_value)

    def get_project_for_permission_check(self):
        """
        Resolve the related Project for permission checks.

        Usage:

        - For detail/edit/delete views, starts from the object returned by
          `get_object()`.
        - For list/create views, starts from the parent object returned by
          `get_parent_object()`. Traverses the path specified by
          `project_lookup_path_from_parent` to reach the Project.
        """
        # For detail/edit views
        if isinstance(self, (DetailView, UpdateView, DeleteView)):
            obj = self.get_object()
        # For list views
        else:
            obj = self.get_parent_object()

        # Traverse relationships to get the project
        relation = getattr(self, "project_lookup_path_from_parent", None)
        if not relation:
            # If the object is already a Project, just return it
            if isinstance(obj, Project):
                return obj
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} requires 'project_lookup_path_from_parent' "
                "for nested resources."
            )

        for part in relation.split("__"):
            obj = getattr(obj, part)
        return obj

    def dispatch(self, request, *args, **kwargs):
        """
        Allow access only if the user has the required role on the resolved Project.

        Superusers are always allowed. Raises PermissionDenied if the user lacks the
        required role.
        """
        if not self.project_roles_required:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} requires 'project_roles_required' to be "
                "set."
            )

        user = request.user
        if user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        project = self.get_project_for_permission_check()
        roles = self.project_roles_required

        if not ProjectMembership.objects.filter(
            user=user, project=project, role__in=roles
        ).exists():
            raise PermissionDenied(
                "You do not have permission for this project."
            )

        return super().dispatch(request, *args, **kwargs)
