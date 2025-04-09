from functools import cache

from django.db.models import F, Prefetch, Q, Value
from django.db.models.functions import Length

from rest_framework import generics, views
from rest_framework.exceptions import NotFound, PermissionDenied

from app.api import acl
from app.api.models import APIRole
from app.api.serializers import (
    FeedbackFormSerializer,
    PromptResponseSerializer,
    ResponseSerializer,
)
from app.feedback_forms.models import FeedbackForm
from app.projects.models import Project
from app.prompts.models import Prompt
from app.responses.models import PromptResponse, Response
from app.utils.views import is_valid_uuid


class CheckProjectAccessMixin(views.APIView):
    """
    Mixin to check if the user has access with one of allowed_roles.
    If get_project() is defined, this will check access to that specific project,
    otherwise it will check access to at least one project.
    """

    allowed_roles: list[APIRole]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        if not hasattr(self, "allowed_roles"):
            raise NotImplementedError(
                "CheckProjectAccessMixin requires self.allowed_roles to be defined as a list of APIRoles."
            )

        if hasattr(self, "get_project"):
            if not acl.can_access_project_with_role(
                user=request.user,
                project=self.get_project(request.data),
                allowed_roles=self.allowed_roles,
            ):
                raise PermissionDenied()
        else:
            if not acl.can_access_any_project_with_role(
                user=request.user,
                allowed_roles=self.allowed_roles,
            ):
                raise PermissionDenied()


class FilterParamMixin:
    def filter_queryset_param(self, queryset, filter_param: str, param: str):
        """
        Filters a queryset based on a query param
        """
        if param in self.request.query_params:
            queryset = queryset.filter(
                **{filter_param: self.request.query_params[param]}
            )

        return queryset


class ValidateUUIDMixin:
    def validate_uuid_param(self, query_params: dict[str, str], param: str):
        """
        Validates a query param is a valid UUID
        """
        if param in query_params:
            if not is_valid_uuid(query_params[param]):
                raise NotFound(
                    f"{param}={query_params[param]} is not a valid UUID."
                )


class FeedbackFormDetail(generics.RetrieveAPIView, CheckProjectAccessMixin):
    queryset = FeedbackForm.objects.all()
    serializer_class = FeedbackFormSerializer
    allowed_roles = [APIRole.SUBMIT_RESPONSES, APIRole.EXPLORE_RESPONSES]

    def get_queryset(self):
        return (
            self.queryset.filter(
                project__uuid=self.kwargs["project"], uuid=self.kwargs["id"]
            )
            .select_related("project")
            .prefetch_related(
                Prefetch(
                    "prompts",
                    queryset=Prompt.objects.select_subclasses(),
                ),
            )
        )

    def get_object(self):
        return generics.get_object_or_404(self.get_queryset())

    def get_project(self, data: dict[str, str]) -> Project:
        return generics.get_object_or_404(
            Project.objects.filter(uuid=self.kwargs["project"])
        )


class FeedbackFormList(
    generics.ListAPIView,
    ValidateUUIDMixin,
    FilterParamMixin,
    CheckProjectAccessMixin,
):
    queryset = FeedbackForm.objects.all()
    serializer_class = FeedbackFormSerializer
    allowed_roles = [APIRole.SUBMIT_RESPONSES, APIRole.EXPLORE_RESPONSES]

    def get_queryset(self):
        return (
            self.queryset.filter(project__uuid=self.kwargs["project"])
            .order_by("name")
            .prefetch_related(
                Prefetch(
                    "prompts",
                    queryset=Prompt.objects.select_subclasses().select_related(
                        "feedback_form"
                    ),
                ),
            )
        )

    def get_project(self, data: dict[str, str]) -> Project:
        return generics.get_object_or_404(
            Project.objects.filter(uuid=self.kwargs["project"])
        )


