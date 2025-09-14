import os

import dj_database_url

from .base import *
from .base import BASE_DIR, INSTALLED_APPS
from .features import *

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = INSTALLED_APPS + ["test"]

ENVIRONMENT = "test"

SECRET_KEY = "abc123"

DEBUG = True

DATABASES = {
    "default": dj_database_url.config(conn_max_age=600)
    or {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
