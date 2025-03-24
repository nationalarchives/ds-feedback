import contextlib
import logging

from django.db.models.base import ModelBase
from django.template.context import Context
from django.template.response import TemplateResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

from factory.django import DjangoModelFactory


def reverse_with_query(viewname: str, query: dict[str, str], *args, **kwargs):
    """
    Returns a reversed URL with query parameters
    """
    return reverse(viewname, *args, **kwargs) + "?" + urlencode(query)


def get_change_list_results(response: TemplateResponse):
    """
    Returns the change list results from a response
    """
    return list(response.context["cl"].result_list)


def get_inline_formset(context: Context, model_class: ModelBase):
    """
    Returns the inline formset for a given model
    """
    try:
        return next(
            (
                formset.formset
                for formset in context["inline_admin_formsets"]
                if formset.formset.model == model_class
            ),
        )
    except StopIteration:
        raise ValueError(f"Inline formset for {repr(model_class)} not found")


@contextlib.contextmanager
def ignore_request_warnings():
    """
    Ignores warnings from the Django request logger
    """

    logger = logging.getLogger("django.request")
    original_level = logger.getEffectiveLevel()
    logger.setLevel(logging.ERROR)

    try:
        yield
    finally:
        logger.setLevel(original_level)


class ResetFactorySequencesMixin(TestCase):
    """
    Mixin to reset all factory sequences
    """

    def setUp(cls):
        for factory_class in DjangoModelFactory.__subclasses__():
            factory_class.reset_sequence()
