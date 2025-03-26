from collections.abc import Iterable

from django.template.defaulttags import querystring


def querystring(query, query_dict=None, **kwargs):
    if query_dict is None:
        query_dict = request.GET
    params = query_dict.copy()
    for key, value in kwargs.items():
        if value is None:
            if key in params:
                del params[key]
        elif isinstance(value, Iterable) and not isinstance(value, str):
            params.setlist(key, value)
        else:
            params[key] = value
    if not params and not query_dict:
        return ""
    query_string = params.urlencode()
    return f"?{query_string}"

def pagination_context(*, url, page):

    context = {}
    if page.has_next():
        context["next"] = {
            "href": querystring()
        }
    if page.has_previous():
        context["previous"] = {
            "href": path + "?page=" + str(page.previous_page_number())
        }
    return context
