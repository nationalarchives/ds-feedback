from django.urls import path, re_path

from app.api.views import (
    FeedbackFormDetail,
    FeedbackFormList,
    FeedbackFormPathPatternDetail,
    PromptResponseCreate,
    PromptResponseDetail,
    PromptResponseList,
    ResponseCreate,
    ResponseDetail,
    ResponseList,
)

app_name = "api"

urlpatterns = [
    path(
        "core/projects/<uuid:project>/feedback-forms/",
        FeedbackFormList.as_view(),
        name="feedback-form_list",
    ),
    path(
        "core/projects/<uuid:project>/feedback-forms/<uuid:id>/",
        FeedbackFormDetail.as_view(),
        name="feedback-form_detail",
    ),
    re_path(
        # <path> always includes the leading slash,
        # and does not require an ending slash to avoid confusing double slashes
        r"^core/projects/(?P<project>[^\/]+)/feedback-forms/path(?P<path>/.*)$",
        FeedbackFormPathPatternDetail.as_view(),
        name="feedback-form-path_detail",
    ),
    path(
        "submit/responses/",
        ResponseCreate.as_view(),
        name="response_create",
    ),
    path(
        "submit/prompt-responses/",
        PromptResponseCreate.as_view(),
        name="prompt-response_create",
    ),
    path(
        "explore/responses/",
        ResponseList.as_view(),
        name="response_list",
    ),
    path(
        "explore/responses/<uuid:id>/",
        ResponseDetail.as_view(),
        name="response_detail",
    ),
    path(
        "explore/prompt-responses/",
        PromptResponseList.as_view(),
        name="prompt-response_list",
    ),
    path(
        "explore/prompt-responses/<uuid:id>/",
        PromptResponseDetail.as_view(),
        name="prompt-response_detail",
    ),
]
