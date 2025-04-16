from django.db import transaction

from drf_spectacular.extensions import OpenApiSerializerExtension
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from app.feedback_forms.models import FeedbackForm
from app.prompts.models import (
    BinaryPrompt,
    Prompt,
    RangedPrompt,
    RangedPromptOption,
    TextPrompt,
)
from app.responses.models import (
    BinaryPromptResponse,
    PromptResponse,
    RangedPromptResponse,
    Response,
    TextPromptResponse,
)


class RangedPromptOptionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True, source="uuid")
    label = serializers.CharField(read_only=True)
    value = serializers.CharField(read_only=True)

    class Meta:
        model = RangedPromptOption
        fields = ["id", "label", "value"]


class PromptSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True, source="uuid")
    feedback_form = serializers.SlugRelatedField(
        slug_field="uuid", read_only=True
    )
    prompt_type = serializers.CharField(read_only=True, source="type")
    text = serializers.CharField(read_only=True)

    is_enabled = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Prompt
        fields = [
            "id",
            "feedback_form",
            "prompt_type",
            "text",
            "is_enabled",
            "created_at",
            "modified_at",
        ]

    @classmethod
    def get_subclass_from_prompt(cls, prompt: Prompt | type[Prompt]):
        """
        Gets the subclassed PromptSerializer for a Prompt
        """
        try:
            return next(
                (
                    Subclass
                    for Subclass in cls.__subclasses__()
                    if (
                        issubclass(prompt, Subclass.Meta.model)
                        if isinstance(prompt, type)
                        else isinstance(prompt, Subclass.Meta.model)
                    )
                ),
            )
        except StopIteration:
            raise ValueError(
                f"Could not find PromptSerializer subclass for {repr(prompt)}."
            )

    def to_representation(self, instance):
        """
        Returns to_representation() of the subclassed PromptSerializer
        """

        # On create, PromptResponse and Prompt aren't loaded as subclasses, so we fetch the subclasses
        if type(instance) is Prompt:
            instance = Prompt.objects.get_subclass(id=instance.id)

        if type(self) is PromptSerializer:
            PromptSerializerSubclass = self.get_subclass_from_prompt(instance)
            return PromptSerializerSubclass(instance).to_representation(
                instance
            )

        return super().to_representation(instance)


class TextPromptSerializer(PromptSerializer):
    max_length = serializers.JSONField(read_only=True)

    class Meta:
        model = TextPrompt
        fields = PromptSerializer.Meta.fields + ["max_length"]


class RangedPromptSerializer(PromptSerializer):
    options = RangedPromptOptionSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = RangedPrompt
        fields = PromptSerializer.Meta.fields + ["options"]


class BinaryPromptSerializer(PromptSerializer):
    positive_answer_label = serializers.CharField(read_only=True)
    negative_answer_label = serializers.CharField(read_only=True)

    class Meta:
        model = BinaryPrompt
        fields = PromptSerializer.Meta.fields + [
            "positive_answer_label",
            "negative_answer_label",
        ]


class FeedbackFormSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True, source="uuid")
    name = serializers.CharField(read_only=True)
    is_enabled = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)
    prompts = PromptSerializer(many=True, read_only=True)

    class Meta:
        model = FeedbackForm
        fields = [
            "id",
            "name",
            "is_enabled",
            "created_at",
            "modified_at",
            "prompts",
        ]


class PromptResponseSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True, source="uuid")
    created_at = serializers.DateTimeField(read_only=True)
    response = serializers.SlugRelatedField(
        queryset=Response.objects.all(), slug_field="uuid"
    )
    prompt = serializers.SlugRelatedField(
        queryset=Prompt.objects.all()
        .select_related("feedback_form")
        .select_subclasses(),
        slug_field="uuid",
    )

    class Meta:
        model = PromptResponse
        fields = ["id", "created_at", "prompt", "response"]

    @classmethod
    def get_subclass_from_prompt_response(
        cls, prompt_response: PromptResponse | type[PromptResponse]
    ):
        """
        Gets the subclassed PromptResponseSerialiser for a PromptResponse
        """
        try:
            return next(
                (
                    Subclass
                    for Subclass in cls.__subclasses__()
                    if (
                        issubclass(prompt_response, Subclass.Meta.model)
                        if isinstance(prompt_response, type)
                        else isinstance(prompt_response, Subclass.Meta.model)
                    )
                ),
            )
        except StopIteration:
            raise ValueError(
                f"Could not find PromptResponseSerializer subclass for {repr(prompt_response)}."
            )

    def to_representation(self, instance):
        """
        Calls to_representation() on the subclassed PromptResponseSerializer
        """

        # Propagate prefetched value to subclass instance.
        # This is needed because select_subclasses() doesn't play well with nested subclass relations
        if isinstance(instance, RangedPromptResponse):
            instance.value = instance.rangedpromptresponse.value

        # On create, PromptResponse and Prompt aren't loaded as subclasses, so we fetch the subclasses
        if type(instance) is PromptResponse:
            instance = PromptResponse.objects.get_subclass(id=instance.id)

        if type(self) is PromptResponseSerializer:
            PromptResponseSerializerSubclass = (
                self.get_subclass_from_prompt_response(instance)
            )
            return PromptResponseSerializerSubclass(instance).to_representation(
                instance
            )

        return super().to_representation(instance)

    def validate_prompt_response_prompt(self, data):
        """
        Validates that a PromptResponse doesn't already exist for this Prompt/Response
        """

        if "response" in data:
            prompt_response_exists = PromptResponse.objects.filter(
                response=data["response"], prompt=data["prompt"]
            ).exists()

            if prompt_response_exists:
                raise ValidationError(
                    {
                        "prompt": f"Prompt response already exists for prompt id={data["prompt"].uuid} and response id={data["response"].uuid}."
                    }
                )

    def validate_feedback_form_prompt(self, data):
        """
        Validates that the Prompt matches the FeedbackForm and is enabled
        """

        prompt = data["prompt"]

        if "response" in data:
            response = data["response"]

            if prompt.feedback_form_id != response.feedback_form_id:
                raise ValidationError(
                    {
                        "prompt": f"Prompt id={prompt.uuid} does not exist in feedback form id={response.feedback_form.uuid}."
                    }
                )

            if prompt.disabled_at is not None:
                raise ValidationError(
                    {
                        "prompt": f"Prompt id={prompt.uuid} is not enabled in feedback form id={response.feedback_form.uuid}."
                    }
                )

    def run_validation(self, data=empty):
        """
        Calls run_validation() on the subclassed PromptResponseSerializer
        """

        if type(self) is PromptResponseSerializer:
            if data is empty:
                raise ValidationError({"prompt": "This field is required."})

            # Unfortunately we need an extra query here to get the prompt to determine which serialiser to use
            prompt = Prompt.objects.get_subclass(uuid=data["prompt"])
            PromptResponseSubclass = PromptResponse.get_subclass_from_prompt(
                prompt
            )
            PromptResponseSerializerSubclass = (
                PromptResponseSerializer.get_subclass_from_prompt_response(
                    PromptResponseSubclass
                )
            )

            serializer_subclass = PromptResponseSerializerSubclass(data=data)
            serializer_subclass.fields["response"].required = self.fields[
                "response"
            ].required
            return serializer_subclass.run_validation(data)

        return super().run_validation(data)

    def validate(self, data):
        self.validate_prompt_response_prompt(data)
        self.validate_feedback_form_prompt(data)

        return data

    def create(self, validated_data):
        """
        Creates a PromptResponse with the appropriate subclass
        """
        prompt = validated_data["prompt"]
        PromptResponseSubclass = PromptResponse.get_subclass_from_prompt(prompt)
        return PromptResponseSubclass.objects.create(**validated_data)


