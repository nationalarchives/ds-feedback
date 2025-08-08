from django.urls import path

from app.editor_ui.views import ProjectCreateView, index

urlpatterns = [
    path("", index, name="index"),
    path(
        "projects/create/", ProjectCreateView.as_view(), name="project_create"
    ),
]
