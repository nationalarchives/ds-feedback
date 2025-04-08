from django.urls import path

from app.api.views import (
    FeedbackFormDetail,
    FeedbackFormList,
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
