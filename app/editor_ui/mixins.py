from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import Resolver404, resolve
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

    def get_user_project_permissions(self, user=None):
        """
        Return a dictionary of the user's permissions/role for the current project (
        retrieved get_project_for_permission_check method). If user is not provided,
        uses self.request.user.
        """
        if user is None:
            user = self.request.user
        project = self.get_project_for_permission_check()
        if user.is_superuser:
            return {
                "is_superuser": True,
                "is_owner": True,
                "is_member": True,
                "role": "superuser",
            }
        membership = ProjectMembership.objects.filter(
            user=user, project=project
        ).first()
        return {
            "is_superuser": False,
            "is_owner": bool(membership and membership.role == "owner"),
            "is_member": bool(membership),
            "role": membership.role if membership else None,
        }

    def get_object(self):
        # TODO: move this to its own mixin.
        # ProjectMembershipRequiredMixin is only meant to handle ProjectMemberships
        if hasattr(self, "_cached_object"):
            return self._cached_object
        obj = super().get_object()
        self._cached_object = obj
        return obj

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
        `get_parent_project()` on the relevant object. Caches the result per-instance.
        """
        if hasattr(self, "_permission_project"):
            return self._permission_project

        if isinstance(self, (DetailView, UpdateView, DeleteView)):
            obj = self.get_object()
        else:
            # For list and create views
            obj = self.get_parent_object()

        if hasattr(obj, "get_parent_project") and callable(
            obj.get_parent_project
        ):
            project = obj.get_parent_project()
        elif isinstance(obj, Project):
            project = obj
        else:
            raise ImproperlyConfigured(
                f"{obj.__class__.__name__} must implement get_parent_project()."
            )

        self._permission_project = project

        return project

    def get_context_data(self, *args, **kwargs):
        """
        Update template context with `user_project_permissions` to be used for
        """
        context = super().get_context_data(*args, **kwargs)
        context["user_project_permissions"] = (
            self.get_user_project_permissions()
        )
        return context

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

        self._current_membership = ProjectMembership.objects.filter(
            user=user, project=project
        ).first()

        if (
            not self._current_membership
            or self._current_membership.role not in self.project_roles_required
        ):
            raise PermissionDenied(
                "You do not have permission for this project."
            )

        return super().dispatch(request, *args, **kwargs)


class BreadCrumbsMixin:
    """
    A mixin to help with the display of breadcrumbs via the TNA Breadcrumbs component.

    Usage:
    - Add BreadCrumbsMixin to your view class
    - Set ONE of the following attributes:
      - `breadcrumb`: A string for static breadcrumb text
      - `breadcrumb_field`: A string with the name of the object field to display

    Examples:
    1. Static: breadcrumb = "Projects"
    2. Dynamic: breadcrumb_field = "name"  # Will display the object's name attribute
    """

    def __init__(self) -> None:
        if not hasattr(self, "breadcrumb") and not hasattr(
            self, "breadcrumb_field"
        ):
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} requires either 'breadcrumb' or "
                "'breadcrumb_field' to be set, as it's using the BreadCrumbsMixin."
            )

        super().__init__()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["breadcrumbs"] = self._breadcrumb_calculator()
        return context

    def _breadcrumb_calculator(self):
        """
        Calculate the breadcrumbs from the url, from root to the parent of the current
        path.
        """
        # remove leading/trailing slashes and split, ignore empty segments
        parts = self.request.path.split("/")
        breadcrumbs = []
        parsed_url = ""

        # only go up to the parent (exclude the current page)
        for url_part in parts[:-2]:
            parsed_url += f"{url_part}/"
            resolved = self._breadcrumb_inner(parsed_url)
            if resolved:
                breadcrumbs.append(resolved)

        return breadcrumbs

    def _breadcrumb_inner(self, url):
        """
        Extract breadcrumb from a url
        """
        try:
            # extract relevant view class or function, from the url
            resolved = resolve(url)

            # check if it's a class-based view
            if hasattr(resolved.func, "view_class"):
                view_class = resolved.func.view_class
                # check if view class uses BreadCrumbsMixin
                if issubclass(view_class, BreadCrumbsMixin):
                    # handle dynamic object field lookup
                    if hasattr(view_class, "breadcrumb_field"):
                        field_name = view_class.breadcrumb_field
                        try:
                            # attempt to get the object based on URL kwargs
                            obj = self._get_object_for_breadcrumb(
                                view_class, resolved.kwargs, field_name
                            )
                            if obj and hasattr(obj, field_name):
                                text = getattr(obj, field_name)
                            else:
                                text = "Unknown"
                        except Exception:
                            text = "Unknown"
                    # handle static text
                    elif hasattr(view_class, "breadcrumb"):
                        text = view_class.breadcrumb
                    else:
                        return None

                    return {"href": url, "text": text}

            return None
        except Resolver404:
            return None

    def _get_object_for_breadcrumb(self, view_class, kwargs, field_name):
        """
        Get the object for a view class based on its kwargs.
        Uses a simple caching mechanism to prevent redundant queries.
        """
        # create a cache key based on view class and kwargs
        cache_key = f"{view_class.__name__}:{sorted(kwargs.items())}"

        # check if we've already cached this object
        if not hasattr(self, "_breadcrumb_object_cache"):
            self._breadcrumb_object_cache = {}

        if cache_key in self._breadcrumb_object_cache:
            return self._breadcrumb_object_cache[cache_key]

        # get the model and lookup fields from the view class
        model = getattr(view_class, "model", None)
        if not model:
            return None

        # find the lookup field (slug_field/slug_url_kwarg or pk)
        slug_field = getattr(view_class, "slug_field", "pk")
        slug_url_kwarg = getattr(view_class, "slug_url_kwarg", "pk")

        # get the lookup value from kwargs
        lookup_value = kwargs.get(slug_url_kwarg)
        if not lookup_value:
            return None

        # fetch the object
        try:
            lookup_kwargs = {slug_field: lookup_value}
            # Only fetch the field we need plus id
            obj = model.objects.only(field_name).get(**lookup_kwargs)
            # cache the result
            self._breadcrumb_object_cache[cache_key] = obj
            return obj
        except Exception:
            return None
