from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from rest_framework.authtoken.models import Token

from app.editor_ui.mixins import BreadCrumbsMixin
from app.editor_ui.views.base_views import CustomCreateView


class ApiKeyListView(LoginRequiredMixin, BreadCrumbsMixin, ListView):
    """
    A view to show the API key associated with the user.
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


class ApiKeyCreateView(LoginRequiredMixin, BreadCrumbsMixin, CustomCreateView):
    """
    A view to confirm whether the user would like to create a API Key for their use.
    """

    model = Token
    fields = []
    template_name = "editor_ui/user/api_key_create.html"
    success_url = reverse_lazy("editor_ui:api_keys:list")

    model_display_name = "API key"

    breadcrumb = "Create API key"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["has_existing_token"] = Token.objects.filter(
            user=self.request.user
        ).exists()
        return context

    def form_valid(self, form):
        existing_token = Token.objects.filter(user=self.request.user).first()
        if existing_token:
            existing_token.delete()

        self.object = Token.objects.create(user=self.request.user)
        return HttpResponseRedirect(self.get_success_url())
