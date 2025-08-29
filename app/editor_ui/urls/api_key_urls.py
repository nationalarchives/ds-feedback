from django.urls import path

from app.editor_ui.views.api_key_views import ApiKeyDetailView


app_name = "api_keys"

urlpatterns = [
    path("", ApiKeyDetailView.as_view(), name="list"),
]
