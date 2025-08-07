from django.urls import path

from app.editor_ui.views import ProjectListView, index

urlpatterns = [
    path("", index, name="index"),
    path("projects/", ProjectListView.as_view(), name="project_list"),
]