class FeedbackFormPathPatternDetail(
    generics.RetrieveAPIView, CheckProjectAccessMixin
):
    queryset = FeedbackForm.objects.all()
    serializer_class = FeedbackFormSerializer
    allowed_roles = [APIRole.SUBMIT_RESPONSES, APIRole.EXPLORE_RESPONSES]

    def get_queryset(self):
        return (
            self.queryset.alias(path=Value(self.kwargs["path"]))
            .filter(
                (
                    Q(path_patterns__pattern=self.kwargs["path"])
                    & Q(path_patterns__is_wildcard=False)
                )
                | (
                    Q(path__istartswith=F("path_patterns__pattern"))
                    & Q(path_patterns__is_wildcard=True)
                ),
                project__uuid=self.kwargs["project"],
                disabled_at=None,
            )
            .order_by(
                "path_patterns__is_wildcard",
                Length("path_patterns__pattern").desc(),
            )
            .prefetch_related(
                Prefetch(
                    "prompts",
                    queryset=Prompt.objects.select_subclasses(),
                ),
            )[:1]
        )

    def get_object(self):
        return generics.get_object_or_404(self.get_queryset())

    def get_project(self, data: dict[str, str]) -> Project:
        return generics.get_object_or_404(
            Project.objects.filter(uuid=self.kwargs["project"])
        )


class ResponseCreate(generics.CreateAPIView, CheckProjectAccessMixin):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer
    allowed_roles = [APIRole.SUBMIT_RESPONSES]

    def get_queryset(self):
        queryset = self.queryset.select_related(
            "feedback_form"
        ).prefetch_related(
            Prefetch(
                "prompt_responses",
                queryset=PromptResponse.objects.select_subclasses().prefetch_related(
                    "rangedpromptresponse__value"
                ),
            ),
            Prefetch(
                "prompt_responses__prompt",
                queryset=Prompt.objects.select_subclasses(),
            ),
        )

        return queryset

    def get_project(self, data: dict[str, str]) -> Project:
        feedback_form = generics.get_object_or_404(
            FeedbackForm.objects.filter(
                uuid=data["feedback_form"]
            ).select_related("project")
        )
        return feedback_form.project

    def validate_feedback_form_enabled(self, data: dict[str, str]):
        if "feedback_form" in data:
            feedback_form_query = FeedbackForm.objects.filter(
                uuid=data["feedback_form"], disabled_at=None
            )

            if not feedback_form_query.exists():
                raise NotFound(
                    f"Feedback form id={data["feedback_form"]} is disabled.",
                )

    def create(self, request, *args, **kwargs):
        self.validate_feedback_form_enabled(request.data)
        return super().create(request, *args, **kwargs)


class PromptResponseCreate(generics.CreateAPIView, CheckProjectAccessMixin):
    queryset = PromptResponse.objects.all()
    serializer_class = PromptResponseSerializer
    allowed_roles = [APIRole.SUBMIT_RESPONSES]

    def get_queryset(self):
        return self.queryset.select_subclasses().prefetch_related(
            "rangedpromptresponse__value",
            Prefetch(
                "prompt",
                queryset=Prompt.objects.select_subclasses(),
            ),
        )

    def get_project(self, data: dict[str, str]) -> Project:
        response = generics.get_object_or_404(
            Response.objects.filter(uuid=data["response"]).select_related(
                "feedback_form__project"
            )
        )
        return response.feedback_form.project

    def validate_feedback_form_enabled(self, data: dict[str, str]):
        if "response" in data:
            feedback_form_query = FeedbackForm.objects.filter(
                responses__uuid=data["response"], disabled_at=None
            )

            if not feedback_form_query.exists():
                raise NotFound(
                    f"Feedback form id={data["response"]} is disabled.",
                )

    def create(self, request, *args, **kwargs):
        self.validate_feedback_form_enabled(request.data)
        return super().create(request, *args, **kwargs)


