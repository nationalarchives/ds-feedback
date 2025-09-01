from django.urls import path

from app.editor_ui.views.api_access_views import APIAccessListView


app_name = "api_access"

urlpatterns = [
    path(
        "",
        APIAccessListView.as_view(),
        name="list",
    ),
]
