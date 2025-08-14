from django.contrib.auth.mixins import UserPassesTestMixin


class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser


class OwnedByUserMixin:
    """
    A mixin that automatically sets the owned_by field to the current user.
    This should be used with CreateView classes where the model has an owned_by field.
    """

    def form_valid(self, form):
        form.instance.owned_by = self.request.user
        # If the model has a set_initial_created_by method, call it
        if hasattr(form.instance, "set_initial_created_by"):
            form.instance.set_initial_created_by(user=self.request.user)
        return super().form_valid(form)
