from django.urls import path

from app.editor_ui.views.path_pattern_views import (
    PathPatternCreateView,
    PathPatternDeleteView,
    PathPatternUpdateView,
)

app_name = "path_patterns"

urlpatterns = [
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/path-pattern/create/",
        PathPatternCreateView.as_view(),
        name="create",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/path-pattern/<uuid:path_pattern_uuid>/update/",
        PathPatternUpdateView.as_view(),
        name="update",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/path-pattern/<uuid:path_pattern_uuid>/delete/",
        PathPatternDeleteView.as_view(),
        name="delete",
    ),
]
