from django.urls import include, path

from app.editor_ui.views.feedback_form_views import (
    FeedbackFormCreateView,
    FeedbackFormDeleteView,
    FeedbackFormDetailView,
    FeedbackFormListView,
    FeedbackFormUpdateView,
)

app_name = "feedback_forms"

urlpatterns = [
    path(
        "",
        FeedbackFormListView.as_view(),
        name="list",
    ),
    path(
        "create/",
        FeedbackFormCreateView.as_view(),
        name="create",
    ),
    path(
        "<uuid:feedback_form_uuid>/update/",
        FeedbackFormUpdateView.as_view(),
        name="update",
    ),
    path(
        "<uuid:feedback_form_uuid>/",
        FeedbackFormDetailView.as_view(),
        name="detail",
    ),
    path(
        "<uuid:feedback_form_uuid>/delete/",
        FeedbackFormDeleteView.as_view(),
        name="delete",
    ),
    path(
        "<uuid:feedback_form_uuid>/path-patterns/",
        include(
            "app.editor_ui.urls.path_pattern_urls", namespace="path_patterns"
        ),
    ),
    path(
        "<uuid:feedback_form_uuid>/prompts/",
        include("app.editor_ui.urls.prompt_urls", namespace="prompts"),
    ),
]
