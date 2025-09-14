from django.urls import path

from app.editor_ui.views.path_pattern_views import (
    PathPatternCreateView,
    PathPatternDeleteView,
    PathPatternUpdateView,
)

app_name = "path_patterns"

urlpatterns = [
    path(
        "create/",
        PathPatternCreateView.as_view(),
        name="create",
    ),
    path(
        "<uuid:path_pattern_uuid>/update/",
        PathPatternUpdateView.as_view(),
        name="update",
    ),
    path(
        "<uuid:path_pattern_uuid>/delete/",
        PathPatternDeleteView.as_view(),
        name="delete",
    ),
]
