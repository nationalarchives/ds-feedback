from django.urls import include, path

from app.editor_ui.views.prompt_views import (
    PromptCreateView,
    PromptDeleteView,
    PromptDetailView,
    PromptUpdateView,
)

app_name = "prompts"

urlpatterns = [
    path(
        "add/",
        PromptCreateView.as_view(),
        name="create",
    ),
    path(
        "<uuid:prompt_uuid>/",
        PromptDetailView.as_view(),
        name="detail",
    ),
    path(
        "<uuid:prompt_uuid>/edit/",
        PromptUpdateView.as_view(),
        name="update",
    ),
    path(
        "<uuid:prompt_uuid>/delete/",
        PromptDeleteView.as_view(),
        name="delete",
    ),
    path(
        "<uuid:prompt_uuid>/options/",
        include("app.editor_ui.urls.prompt_option_urls", namespace="options"),
    ),
]
