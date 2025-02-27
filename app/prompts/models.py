from django.db import models

from model_utils.managers import InheritanceManager

from app.feedback_forms.models import FeedbackForm
from app.utils.models import (
    CreatedByModel,
    DisableableModel,
    Specialisable,
    TimestampedModel,
    UUIDModel,
)


class Prompt(
    TimestampedModel, UUIDModel, CreatedByModel, DisableableModel, Specialisable
):
    objects = InheritanceManager()

    text = models.CharField(max_length=128)
    feedback_form = models.ForeignKey(
        FeedbackForm, on_delete=models.CASCADE, related_name="prompts"
    )
    order = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.text


class TextPrompt(Prompt):
    max_length = models.PositiveSmallIntegerField(default=1000)


class BinaryPrompt(Prompt):
    positive_answer_label = models.CharField(max_length=64, default="Yes")
    negative_answer_label = models.CharField(max_length=64, default="No")


class RangedPrompt(Prompt):
    pass


class RangedPromptOption(models.Model):
    ranged_prompt = models.ForeignKey(
        RangedPrompt, on_delete=models.CASCADE, related_name="options"
    )
    label = models.CharField(max_length=64)
    value = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.label
