from django.urls import path

from app.editor_ui.views.feedback_form_views import (
    FeedbackFormCreateView,
    FeedbackFormDetailView,
    FeedbackFormListView,
    FeedbackFormUpdateView,
)
from app.editor_ui.views.membership_views import (
    ProjectMembershipCreateView,
    ProjectMembershipDeleteView,
    ProjectMembershipListView,
    ProjectMembershipUpdateView,
)
from app.editor_ui.views.path_pattern_views import (
    PathPatternCreateView,
    PathPatternUpdateView,
)
from app.editor_ui.views.project_views import (
    ProjectCreateView,
    ProjectDetailView,
    ProjectListView,
    ProjectUpdateView,
)
from app.editor_ui.views.prompt_views import (
    PromptCreateView,
    PromptDetailView,
    PromptUpdateView,
    RangedPromptOptionCreateView,
    RangedPromptOptionUpdateView,
)

from app.editor_ui.views.response_views import (
    ResponseListingView,
    ResponseDetailView,
)

app_name = "editor_ui"

urlpatterns = [
    path("projects/", ProjectListView.as_view(), name="project_list"),
    path(
        "projects/create/", ProjectCreateView.as_view(), name="project_create"
    ),
    path(
        "projects/<uuid:project_uuid>/",
        ProjectDetailView.as_view(),
        name="project_detail",
    ),
    path(
        "projects/<uuid:project_uuid>/edit/",
        ProjectUpdateView.as_view(),
        name="project_update",
    ),
    path(
        "projects/<uuid:project_uuid>/members",
        ProjectMembershipListView.as_view(),
        name="project__memberships",
    ),
    path(
        "projects/<uuid:project_uuid>/members/add/",
        ProjectMembershipCreateView.as_view(),
        name="project__memberships_add",
    ),
    path(
        "projects/<uuid:project_uuid>/members/<uuid:membership_uuid>/edit/",
        ProjectMembershipUpdateView.as_view(),
        name="project__memberships_edit",
    ),
    path(
        "projects/<uuid:project_uuid>/members/<uuid:membership_uuid>/delete/",
        ProjectMembershipDeleteView.as_view(),
        name="project__memberships_delete",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/",
        FeedbackFormListView.as_view(),
        name="project__feedback_form_list",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/create/",
        FeedbackFormCreateView.as_view(),
        name="project__feedback_form_create",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/edit/",
        FeedbackFormUpdateView.as_view(),
        name="project__feedback_form_edit",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/",
        FeedbackFormDetailView.as_view(),
        name="project__feedback_form_detail",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/path-pattern/create/",
        PathPatternCreateView.as_view(),
        name="project__feedback_form__path_pattern_create",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/path-pattern/<uuid:path_pattern_uuid>/edit/",
        PathPatternUpdateView.as_view(),
        name="project__feedback_form__path_pattern_edit",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/prompts/create/",
        PromptCreateView.as_view(),
        name="project__feedback_form__prompt_create",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/prompts/<uuid:prompt_uuid>/",
        PromptDetailView.as_view(),
        name="project__feedback_form__prompt_detail",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/prompts/<uuid:prompt_uuid>/edit/",
        PromptUpdateView.as_view(),
        name="project__feedback_form__prompt_edit",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/prompts/<uuid:prompt_uuid>/ranged-prompt-options/create/",
        RangedPromptOptionCreateView.as_view(),
        name="project__feedback_form__prompt__ranged_prompt_options_create",
    ),
    path(
        "projects/<uuid:project_uuid>/feedback-forms/<uuid:feedback_form_uuid>/prompts/<uuid:prompt_uuid>/options/<uuid:option_uuid>/edit/",
        RangedPromptOptionUpdateView.as_view(),
        name="project__feedback_form__prompt__ranged_prompt_options_edit",
    ),
    path(
        "projects/<uuid:project_uuid>/responses/",
        ResponseListingView.as_view(),
        name="project__response_list",
    ),
    path(
        "projects/<uuid:project_uuid>/responses/<uuid:response_uuid>/",
        ResponseDetailView.as_view(),
        name="project__response_list",
    ),
]
