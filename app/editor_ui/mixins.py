from django.contrib.auth.mixins import UserPassesTestMixin

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
        instance.owned_by = (
            self.request.user
        )  # Temp set project owner until auth implementation
        instance.created_by = self.request.user

        return super().form_valid(form)


class ProjectOwnerMembershipMixin:
    """
    Mixin to automatically create a ProjectMembership for the user as the project owner
    when a Project is created (unless the user is a superuser).
    """

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        instance = self.object

        if isinstance(instance, Project) and not user.is_superuser:
            ProjectMembership.objects.get_or_create(
                user=user,
                project=instance,
                defaults={"role": "owner"},
            )

        return response
