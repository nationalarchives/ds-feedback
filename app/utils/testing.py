from typing import Dict

from django.db.models.base import ModelBase
from django.http import HttpResponse
from django.template.context import Context
from django.urls import reverse
from django.utils.http import urlencode


def reverse_with_query(name: str, query: Dict[str, str]):
    """
    Returns a reversed URL with query parameters
    """
    return reverse(name) + "?" + urlencode(query)


def get_change_list_results(response: HttpResponse):
    """
    Returns the change list results from a response
    """
    return list(response.context["cl"].result_list)


def get_inline_formset(context: Context, model_class: ModelBase):
    """
    Returns the inline formset for a given model
    """
    return next(
        (
            formset.formset
            for formset in context["inline_admin_formsets"]
            if formset.formset.model == model_class
        ),
    )
