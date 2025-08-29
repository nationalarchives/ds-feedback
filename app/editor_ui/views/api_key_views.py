from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from rest_framework.authtoken.models import Token

from app.editor_ui.mixins import BreadCrumbsMixin


class ApiKeyDetailView(LoginRequiredMixin, BreadCrumbsMixin, ListView):
    """
    A view to list the API keys associated with the user.
    API keys are represented in the Token model from django rest framework.
    """

    model = Token
    context_object_name = "tokens"
    template_name = "editor_ui/user/api_key_list.html"

    breadcrumb = "API Key"

    def get_queryset(self):
        """
        Get only the Token that the user has access to
        """
        return super().get_queryset().filter(user=self.request.user)
