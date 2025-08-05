from factory import Sequence
from factory.django import DjangoModelFactory

from .models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = Sequence(lambda i: f"user_{i}@example.com")
    password = "password"


class StaffUserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = Sequence(lambda i: f"staff_user_{i}@example.com")
    password = "password"
    is_staff = True
