import os

from .features import *
from .production import *
from .production import BASE_DIR, INSTALLED_APPS

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = INSTALLED_APPS + ["test"]

ENVIRONMENT = "test"

SECRET_KEY = "abc123"

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
