from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from app.editor_auth.forms import (
    CustomAuthenticationForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
)


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = "registration/login.html"
    next_page = reverse_lazy("index")


class CustomLogoutConfirmationView(TemplateView):
    template_name = "registration/logout_confirmation.html"


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("index")


class CustomResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = "registration/password_reset_form.html"
    form_class = CustomPasswordResetForm
    email_template_name = "registration/password_reset_email.html"
    subject_template_name = "registration/password_reset_subject.txt"
    success_message = (
        "A link to reset your password has been emailed to you "
        "if an account exists for this address."
    )
    success_url = reverse_lazy("password_reset_done")


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "registration/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "registration/password_reset_complete.html"
