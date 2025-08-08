from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import render
from django.views.generic import DetailView

from app.editor_ui.mixins import SuperuserRequiredMixin
from app.projects.models import Project


def index(request):
    return render(request, "editor_ui/index.html")


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
