from factory.django import DjangoModelFactory

from .models import (
    BinaryPromptResponse,
    RangedPromptResponse,
    Response,
    TextPromptResponse,
)


class ResponseFactory(DjangoModelFactory):
    class Meta:
        model = Response

    metadata = {}


class TextPromptResponseFactory(DjangoModelFactory):
    class Meta:
        model = TextPromptResponse


class BinaryPromptResponseFactory(DjangoModelFactory):
    class Meta:
        model = BinaryPromptResponse


class RangedPromptResponseFactory(DjangoModelFactory):
    class Meta:
        model = RangedPromptResponse
