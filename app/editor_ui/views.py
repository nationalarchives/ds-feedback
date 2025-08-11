from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from app.editor_ui.forms import ProjectForm
from app.editor_ui.mixins import SuperuserRequiredMixin
from app.projects.models import Project


class ProjectCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "editor_ui/projects/project_create.html"
    # success_url = reverse_lazy("editor_ui:project_list")

    def form_valid(self, form):
        project_obj = form.save(commit=False)
        project_obj.owned_by = self.request.user
        project_obj.set_initial_created_by(user=self.request.user)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("editor_ui:project_detail", kwargs={"uuid": self.object.uuid})

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "editor_ui/projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        if self.request.user.is_superuser:
            qs = Project.objects.all()
        else:
            qs = Project.objects.filter(owned_by=self.request.user)
        return qs


class ProjectDetailView(LoginRequiredMixin, SuperuserRequiredMixin, DetailView):
    model = Project
    template_name = "editor_ui/projects/project_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        return (
            Project.objects.all()
            .select_related("owned_by")
            .annotate(
                forms_count=Count(
                    "feedback_forms",
                    filter=Q(feedback_forms__disabled_at=None),
                ),
                responses_count=Count(
                    "feedback_forms__responses",
                    filter=Q(feedback_forms__disabled_at=None),
                ),
                prompts_count=Count(
                    "feedback_forms__prompts",
                    filter=Q(
                        feedback_forms__disabled_at=None,
                        feedback_forms__prompts__disabled_at=None,
                    ),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        context["forms_count"] = project.forms_count
        context["responses_count"] = project.responses_count
        context["prompts_count"] = project.prompts_count

        return context
