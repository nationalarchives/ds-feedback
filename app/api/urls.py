from django.urls import path, re_path

from csp.constants import SELF, UNSAFE_INLINE
from csp.decorators import csp_update
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

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
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "schema/swagger/",
        csp_update(
            {
                "img-src": [SELF, "cdn.jsdelivr.net", "data:"],
                "style-src-elem": ["cdn.jsdelivr.net", UNSAFE_INLINE],
                "script-src": [SELF, "cdn.jsdelivr.net", UNSAFE_INLINE],
            }
        )(SpectacularSwaggerView.as_view(url_name="api:schema")),
        name="schema_swagger",
    ),
]
