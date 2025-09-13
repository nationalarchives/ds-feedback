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
        "projects/<uuid:project_uuid>/feedback-forms/",
        FeedbackFormListView.as_view(),
        name="list",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/create/",
        FeedbackFormCreateView.as_view(),
        name="create",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/update/",
        FeedbackFormUpdateView.as_view(),
        name="update",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/",
        FeedbackFormDetailView.as_view(),
        name="detail",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/delete/",
        FeedbackFormDeleteView.as_view(),
        name="delete",
    ),
    path(
        "path-pattern/",
        include(
            "app.editor_ui.urls.path_pattern_urls", namespace="path_patterns"
        ),
    ),
    path(
        "prompts/",
        include("app.editor_ui.urls.prompt_urls", namespace="prompts"),
    ),
]
