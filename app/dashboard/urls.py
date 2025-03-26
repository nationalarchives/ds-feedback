from django.urls import path


from .views import projects

urlpatterns = [
    path("projects/", projects.projects_index, name="projects_index"),
]