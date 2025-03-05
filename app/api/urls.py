from django.urls import path

from app.api.views import ResponseDetail, ResponseList

urlpatterns = [
    path(
        "projects/<str:project_id>/feedback-forms/<str:feedback_form_id>/responses/",
        ResponseList.as_view(),
    ),
    path(
        "projects/<str:project_id>/feedback-forms/<str:feedback_form_id>/responses/<str:response_id>/",
        ResponseDetail.as_view(),
    ),
]
