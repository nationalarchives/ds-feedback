from django.db.models import Prefetch

from rest_framework import generics
from rest_framework.exceptions import NotFound

from app.api.serializers import (
    FeedbackFormSerializer,
    PromptResponseSerializer,
    PromptSerializer,
    ResponseSerializer,
)
from app.feedback_forms.models import FeedbackForm
from app.prompts.models import Prompt
from app.responses.models import PromptResponse, Response


class ValidateFeedbackFormMixin:
    def validate_feedback_form_exists(
        self, url_params: dict[str, str], ensure_enabled=False
    ):
        """
        Validates the FeedbackForm exists (and optionally is enabled) in the Project
        """

        feedback_form_query = FeedbackForm.objects.filter(
            uuid=url_params["feedback_form_id"],
            project__uuid=url_params["project_id"],
        )

        if ensure_enabled:
            feedback_form_query = feedback_form_query.filter(disabled_at=None)

        if not feedback_form_query.exists():
            raise NotFound(
                " ".join(
                    [
                        f"Feedback form id={url_params["feedback_form_id"]} does not exist",
                        *(["or is disabled"] if ensure_enabled else []),
                        f"in project id={url_params["project_id"]}.",
                    ]
                )
            )


class ValidateResponseMixin:
    def validate_response_exists(self, url_params: dict[str, str]):
        """
        Validates the Response exists for the FeedbackForm
        """

        response_exists = Response.objects.filter(
            uuid=url_params["response_id"],
            feedback_form__uuid=url_params["feedback_form_id"],
        ).exists()

        if not response_exists:
            raise NotFound(
                f"Response id={url_params["response_id"]} does not exist in feedback form id={url_params["feedback_form_id"]}."
            )


class FeedbackFormDetail(generics.RetrieveAPIView):
    queryset = FeedbackForm.objects.all()
    serializer_class = FeedbackFormSerializer

    def get_queryset(self):
        return self.queryset.filter(
            uuid=self.kwargs["feedback_form_id"],
            project__uuid=self.kwargs["project_id"],
        ).prefetch_related(
            Prefetch(
                "prompts",
                queryset=Prompt.objects.select_subclasses(),
            ),
        )

    def get_object(self):
        return generics.get_object_or_404(self.get_queryset())


class PromptList(generics.ListAPIView, ValidateFeedbackFormMixin):
    queryset = Prompt.objects.all()
    serializer_class = PromptSerializer

    def get_queryset(self):
        return (
            self.queryset.filter(
                feedback_form__uuid=self.kwargs["feedback_form_id"],
            )
            .order_by("order")
            .select_subclasses()
        )

    def get(self, request, *args, **kwargs):
        self.validate_feedback_form_exists(kwargs)
        return super().get(request, *args, **kwargs)


class ResponseListCreate(generics.ListCreateAPIView, ValidateFeedbackFormMixin):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer

    def get_queryset(self):
        return (
            self.queryset.filter(
                feedback_form__uuid=self.kwargs["feedback_form_id"]
            )
            .select_related("feedback_form")
            .prefetch_related(
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
        )

    def create(self, request, *args, **kwargs):
        self.validate_feedback_form_exists(kwargs, ensure_enabled=True)

        request.data["feedback_form"] = kwargs["feedback_form_id"]
        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        self.validate_feedback_form_exists(kwargs)
        return super().list(request, *args, **kwargs)


class ResponseDetail(generics.RetrieveAPIView, ValidateFeedbackFormMixin):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer

    def get_queryset(self):
        return (
            self.queryset.filter(uuid=self.kwargs["response_id"])
            .select_related("feedback_form")
            .prefetch_related(
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
        )

    def get_object(self):
        return generics.get_object_or_404(self.get_queryset())

    def get(self, request, *args, **kwargs):
        self.validate_feedback_form_exists(kwargs)
        return super().get(request, *args, **kwargs)


class PromptResponseListCreate(
    generics.ListCreateAPIView, ValidateFeedbackFormMixin, ValidateResponseMixin
):
    queryset = PromptResponse.objects.all()
    serializer_class = PromptResponseSerializer

    def get_queryset(self):
        return (
            self.queryset.filter(response__uuid=self.kwargs["response_id"])
            .select_subclasses()
            .prefetch_related(
                "rangedpromptresponse__value",
                Prefetch(
                    "prompt",
                    queryset=Prompt.objects.select_subclasses(),
                ),
            )
        )

    def create(self, request, *args, **kwargs):
        self.validate_feedback_form_exists(kwargs, ensure_enabled=True)
        self.validate_response_exists(kwargs)

        request.data["response_id"] = kwargs["response_id"]
        request.data["feedback_form_id"] = kwargs["feedback_form_id"]
        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        self.validate_feedback_form_exists(kwargs)
        self.validate_response_exists(kwargs)

        return super().list(request, *args, **kwargs)


class PromptResponseDetail(
    generics.RetrieveAPIView, ValidateFeedbackFormMixin, ValidateResponseMixin
):
    queryset = PromptResponse.objects.all()
    serializer_class = PromptResponseSerializer

    def get_queryset(self):
        return (
            self.queryset.filter(uuid=self.kwargs["prompt_response_id"])
            .select_subclasses()
            .prefetch_related(
                "rangedpromptresponse__value",
                Prefetch(
                    "prompt",
                    queryset=Prompt.objects.select_subclasses(),
                ),
            )
        )

    def get_object(self):
        return generics.get_object_or_404(self.get_queryset())

    def get(self, request, *args, **kwargs):
        self.validate_feedback_form_exists(kwargs)
        self.validate_response_exists(kwargs)

        return super().get(request, *args, **kwargs)
