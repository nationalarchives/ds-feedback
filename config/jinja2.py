import json
import re
from datetime import datetime

from django.conf import settings
from django.template.defaultfilters import date as dj_date
from django.template.defaultfilters import pluralize as dj_pluralize
from django.templatetags.static import static
from django.urls import reverse

from jinja2 import Environment
from markupsafe import Markup


def slugify(s):
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s


def now_iso_8601():
    now = datetime.now()
    now_date = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    return now_date


def jinja_url(name, *args, **kwargs):
    path = reverse(name, args=args, kwargs=kwargs)
    return Markup(path)


def jinja_date(value, format=None):
    if format is None:
        format = getattr(settings, "DATE_FORMAT", "N j, Y")
    return dj_date(value, format)


def dict_merge(a, b):
    merged = a.copy()
    merged.update(b)
    return merged


def environment(**options):
    env = Environment(**options)

    def is_active_url(url, request=None, exact=False):
        if not request:
            return False

        return request.path == url

    # Register Django filters/functions for use with Jinja backend
    env.filters["pluralize"] = dj_pluralize
    env.filters["date"] = jinja_date
    env.filters["dict_merge"] = dict_merge
    env.globals["is_active_url"] = is_active_url

    TNA_FRONTEND_VERSION = ""
    try:
        with open(
            "/app/node_modules/@nationalarchives/frontend/package.json",
        ) as package_json:
            try:
                data = json.load(package_json)
                TNA_FRONTEND_VERSION = data["version"] or ""
            except ValueError:
                pass
    except FileNotFoundError:
        pass

    env.globals.update(
        {
            "static": static,
            "app_config": {
                "GA4_ID": settings.GA4_ID,
                "TNA_FRONTEND_VERSION": TNA_FRONTEND_VERSION,
                "BUILD_VERSION": settings.BUILD_VERSION,
                "COOKIE_DOMAIN": settings.COOKIE_DOMAIN,
            },
            "url": jinja_url,
            "now_iso_8601": now_iso_8601,
        }
    )
    env.filters.update({"slugify": slugify})
    return env
