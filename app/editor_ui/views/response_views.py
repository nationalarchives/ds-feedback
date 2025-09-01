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
    template_name = "todo"  # TODO: add template
    context_object_name = "responses"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["editor", "owner"]
    parent_model = Project
    parent_lookup_kwarg = "project_uuid"

    breadcrumb = "Responses"


class ResponseDetailView(
    ProjectMembershipRequiredMixin, BreadCrumbsMixin, DetailView
):
    model = Response
    template_name = "todo"  # TODO: add template
    context_object_name = "response"
    slug_field = "uuid"
    slug_url_kwarg = "response_uuid"

    project_roles_required = ["editor", "owner"]
    parent_model = Project
    parent_lookup_kwarg = "project_uuid"

    breadcrumb = "Responses"
