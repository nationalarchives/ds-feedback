import json
import re
from datetime import datetime

from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment


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


def environment(**options):
    env = Environment(**options)

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
            "url": reverse,
            "now_iso_8601": now_iso_8601,
        }
    )
    env.filters.update({"slugify": slugify})
    return env
