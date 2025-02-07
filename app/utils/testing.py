from django.urls import reverse
from django.utils.http import urlencode


def reverse_with_query(name, query):
    """
    Returns a reversed URL with query parameters
    """
    return reverse(name) + "?" + urlencode(query)
