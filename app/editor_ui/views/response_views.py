from django.views.generic import DetailView, ListView

from app.editor_ui.mixins import (
    BreadCrumbsMixin,
    ProjectMembershipRequiredMixin,
)


from app.projects.models import Project
from app.responses.models import Response


class ResponseListingView(
    ProjectMembershipRequiredMixin, BreadCrumbsMixin, ListView
):
    model = Response
    template_name = "editor_ui/responses/response_list.html"
    context_object_name = "responses"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["editor", "owner"]
    parent_model = Project
    parent_lookup_kwarg = "project_uuid"

    breadcrumb = "Responses"

    def get_queryset(self):
        return (
            Response.objects.all()
            .select_related("feedback_form")
            .filter(feedback_form__project__uuid=self.kwargs.get("project_uuid"))
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_uuid"] = self.kwargs.get("project_uuid")
        return context


class ResponseDetailView(
    ProjectMembershipRequiredMixin, BreadCrumbsMixin, DetailView
):
    model = Response
    template_name = "editor_ui/responses/response_detail.html"
    context_object_name = "response"
    slug_field = "uuid"
    slug_url_kwarg = "response_uuid"

    project_roles_required = ["editor", "owner"]
    parent_model = Project
    parent_lookup_kwarg = "project_uuid"

    breadcrumb = "Response Details"

    def get_queryset(self):
        return (
            Response.objects.all()
            .select_related("feedback_form")
            .prefetch_related("prompt_responses")
            .filter(feedback_form__project__uuid=self.kwargs.get("project_uuid"))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_uuid"] = self.kwargs.get("project_uuid")
        return context
