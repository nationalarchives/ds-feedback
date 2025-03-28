from django.urls import path, re_path

from app.api.views import (
    FeedbackFormDetail,
    FeedbackFormPathPatternDetail,
    PromptList,
    PromptResponseDetail,
    PromptResponseListCreate,
    ResponseDetail,
    ResponseListCreate,
)

app_name = "api"

urlpatterns = [
    path(
        "projects/<str:project_id>/feedback-forms/<str:feedback_form_id>/",
        FeedbackFormDetail.as_view(),
        name="feedback-form_detail",
    ),
    re_path(
        r"^projects/(?P<project_id>[^\/]+)/feedback-forms/path/(?P<path>.+)/$",
        FeedbackFormPathPatternDetail.as_view(),
        name="feedback-form-path_detail",
    ),
    path(
        "projects/<str:project_id>/feedback-forms/<str:feedback_form_id>/prompts/",
        PromptList.as_view(),
        name="prompt_list",
    ),
    path(
        "projects/<str:project_id>/feedback-forms/<str:feedback_form_id>/responses/",
        ResponseListCreate.as_view(),
        name="response_list",
    ),
    path(
        "projects/<str:project_id>/feedback-forms/<str:feedback_form_id>/responses/<str:response_id>/",
        ResponseDetail.as_view(),
        name="response_detail",
    ),
    path(
        "projects/<str:project_id>/feedback-forms/<str:feedback_form_id>/responses/<str:response_id>/prompt-responses/",
        PromptResponseListCreate.as_view(),
        name="prompt-response_list",
    ),
    path(
        "projects/<str:project_id>/feedback-forms/<str:feedback_form_id>/responses/<str:response_id>/prompt-responses/<str:prompt_response_id>/",
        PromptResponseDetail.as_view(),
        name="prompt-response_detail",
    ),
]
