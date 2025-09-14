from django.urls import path

from app.editor_ui.views.membership_views import (
    ProjectMembershipCreateView,
    ProjectMembershipDeleteView,
    ProjectMembershipListView,
    ProjectMembershipUpdateView,
)

app_name = "memberships"

urlpatterns = [
    path(
        "",
        ProjectMembershipListView.as_view(),
        name="list",
    ),
    path(
        "create/",
        ProjectMembershipCreateView.as_view(),
        name="create",
    ),
    path(
        "<uuid:membership_uuid>/update/",
        ProjectMembershipUpdateView.as_view(),
        name="update",
    ),
    path(
        "<uuid:membership_uuid>/delete/",
        ProjectMembershipDeleteView.as_view(),
        name="delete",
    ),
]
