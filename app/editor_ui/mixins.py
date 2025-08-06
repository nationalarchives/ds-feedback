from django.contrib.auth.mixins import UserPassesTestMixin


class AdminPrivRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser
