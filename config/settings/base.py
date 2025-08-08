import json
import os
from sysconfig import get_path

from django.core.exceptions import ImproperlyConfigured

import dj_database_url
from csp.constants import NONE, SELF

from config.util import strtobool

env = os.environ.copy()

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
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "csp",
    "app.api",
    "app.users",
    "app.main",
    "app.projects",
    "app.feedback_forms",
    "app.prompts",
    "app.responses",
    "app.editor_auth",
    "app.editor_ui",
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
            os.path.join(BASE_DIR, "app/editor_auth/templates"),
            os.path.join(BASE_DIR, "app/editor_ui/templates"),
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


def get_env_csp(env_name: str) -> list[str]:
    """
    Gets a CSP directive from an env variable
    """
    return os.environ.get(env_name, SELF).split(",")


def trim_default_directives(directives: dict[str, str]) -> dict[str, str]:
    """
    Remove directives that are the default value
    """
    return {
        directive: value
        for directive, value in directives.items()
        if directive == "default-src" or value != directives["default-src"]
    }


CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": trim_default_directives(
        {
            "default-src": [SELF],
            "base-uri": NONE,
            "object-src": NONE,
            "img-src": get_env_csp("CSP_IMG_SRC"),
            "script-src": get_env_csp("CSP_SCRIPT_SRC"),
            "script-src-elem": get_env_csp("CSP_SCRIPT_SRC_ELEM"),
            "style-src": get_env_csp("CSP_STYLE_SRC"),
            "style-src-elem": get_env_csp("CSP_STYLE_SRC_ELEM"),
            "font-src": get_env_csp("CSP_FONT_SRC"),
            "connect-src": get_env_csp("CSP_CONNECT_SRC"),
            "media-src": get_env_csp("CSP_MEDIA_SRC"),
            "worker-src": get_env_csp("CSP_WORKER_SRC"),
            "frame-src": get_env_csp("CSP_FRAME_SRC"),
        }
    )
}

GA4_ID = os.environ.get("GA4_ID", "")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "TNA Feedback API",
    "DESCRIPTION": "API to collect feedback from users of TNA services.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Email settings
# We use SMTP to send emails. We typically use transactional email services
# that let us use SMTP.
# https://docs.djangoproject.com/en/2.1/topics/email/

# https://docs.djangoproject.com/en/stable/ref/settings/#email-host
if "EMAIL_HOST" in env:
    EMAIL_HOST = env["EMAIL_HOST"]

# https://docs.djangoproject.com/en/stable/ref/settings/#email-port
# Use a default port of 587, as some services now block the Django default of 25
try:
    EMAIL_PORT = int(env.get("EMAIL_PORT", 587))
except ValueError:
    raise ImproperlyConfigured(
        "The setting EMAIL_PORT should be an integer, e.g. 587"
    ) from None

# https://docs.djangoproject.com/en/stable/ref/settings/#email-host-user
if "EMAIL_HOST_USER" in env:
    EMAIL_HOST_USER = env["EMAIL_HOST_USER"]

# https://docs.djangoproject.com/en/stable/ref/settings/#email-host-password
if "EMAIL_HOST_PASSWORD" in env:
    EMAIL_HOST_PASSWORD = env["EMAIL_HOST_PASSWORD"]

# https://docs.djangoproject.com/en/stable/ref/settings/#email-use-tls
# We always want to use TLS
EMAIL_USE_TLS = True

# https://docs.djangoproject.com/en/stable/ref/settings/#email-subject-prefix
if "EMAIL_SUBJECT_PREFIX" in env:
    EMAIL_SUBJECT_PREFIX = env["EMAIL_SUBJECT_PREFIX"]
