from factory import Sequence
from factory.django import DjangoModelFactory

from .models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Sequence(lambda i: f"user_{i}")
    password = "password"


class StaffUserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Sequence(lambda i: f"staff_user_{i}")
    password = "password"
    is_staff = True
