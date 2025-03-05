from typing import Type

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

    @staticmethod
    def get_subclass_by_name(name: str):
        """
        Returns a Prompt subclass by its name
        """
        return PROMPT_TYPES[name]

    def __str__(self):
        return self.text

    @classmethod
    def type(cls):
        return cls.__name__


class TextPrompt(Prompt):
    max_length = models.PositiveSmallIntegerField(default=1000)

    def spec(self):
        return {
            "max_length": self.max_length,
        }


class BinaryPrompt(Prompt):
    positive_answer_label = models.CharField(max_length=64, default="Yes")
    negative_answer_label = models.CharField(max_length=64, default="No")

    def get_label(self, answer: bool) -> str:
        """
        Returns the label given a positive or negative answer
        """
        return (
            self.positive_answer_label if answer else self.negative_answer_label
        )

    def spec(self):
        return {
            "positive_answer_label": self.positive_answer_label,
            "negative_answer_label": self.negative_answer_label,
        }


class RangedPrompt(Prompt):
    def spec(self):
        return {"options": [option.spec() for option in self.options.all()]}


class RangedPromptOption(UUIDModel):
    ranged_prompt = models.ForeignKey(
        RangedPrompt, on_delete=models.CASCADE, related_name="options"
    )
    label = models.CharField(max_length=64)
    value = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.label

    def spec(self):
        return {"label": self.label, "value": self.value}


PROMPT_TYPES: dict[str, Type[Prompt]] = {
    PromptType.__name__: PromptType
    for PromptType in [TextPrompt, BinaryPrompt, RangedPrompt]
}
