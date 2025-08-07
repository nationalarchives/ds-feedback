from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import CreateView

from app.editor_ui.forms import ProjectForm
from app.editor_ui.mixins import SuperuserRequiredMixin
from app.projects.models import Project


def index(request):
    return render(request, "editor_ui/index.html")


class ProjectCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "editor_ui/projects/project_create.html"
    login_url = "/auth/login/"
    success_url = "/projects/"

    def form_valid(self, form):
        project_obj = form.save(commit=False)
        project_obj.owned_by = self.request.user
        project_obj.set_initial_created_by(user=self.request.user)

        return super().form_valid(form)
