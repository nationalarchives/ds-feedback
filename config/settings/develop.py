import os

from config.util import strtobool

from .base import *
from .features import *

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

DEBUG: bool = strtobool(os.getenv("DEBUG", "True"))

# Adds Django Debug Toolbar
INSTALLED_APPS.append("debug_toolbar") # noqa
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware") # noqa
SHOW_TOOLBAR = True
DEBUG_TOOLBAR_CONFIG = {
    # The default debug_toolbar_middleware.show_toolbar function checks whether the
    # request IP is in settings.INTERNAL_IPS. In Docker, the request IP can vary, so
    # we set it in settings.local instead.
    "SHOW_TOOLBAR_CALLBACK": lambda x: SHOW_TOOLBAR,
}
