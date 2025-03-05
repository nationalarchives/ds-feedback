from typing import Type

from django.db import models

from model_utils.managers import InheritanceManager

from app.feedback_forms.models import FeedbackForm
from app.prompts.models import (
    BinaryPrompt,
    Prompt,
    RangedPrompt,
    RangedPromptOption,
    TextPrompt,
)
from app.utils.models import TimestampedModel, UUIDModel


class Response(TimestampedModel, UUIDModel):
    feedback_form = models.ForeignKey(
        FeedbackForm, on_delete=models.PROTECT, related_name="+"
    )
    url = models.TextField()
    metadata = models.JSONField()

    def __str__(self):
        return self.url


class PromptResponse(TimestampedModel, UUIDModel):
    objects = InheritanceManager()

    response = models.ForeignKey(
        Response, on_delete=models.PROTECT, related_name="prompt_responses"
    )
    prompt = models.ForeignKey(
        Prompt, on_delete=models.PROTECT, related_name="+"
    )

    def get_subclass_prompt(self) -> Prompt:
        """
        Gets the subclassed prompt based on the subclassed prompt response
        """
        PromptType = PROMPT_RESPONSE_MAPPING[type(self)]
        return PromptType.objects.get(id=self.prompt.id)

    def __str__(self):
        return str(self.uuid)


class TextPromptResponse(PromptResponse):
    value = models.TextField()

    def answer(self) -> str:
        """
        Returns the response text
        """
        return self.value

    def answer_json(self):
        return self.value

    def __str__(self):
        return "Text prompt"


class BinaryPromptResponse(PromptResponse):
    value = models.BooleanField()

    def answer(self) -> str:
        """
        Returns the selected binary label
        """
        return BinaryPrompt.objects.get(id=self.prompt_id).get_label(self.value)

    def answer_json(self):
        return self.value

    def __str__(self):
        return "Binary prompt"


class RangedPromptResponse(PromptResponse):
    value = models.ForeignKey(
        RangedPromptOption, on_delete=models.PROTECT, related_name="+"
    )

    def answer(self) -> str:
        """
        Returns the selected option label
        """
        return self.value.label

    def answer_json(self):
        # If prefetched RangedPromptResponse exists, use that instead
        if hasattr(self, "rangedpromptresponse"):
            return self.rangedpromptresponse.value.uuid

        return self.value.uuid

    def __str__(self):
        return "Ranged prompt"


PROMPT_RESPONSE_MAPPING: dict[Type[PromptResponse], Type[Prompt]] = {
    TextPromptResponse: TextPrompt,
    BinaryPromptResponse: BinaryPrompt,
    RangedPromptResponse: RangedPrompt,
}
