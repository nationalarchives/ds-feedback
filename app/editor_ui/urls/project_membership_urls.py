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
        "<uuid:project_uuid>/members/create/",
        ProjectMembershipCreateView.as_view(),
        name="create",
    ),
    path(
        "<uuid:project_uuid>/members/",
        ProjectMembershipListView.as_view(),
        name="list",
    ),
    path(
        "<uuid:project_uuid>/members/<uuid:membership_uuid>/update/",
        ProjectMembershipUpdateView.as_view(),
        name="update",
    ),
    path(
        "<uuid:project_uuid>/members/<uuid:membership_uuid>/delete/",
        ProjectMembershipDeleteView.as_view(),
        name="delete",
    ),
]
