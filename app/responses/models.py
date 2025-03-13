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
from app.utils.models import TimestampedModelMixin, UUIDModelMixin


class Response(TimestampedModelMixin, UUIDModelMixin):
    feedback_form = models.ForeignKey(
        FeedbackForm, on_delete=models.PROTECT, related_name="+"
    )
    url = models.TextField()
    metadata = models.JSONField()

    def __str__(self):
        return self.url


class PromptResponse(TimestampedModelMixin, UUIDModelMixin):
    objects = InheritanceManager()
    prompt_type = Prompt

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
        if not isinstance(self.prompt, self.prompt_type):
            self.prompt = self.prompt_type.objects.get(id=self.prompt_id)

        return self.prompt

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
        return self.get_subclass_prompt().get_label(self.value)

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
