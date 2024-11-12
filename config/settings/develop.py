import os

from config.util import strtobool

from .base import *
from .features import *

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

DEBUG = strtobool(os.getenv("DEBUG", "True"))
