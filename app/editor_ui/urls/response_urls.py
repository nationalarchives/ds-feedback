from django.urls import path

from app.editor_ui.views.response_views import (
    ResponseDetailView,
    ResponseListingView,
)

app_name = "responses"

urlpatterns = [
    path(
        "",
        ResponseListingView.as_view(),
        name="list",
    ),
    path(
        "<uuid:response_uuid>/",
        ResponseDetailView.as_view(),
        name="detail",
    ),
]
