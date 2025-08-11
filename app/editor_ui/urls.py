from django.urls import path

from app.editor_ui.views import (
    ProjectCreateView,
    ProjectDetailView,
    ProjectListView,
)

app_name = "editor_ui"

urlpatterns = [
    path("projects/", ProjectListView.as_view(), name="project_list"),
    path(
        "projects/create/", ProjectCreateView.as_view(), name="project_create"
    ),
    path(
        "projects/<uuid:uuid>/",
        ProjectDetailView.as_view(),
        name="project_detail",
    ),
]
