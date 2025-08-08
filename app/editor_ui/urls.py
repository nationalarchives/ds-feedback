from django.urls import path

from app.editor_ui.views import ProjectDetailView, ProjectListView, index

urlpatterns = [
    path("", index, name="index"),
    path(
        "projects/<uuid:uuid>/",
        ProjectDetailView.as_view(),
        name="project_detail",
    ),
    path("projects/", ProjectListView.as_view(), name="project_list"),
]
