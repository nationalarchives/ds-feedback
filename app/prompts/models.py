from django.db import models

from model_utils.managers import InheritanceManager

from app.feedback_forms.models import FeedbackForm
from app.utils.models import (
    CreatedByModelMixin,
    CreateSubclassModelMixin,
    DisableableModelMixin,
    GetSubclassesModelMixin,
    TimestampedModelMixin,
    UUIDModelMixin,
)


class Prompt(
    TimestampedModelMixin,
    UUIDModelMixin,
    CreatedByModelMixin,
    DisableableModelMixin,
    GetSubclassesModelMixin,
    CreateSubclassModelMixin,
):
    objects = InheritanceManager()
    field_label = "Prompt"

    text = models.CharField(max_length=128)
    feedback_form = models.ForeignKey(
        FeedbackForm, on_delete=models.CASCADE, related_name="prompts"
    )
    order = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.text


class TextPrompt(Prompt):
    field_label = "Text Prompt"

    max_length = models.PositiveSmallIntegerField(default=1000)


class BinaryPrompt(Prompt):
    field_label = "Binary Prompt"

    positive_answer_label = models.CharField(max_length=64, default="Yes")
    negative_answer_label = models.CharField(max_length=64, default="No")

    def get_label(self, answer: bool) -> str:
        """
        Returns the label given a positive or negative answer
        """
        return (
            self.positive_answer_label if answer else self.negative_answer_label
        )


class RangedPrompt(Prompt):
    field_label = "Ranged Prompt"


class RangedPromptOption(models.Model):
    ranged_prompt = models.ForeignKey(
        RangedPrompt, on_delete=models.CASCADE, related_name="options"
    )
    label = models.CharField(max_length=64)
    value = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.label
