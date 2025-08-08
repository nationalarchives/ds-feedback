from django.urls import path

from app.editor_auth.views import (
    CustomLoginView,
    CustomLogoutConfirmationView,
    CustomLogoutView,
)

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutConfirmationView.as_view(), name="logout"),
    path("logout_action/", CustomLogoutView.as_view(), name="logout_action"),
]
