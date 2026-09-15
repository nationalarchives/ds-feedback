import os

from tna_utilities import strtobool

from .features import *
from .production import *

DEBUG = strtobool(os.getenv("DEBUG", "False"))
