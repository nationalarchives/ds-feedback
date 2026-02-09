import os

from config.util import strtobool

from .features import *  # noqa: F403
from .production import *  # noqa: F403

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

DEBUG = strtobool(os.getenv("DEBUG", "False"))


# Display sent emails in the console while developing locally.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

if DEBUG:
    # Adds Django Silk
    MIDDLEWARE.insert(0, "silk.middleware.SilkyMiddleware")  # noqa
    INSTALLED_APPS.append("silk")  # noqa

    try:
        INSTALLED_APPS += [  # noqa: F405
            "debug_toolbar",
        ]

        MIDDLEWARE = [
            "debug_toolbar.middleware.DebugToolbarMiddleware",
        ] + MIDDLEWARE  # noqa: F405

        DEBUG_TOOLBAR_CONFIG = {
            "SHOW_TOOLBAR_CALLBACK": lambda request: True,
            "SHOW_COLLAPSED": True,
        }
    except ImportError:
        pass
