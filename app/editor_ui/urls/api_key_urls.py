from django.urls import path

from app.editor_ui.views.api_key_views import ApiKeyListView, ApiKeyCreateView


app_name = "api_keys"

urlpatterns = [
    path("", ApiKeyListView.as_view(), name="list"),
    path("create/", ApiKeyCreateView.as_view(), name="create"),
]