class ResponseList(
    generics.ListAPIView,
    ValidateUUIDMixin,
    FilterParamMixin,
    CheckProjectAccessMixin,
):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer
    allowed_roles = [APIRole.EXPLORE_RESPONSES]

    def get_queryset(self):
        queryset = self.queryset.select_related(
            "feedback_form"
        ).prefetch_related(
            Prefetch(
                "prompt_responses",
                queryset=PromptResponse.objects.select_subclasses().prefetch_related(
                    "rangedpromptresponse__value",
                ),
            ),
            Prefetch(
                "prompt_responses__prompt",
                queryset=Prompt.objects.select_subclasses(),
            ),
        )

        if not self.request.user.is_superuser:
            allowed_projects = acl.get_accessible_projects_with_role(
                user=self.request.user, allowed_roles=self.allowed_roles
            )
            queryset = queryset.filter(
                feedback_form__project__in=allowed_projects
            )

        queryset = self.filter_queryset_param(
            queryset, "feedback_form__project__uuid", "project"
        )
        queryset = self.filter_queryset_param(
            queryset, "feedback_form__uuid", "feedback_form"
        )

        return queryset

    def list(self, request, *args, **kwargs):
        self.validate_uuid_param(request.query_params, "project")
        self.validate_uuid_param(request.query_params, "feedback_form")

        return super().list(request, *args, **kwargs)


class ResponseDetail(generics.RetrieveAPIView, CheckProjectAccessMixin):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer
    allowed_roles = [APIRole.EXPLORE_RESPONSES]

    def get_queryset(self):
        return (
            self.queryset.filter(uuid=self.kwargs["id"])
            .select_related("feedback_form__project")
            .prefetch_related(
                Prefetch(
                    "prompt_responses",
                    queryset=PromptResponse.objects.select_subclasses(),
                ),
                Prefetch(
                    "prompt_responses__prompt",
                    queryset=Prompt.objects.select_subclasses(),
                ),
            )
        )

    # Cache allows the project access check to use the same query as the get
    @cache
    def get_object(self):
        return generics.get_object_or_404(self.get_queryset())

    def get_project(self, data: dict[str, str]) -> Project:
        response = self.get_object()
        return response.feedback_form.project


class PromptResponseList(
    generics.ListAPIView,
    ValidateUUIDMixin,
    FilterParamMixin,
    CheckProjectAccessMixin,
):
    queryset = PromptResponse.objects.all()
    serializer_class = PromptResponseSerializer
    allowed_roles = [APIRole.EXPLORE_RESPONSES]

    def get_queryset(self):
        queryset = self.queryset.select_subclasses().prefetch_related(
            "response",
            "rangedpromptresponse__value",
            Prefetch("prompt", queryset=Prompt.objects.select_subclasses()),
        )

        if not self.request.user.is_superuser:
            allowed_projects = acl.get_accessible_projects_with_role(
                user=self.request.user, allowed_roles=self.allowed_roles
            )
            queryset = queryset.filter(
                response__feedback_form__project__in=allowed_projects
            )

        queryset = self.filter_queryset_param(
            queryset, "response__feedback_form__project__uuid", "project"
        )
        queryset = self.filter_queryset_param(
            queryset, "response__feedback_form__uuid", "feedback_form"
        )
        queryset = self.filter_queryset_param(
            queryset, "prompt__uuid", "prompt"
        )
        return queryset

    def list(self, request, *args, **kwargs):
        self.validate_uuid_param(request.query_params, "project")
        self.validate_uuid_param(request.query_params, "feedback_form")
        self.validate_uuid_param(request.query_params, "prompt")

        return super().list(request, *args, **kwargs)


class PromptResponseDetail(generics.RetrieveAPIView, CheckProjectAccessMixin):
    queryset = PromptResponse.objects.all()
    serializer_class = PromptResponseSerializer
    allowed_roles = [APIRole.EXPLORE_RESPONSES]

    def get_queryset(self):
        return (
            self.queryset.filter(uuid=self.kwargs["id"])
            .select_subclasses()
            .select_related("response__feedback_form__project")
            .prefetch_related(
                "rangedpromptresponse__value",
                Prefetch("prompt", queryset=Prompt.objects.select_subclasses()),
            )
        )

    # Cache allows the project access check to use the same query as the get
    @cache
    def get_object(self):
        return generics.get_object_or_404(self.get_queryset())

    def get_project(self, data: dict[str, str]) -> Project:
        prompt_response = self.get_object()
        return prompt_response.response.feedback_form.project