class PromptResponseSerializerExtension(OpenApiSerializerExtension):
    """
    Adds a generic "value" field to the PromptResponseSerializer
    """

    target_class = PromptResponseSerializer

    def map_serializer(self, auto_schema, direction):
        schema = auto_schema._map_serializer(
            self.target_class, direction, bypass_extensions=True
        )
        # This is how we specify "any" type in OpenAPI
        schema["properties"]["value"] = {}
        return schema


class TextPromptResponseSerializer(PromptResponseSerializer):
    value = serializers.CharField()

    class Meta:
        model = TextPromptResponse
        fields = PromptResponseSerializer.Meta.fields + ["value"]

    def validate(self, data):
        if len(data["value"]) > data["prompt"].max_length:
            raise ValidationError(
                {
                    "value": f"Value must not be longer than {data['prompt'].max_length} characters."
                }
            )

        return super().validate(data)


class BinaryPromptResponseSerializer(PromptResponseSerializer):
    value = serializers.BooleanField()

    class Meta:
        model = BinaryPromptResponse
        fields = PromptResponseSerializer.Meta.fields + ["value"]


class RangedPromptResponseSerializer(PromptResponseSerializer):
    prompt = serializers.SlugRelatedField(
        queryset=Prompt.objects.all()
        .select_related("feedback_form")
        .prefetch_related("options")
        .select_subclasses(),
        slug_field="uuid",
    )
    value = serializers.SlugRelatedField(
        queryset=RangedPromptOption.objects.all(), slug_field="uuid"
    )

    class Meta:
        model = RangedPromptResponse
        fields = PromptResponseSerializer.Meta.fields + ["value"]

    def validate(self, data):
        if not next(
            (
                option
                for option in data["prompt"].options.all()
                if option == data["value"]
            ),
            None,
        ):
            raise ValidationError(
                {
                    "value": f"Value must be an option from prompt id={data['prompt'].uuid}."
                }
            )

        return super().validate(data)


class ResponseSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True, source="uuid")
    created_at = serializers.DateTimeField(read_only=True)
    feedback_form = serializers.SlugRelatedField(
        queryset=FeedbackForm.objects.all(), slug_field="uuid"
    )
    prompt_responses = PromptResponseSerializer(many=True, read_only=True)
    first_prompt_response = PromptResponseSerializer(write_only=True)

    class Meta:
        model = Response
        fields = [
            "id",
            "url",
            "created_at",
            "metadata",
            "feedback_form",
            "prompt_responses",
            "first_prompt_response",
        ]

    def validate(self, data):
        """
        Validates the selected Prompt is the first enabled Prompt in the FeedbackForm
        """

        prompt = data["first_prompt_response"]["prompt"]
        first_prompt = (
            Prompt.objects.order_by("order")
            .filter(feedback_form=data["feedback_form"], disabled_at=None)
            .first()
        )
        if prompt.id != first_prompt.id:
            raise ValidationError(
                {
                    "prompt": f"Prompt must be the first enabled prompt in the feedback form {data["feedback_form"].uuid}"
                }
            )

        return data

    def run_validation(self, data=empty):
        """
        Disables requirement for first_prompt_response.response, since this does not exist until save
        """
        self.fields["first_prompt_response"].fields["response"].required = False

        return super().run_validation(data)

    @transaction.atomic
    def create(self, validated_data):
        """
        Creates a Response and the first PromptResponse with the appropriate subclass
        """

        prompt_response_data = validated_data.pop("first_prompt_response")
        response = Response.objects.create(**validated_data)

        prompt = prompt_response_data["prompt"]
        PromptResponseSubclass = PromptResponse.get_subclass_from_prompt(prompt)
        PromptResponseSubclass.objects.create(
            response=response,
            **prompt_response_data,
        )
        return response
