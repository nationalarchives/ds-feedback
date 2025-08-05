from django.contrib.auth.views import LoginView

from app.editor_auth.forms import CustomAuthenticationForm


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = "registration/login.html"
