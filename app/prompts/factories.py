from factory import Sequence
from factory.django import DjangoModelFactory

from .models import (
    BinaryPrompt,
    Prompt,
    RangedPrompt,
    RangedPromptOption,
    TextPrompt,
)


class PromptFactory(DjangoModelFactory):
    order = Sequence(lambda i: i)

    class Meta:
        model = Prompt


class TextPromptFactory(PromptFactory):
    class Meta:
        model = TextPrompt


class BinaryPromptFactory(PromptFactory):
    class Meta:
        model = BinaryPrompt


class RangedPromptFactory(PromptFactory):
    class Meta:
        model = RangedPrompt


class RangedPromptOptionFactory(DjangoModelFactory):
    class Meta:
        model = RangedPromptOption

    value = Sequence(lambda i: i)
