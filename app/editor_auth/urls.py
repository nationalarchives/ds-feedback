from django.urls import path

from app.editor_auth.views import (
    CustomLoginView,
    CustomLogoutConfirmationView,
    CustomLogoutView,
    CustomPasswordResetCompleteView,
    CustomPasswordResetConfirmView,
    CustomPasswordResetDoneView,
    CustomResetPasswordView,
)

app_name = 'editor_auth'

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutConfirmationView.as_view(), name="logout"),
    path("logout_action/", CustomLogoutView.as_view(), name="logout_action"),
    path(
        "password_reset/",
        CustomResetPasswordView.as_view(),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        CustomPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
