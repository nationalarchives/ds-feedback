from django.urls import path

from app.editor_ui.views import ProjectDetailView, index

urlpatterns = [
    path("", index, name="index"),
    path(
        "projects/<uuid:uuid>/",
        ProjectDetailView.as_view(),
        name="project_detail",
    ),
]
