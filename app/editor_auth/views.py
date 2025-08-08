from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from app.editor_auth.forms import CustomAuthenticationForm


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = "registration/login.html"
    next_page = reverse_lazy("index")


class CustomLogoutConfirmationView(TemplateView):
    template_name = "registration/logout_confirmation.html"


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("index")
