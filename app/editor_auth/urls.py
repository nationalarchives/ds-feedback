from django.urls import path

from app.editor_auth.views import CustomLoginView

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
]
