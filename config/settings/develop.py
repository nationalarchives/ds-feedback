import os

from tna_utilities import strtobool

from .features import *
from .production import *

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# Display sent emails in the console while developing locally.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEBUG = strtobool(os.getenv("DEBUG", "False"))

if DEBUG:
    # Adds Django Silk
    # MIDDLEWARE.insert(0, "silk.middleware.SilkyMiddleware")
    # INSTALLED_APPS.append("silk")

    try:
        import debug_toolbar  # noqa: F401

        INSTALLED_APPS += [
            "debug_toolbar",
        ]

        MIDDLEWARE = [
            "debug_toolbar.middleware.DebugToolbarMiddleware",
        ] + MIDDLEWARE

        DEBUG_TOOLBAR_CONFIG = {
            "SHOW_TOOLBAR_CALLBACK": lambda request: True,
            "SHOW_COLLAPSED": True,
        }
    except ImportError:
        # Django debug toolbar is not available
        pass
