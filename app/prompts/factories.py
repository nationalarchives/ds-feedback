from factory import Sequence
from factory.django import DjangoModelFactory

from .models import BinaryPrompt, RangedPrompt, RangedPromptOption, TextPrompt


class TextPromptFactory(DjangoModelFactory):
    class Meta:
        model = TextPrompt

    order = Sequence(lambda i: i)


class BinaryPromptFactory(DjangoModelFactory):
    class Meta:
        model = BinaryPrompt

    order = Sequence(lambda i: i)


class RangedPromptFactory(DjangoModelFactory):
    class Meta:
        model = RangedPrompt

    order = Sequence(lambda i: i)


class RangedPromptOptionFactory(DjangoModelFactory):
    class Meta:
        model = RangedPromptOption

    value = Sequence(lambda i: i)
