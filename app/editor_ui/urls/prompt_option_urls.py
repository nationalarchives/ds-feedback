from django.urls import path

from app.editor_ui.views.prompt_views import (
    RangedPromptOptionCreateView,
    RangedPromptOptionDeleteView,
    RangedPromptOptionUpdateView,
)

app_name = "options"

urlpatterns = [
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/prompts/<uuid:prompt_uuid>/ranged-prompt-options/create/",
        RangedPromptOptionCreateView.as_view(),
        name="create",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/prompts/<uuid:prompt_uuid>/options/<uuid:option_uuid>/update/",
        RangedPromptOptionUpdateView.as_view(),
        name="update",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/prompts/<uuid:prompt_uuid>/options/<uuid:option_uuid>/delete/",
        RangedPromptOptionDeleteView.as_view(),
        name="delete",
    ),
]
