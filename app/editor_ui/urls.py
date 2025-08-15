from django.urls import path

from app.editor_ui.views import (
    FeedbackFormCreateView,
    FeedbackFormDetailView,
    FeedbackFormListView,
    ProjectCreateView,
    ProjectDetailView,
    ProjectListView,
    PromptCreateView,
)

app_name = "editor_ui"

urlpatterns = [
    path("projects/", ProjectListView.as_view(), name="project_list"),
    path(
        "projects/create/", ProjectCreateView.as_view(), name="project_create"
    ),
    path(
        "projects/<uuid:uuid>/",
        ProjectDetailView.as_view(),
        name="project_detail",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/",
        FeedbackFormListView.as_view(),
        name="project__feedback_form_list",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/create/",
        FeedbackFormCreateView.as_view(),
        name="feedback_form_create",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/",
        FeedbackFormDetailView.as_view(),
        name="project__feedback_form_detail",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/prompts/create/",
        PromptCreateView.as_view(),
        name="project__feedback_form__prompt_create",
    ),
]
