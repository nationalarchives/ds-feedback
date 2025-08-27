from django.urls import Resolver404, resolve
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.shortcuts import get_object_or_404
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

    - For detail/edit/delete views: uses `get_object()` and calls `get_parent_project()`
      on it.
    - For list/create views: set `parent_lookup_kwarg` and `parent_model` to fetch the
      parent object, then call `get_parent_project()` on that object.
    - Set `project_roles_required` (a list of allowed roles, e.g., ["editor", "owner"]).
    """

    project_roles_required = None
    parent_lookup_kwarg = None
    parent_model = None

    def get_parent_object(self):
        """
        Fetch the parent object using the URL kwarg and model.

        Usage:

        - For list/create views to resolve the object from which to traverse to Project.
        """
        if not self.parent_lookup_kwarg:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} needs 'parent_lookup_kwarg' to be set."
            )
        if not self.parent_model:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} needs 'parent_model' to be set."
            )

        lookup_value = self.kwargs.get(self.parent_lookup_kwarg)

        if not lookup_value:
            raise ImproperlyConfigured(
                f"Missing '{self.parent_lookup_kwarg}' in URL kwargs."
            )

        return get_object_or_404(self.parent_model, uuid=lookup_value)

    def get_project_for_permission_check(self):
        """
        Returns the related Project for permission checks by calling
        `get_parent_project()` on the relevant object.
        """

        if isinstance(self, (DetailView, UpdateView, DeleteView)):
            obj = self.get_object()
        else:
            # For list and create views
            obj = self.get_parent_object()

        if hasattr(obj, "get_parent_project") and callable(
            obj.get_parent_project
        ):
            return obj.get_parent_project()
        elif isinstance(obj, Project):
            return obj
        else:
            raise ImproperlyConfigured(
                f"{obj.__class__.__name__} must implement get_parent_project()."
            )

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

        if not ProjectMembership.objects.filter(
            user=user, project=project, role__in=self.project_roles_required
        ).exists():
            raise PermissionDenied(
                "You do not have permission for this project."
            )

        return super().dispatch(request, *args, **kwargs)


class BreadCrumbsMixin:
    """
    A mixin to help with the display of breadcrumbs

    Usage:
    - Set the `breadcrumb` property in the views
    """

    breadcrumb = "Error"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["breadcrumbs"] = self._breadcrumb_calculator()

    def _breadcrumb_calculator(self):
        parts = self.request.path.split("/")
        breadcrumbs = []

        parsed_url = ""

        for url_part in parts[:-1]:
            parsed_url += f"{url_part}/"
            resolved = self._breadcrumb_inner(parsed_url)
            if resolved:
                breadcrumbs.append(resolved)

        return breadcrumbs

    def _breadcrumb_inner(self, url):
        try:
            resolved = resolve(url)

            target = resolved.func.view_class
            if issubclass(target, BreadCrumbsMixin):
                return {"url": url, "slug": target.breadcrumb}
            else:
                return None
        except Resolver404:
            return None
