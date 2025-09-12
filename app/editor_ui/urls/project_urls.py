from django.urls import include, path

from app.editor_ui.views.membership_views import (
    ProjectMembershipCreateView,
    ProjectMembershipDeleteView,
    ProjectMembershipListView,
    ProjectMembershipUpdateView,
)
from app.editor_ui.views.project_views import (
    ProjectCreateView,
    ProjectDetailView,
    ProjectListView,
    ProjectUpdateView,
)

app_name = "projects"

urlpatterns = [
    path(
        "create/",
        ProjectCreateView.as_view(),
        name="create",
    ),
    path(
        "",
        ProjectListView.as_view(),
        name="list",
    ),
    path(
        "<uuid:project_uuid>/",
        ProjectDetailView.as_view(),
        name="detail",
    ),
    path(
        "<uuid:project_uuid>/edit/",
        ProjectUpdateView.as_view(),
        name="update",
    ),
    path(
        "feedback-forms/",
        include(
            "app.editor_ui.urls.feedback_form_urls", namespace="feedback_forms"
        ),
    ),
    path(
        "responses/",
        include("app.editor_ui.urls.response_urls", namespace="responses"),
    ),
    path(
        "members/",
        include(
            "app.editor_ui.urls.project_membership_urls",
            namespace="memberships",
        ),
    ),
]
