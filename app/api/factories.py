from factory.django import DjangoModelFactory
from rest_framework.authtoken.models import Token

from .models import ProjectAPIAccess
from .types import APIAccessLifespan


class APIAccessLifespanFactory(DjangoModelFactory):
    class Meta:
        model = ProjectAPIAccess

    lifespan_days = APIAccessLifespan.DAYS_180


class TokenFactory(DjangoModelFactory):
    class Meta:
        model = Token
