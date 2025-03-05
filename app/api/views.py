from django.db import transaction
from django.db.models import Prefetch
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import generics, serializers
from rest_framework.exceptions import NotFound

from app.feedback_forms.models import FeedbackForm
from app.prompts.models import Prompt
from app.responses.models import PromptResponse, Response


class PromptSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="uuid")
    type = serializers.CharField(read_only=True)

    class Meta:
        model = Prompt
        fields = ["id", "type", "text"]


class PromptResponseSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="uuid")
    prompt = PromptSerializer(read_only=True)
    prompt_id = serializers.SlugRelatedField(
        queryset=Prompt.objects.all(), slug_field="uuid", write_only=True
    )
    answer = serializers.JSONField(read_only=True, source="answer_json")

    class Meta:
        model = PromptResponse
        fields = ["id", "prompt", "prompt_id", "answer"]


class ResponseSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="uuid")
    feedback_form = serializers.SlugRelatedField(
        queryset=FeedbackForm.objects.all(), slug_field="uuid"
    )
    prompt_responses = PromptResponseSerializer(many=True, read_only=True)
    initial_prompt_response = PromptResponseSerializer(write_only=True)

    class Meta:
        model = Response
        fields = [
            "id",
            "url",
            "metadata",
            "feedback_form",
            "prompt_responses",
            "initial_prompt_response",
        ]

    @transaction.atomic
    def create(self, validated_data):
        prompt_response_data = validated_data.pop("initial_prompt_response")
        response = Response.objects.create(**validated_data)
        PromptResponse.objects.create(
            response=response,
            prompt=prompt_response_data.pop("prompt_id"),
            **prompt_response_data,
        )
        return response


@method_decorator(csrf_exempt, name="dispatch")
class ResponseList(generics.ListCreateAPIView):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer

    def get_queryset(self):
        return (
            self.queryset.filter(
                feedback_form__uuid=self.kwargs.get("feedback_form_id"),
                feedback_form__project__uuid=self.kwargs.get("project_id"),
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
                "prompt_responses__rangedpromptresponse__value",
            )
        )

    def create(self, request, *args, **kwargs):
        try:
            FeedbackForm.objects.filter(
                uuid=kwargs["feedback_form_id"],
                project__uuid=kwargs["project_id"],
            ).exists()
        except FeedbackForm.DoesNotExist:
            raise NotFound(
                f"Feedback form id={kwargs["feedback_form_id"]} does not exist in project id={kwargs["project_id"]}"
            )

        request.data["feedback_form"] = kwargs["feedback_form_id"]
        return super().create(request, *args, **kwargs)


@method_decorator(csrf_exempt, name="dispatch")
class ResponseDetail(generics.RetrieveAPIView):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer

    def get_object(self):
        return generics.get_object_or_404(
            self.get_queryset(),
            uuid=self.kwargs.get("response_id"),
            feedback_form__uuid=self.kwargs.get("feedback_form_id"),
            feedback_form__project__uuid=self.kwargs.get("project_id"),
        )


# {
#   "url": "https://some-domain.com/then/some/path",
#   "metadata": {
#     "theme": "dark",
#     "custom-parameter": ["Custom value A", "Custom value B"],
#     "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0"
#   },
#   "first_prompt_response": {
#     "prompt_id": "8f9f5ac6-2aa7-4fa1-a51d-21c87d917f3b",
#     "value": "Yes"
#   }
# }


# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework.exceptions import NotFound

# class MyView(APIView):
#     def get(self, request, pk):
#         # Manually validate if the pk exists in the database
#         try:
#             item = MyModel.objects.get(pk=pk)
#         except MyModel.DoesNotExist:
#             raise NotFound("Item with the given ID does not exist.")

#         return Response({"message": "Item found!", "item": item.id})
