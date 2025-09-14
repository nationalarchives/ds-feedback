from django.urls import path

from app.editor_ui.views.prompt_views import (
    RangedPromptOptionCreateView,
    RangedPromptOptionDeleteView,
    RangedPromptOptionUpdateView,
)

app_name = "options"

urlpatterns = [
    path(
        "create/",
        RangedPromptOptionCreateView.as_view(),
        name="create",
    ),
    path(
        "<uuid:option_uuid>/update/",
        RangedPromptOptionUpdateView.as_view(),
        name="update",
    ),
    path(
        "<uuid:option_uuid>/delete/",
        RangedPromptOptionDeleteView.as_view(),
        name="delete",
    ),
]
