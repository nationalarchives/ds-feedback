from django.contrib.auth.models import User

from factory import Sequence
from factory.django import DjangoModelFactory


class StaffUserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Sequence(lambda i: f"user_{i}")
    password = "password"
    is_staff = True
