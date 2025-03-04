from typing import Dict

from django.db.models.base import ModelBase
from django.http import HttpResponse
from django.template.context import Context
from django.urls import reverse
from django.utils.http import urlencode


def reverse_with_query(viewname: str, query: Dict[str, str], *args, **kwargs):
    """
    Returns a reversed URL with query parameters
    """
    return reverse(viewname, *args, **kwargs) + "?" + urlencode(query)


def get_change_list_results(response: HttpResponse):
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
        raise ValueError(f"Inline formset for {model_class} not found")
