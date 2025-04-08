from django.db import models
from django.db.models import UniqueConstraint

from model_utils.managers import InheritanceManager

from app.feedback_forms.models import FeedbackForm
from app.prompts.models import (
    BinaryPrompt,
    Prompt,
    RangedPrompt,
    RangedPromptOption,
    TextPrompt,
)
from app.utils.models import (
    GetSubclassesModelMixin,
    TimestampedModelMixin,
    UUIDModelMixin,
)


class Response(TimestampedModelMixin, UUIDModelMixin):
    feedback_form = models.ForeignKey(
        FeedbackForm, on_delete=models.PROTECT, related_name="responses"
    )
    url = models.TextField()
    metadata = models.JSONField()

    def __str__(self):
        return self.url


class PromptResponse(
    TimestampedModelMixin, UUIDModelMixin, GetSubclassesModelMixin
):
    objects = InheritanceManager()
    prompt_type = Prompt

    response = models.ForeignKey(
        Response, on_delete=models.PROTECT, related_name="prompt_responses"
    )
    prompt = models.ForeignKey(
        Prompt, on_delete=models.PROTECT, related_name="+"
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                "response",
                "prompt",
                name="unique_response_prompt",
                violation_error_message="You cannot submit the same prompt twice for a response.",
            )
        ]

    def get_subclassed_prompt(self) -> Prompt:
        """
        Ensures we have the subclassed prompt using the prompt_type field
        """

        if type(self.prompt) is Prompt:
            self.prompt = self.prompt_type.objects.get(id=self.prompt_id)

        return self.prompt

    @classmethod
    def get_subclass_from_prompt(cls, prompt: Prompt):
        """
        Gets the subclassed PromptResponse for a Prompt
        """
        subclasses = cls.get_subclasses_mapping().values()
        try:
            return next(
                (
                    subclass
                    for subclass in subclasses
                    if isinstance(prompt, subclass.prompt_type)
                ),
            )
        except StopIteration:
            raise ValueError(
                f"Could not find PromptResponse subclass for {repr(prompt)}"
            )

    def __str__(self):
        return str(self.uuid)


class TextPromptResponse(PromptResponse):
    prompt_type = TextPrompt

    value = models.TextField()

    def answer(self) -> str:
        """
        Returns the response text
        """
        return self.value

    def __str__(self):
        return "Text prompt"


class BinaryPromptResponse(PromptResponse):
    prompt_type = BinaryPrompt

    value = models.BooleanField()

    def answer(self) -> str:
        """
        Returns the selected binary label
        """
        return self.get_subclassed_prompt().get_label(self.value)

    def __str__(self):
        return "Binary prompt"


class RangedPromptResponse(PromptResponse):
    prompt_type = RangedPrompt

    value = models.ForeignKey(
        RangedPromptOption, on_delete=models.PROTECT, related_name="+"
    )

    def answer(self) -> str:
        """
        Returns the selected option label
        """
        return self.value.label

    def __str__(self):
        return "Ranged prompt"
