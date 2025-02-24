import json
import os
from sysconfig import get_path

import dj_database_url

from config.util import strtobool

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")
USE_X_FORWARDED_HOST = strtobool(os.getenv("USE_X_FORWARDED_HOST", "False"))

AUTH_USER_MODEL = "users.User"

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "csp",
    "app.users",
    "app.main",
    "app.projects",
    "app.feedback_form",
    "app.prompts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [
            os.path.join(BASE_DIR, "app/templates"),
            os.path.join(get_path("platlib"), "tna_frontend_jinja/templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "config.jinja2.environment",
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# Using dj-database-url for the temporary Heroku dev environment
DATABASES = {"default": dj_database_url.config(conn_max_age=600)}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "app/static")]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Logging
# https://docs.djangoproject.com/en/stable/topics/logging/
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        # Send logs with at least INFO level to the console.
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s][%(process)d][%(levelname)s][%(name)s] %(message)s"
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "app": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "config": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


# TNA Configuration

ENVIRONMENT: str = os.environ.get("ENVIRONMENT", "production")

BUILD_VERSION: str = os.environ.get("BUILD_VERSION", "")
TNA_FRONTEND_VERSION: str = ""
try:
    with open(
        os.path.join(
            os.path.realpath(os.path.dirname(__file__)),
            "node_modules/@nationalarchives/frontend",
            "package.json",
        )
    ) as package_json:
        try:
            data = json.load(package_json)
            TNA_FRONTEND_VERSION = data["version"] or ""
        except ValueError:
            pass
except FileNotFoundError:
    pass

SECRET_KEY: str = os.environ.get("SECRET_KEY", "")

DEBUG: bool = strtobool(os.getenv("DEBUG", "False"))

COOKIE_DOMAIN: str = os.environ.get("COOKIE_DOMAIN", "")

if "CSRF_TRUSTED_ORIGINS" in os.environ:
    CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")

CSP_IMG_SRC: list[str] = os.environ.get("CSP_IMG_SRC", "'self'").split(",")
CSP_SCRIPT_SRC: list[str] = os.environ.get("CSP_SCRIPT_SRC", "'self'").split(
    ","
)
CSP_SCRIPT_SRC_ELEM: list[str] = os.environ.get(
    "CSP_SCRIPT_SRC_ELEM", "'self'"
).split(",")
CSP_STYLE_SRC: list[str] = os.environ.get("CSP_STYLE_SRC", "'self'").split(",")
CSP_STYLE_SRC_ELEM: list[str] = os.environ.get(
    "CSP_STYLE_SRC_ELEM", "'self'"
).split(",")
CSP_FONT_SRC: list[str] = os.environ.get("CSP_FONT_SRC", "'self'").split(",")
CSP_CONNECT_SRC: list[str] = os.environ.get("CSP_CONNECT_SRC", "'self'").split(
    ","
)
CSP_MEDIA_SRC: list[str] = os.environ.get("CSP_MEDIA_SRC", "'self'").split(",")
CSP_WORKER_SRC: list[str] = os.environ.get("CSP_WORKER_SRC", "'self'").split(
    ","
)
CSP_FRAME_SRC: list[str] = os.environ.get("CSP_FRAME_SRC", "'self'").split(",")

CSP_SELF = "'self'"
CSP_NONE = "'none'"
CONTENT_SECURITY_POLICY = (
    {
        "DIRECTIVES": {
            "default-src": CSP_SELF,
            "base-uri": CSP_NONE,
            "object-src": CSP_NONE,
            **({"img-src": CSP_IMG_SRC} if CSP_IMG_SRC != [CSP_SELF] else {}),
            **(
                {"script-src": CSP_SCRIPT_SRC}
                if CSP_SCRIPT_SRC != [CSP_SELF]
                else {}
            ),
            **(
                {"script-src-elem": CSP_SCRIPT_SRC_ELEM}
                if CSP_SCRIPT_SRC_ELEM != [CSP_SELF]
                else {}
            ),
            **(
                {"style-src": CSP_STYLE_SRC}
                if CSP_STYLE_SRC != [CSP_SELF]
                else {}
            ),
            **(
                {"font-src": CSP_FONT_SRC} if CSP_FONT_SRC != [CSP_SELF] else {}
            ),
            **(
                {"connect-src": CSP_CONNECT_SRC}
                if CSP_CONNECT_SRC != [CSP_SELF]
                else {}
            ),
            **(
                {"media-src": CSP_MEDIA_SRC}
                if CSP_MEDIA_SRC != [CSP_SELF]
                else {}
            ),
            **(
                {"worker-src": CSP_WORKER_SRC}
                if CSP_WORKER_SRC != [CSP_SELF]
                else {}
            ),
            **(
                {"frame-src": CSP_FRAME_SRC}
                if CSP_FRAME_SRC != [CSP_SELF]
                else {}
            ),
        }
    },
)

GA4_ID = os.environ.get("GA4_ID", "")
