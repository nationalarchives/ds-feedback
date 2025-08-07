from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView

from app.projects.models import Project


@login_required(login_url="/auth/login/")
def index(request):
    return render(request, "editor_ui/index.html")


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "editor_ui/projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        # TODO: Project member ship beyond an owner
        if self.request.user.is_superuser:
            qs = Project.objects.all()
        else:
            qs = Project.objects.filter(owned_by=self.request.user)
        return qs
