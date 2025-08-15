from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser


class OwnedByUserMixin:
    """
    Mixin to automatically set ownership fields on model instances created via a form.

    - Sets `owned_by` and `created_by` fields to the current user before saving.
    - Intended for use with Django class-based views.
    """

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.owned_by = self.request.user
        instance.created_by = self.request.user

        return super().form_valid(form)
