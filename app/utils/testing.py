from django.urls import reverse
from django.utils.http import urlencode


def reverse_with_query(name, query):
    """
    Returns a reversed URL with query parameters
    """
    return reverse(name) + "?" + urlencode(query)


def get_change_list_results(response):
    """
    Returns the change list results from a response
    """
    return list(response.context["cl"].result_list)
