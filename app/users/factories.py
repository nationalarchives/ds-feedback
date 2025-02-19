from factory import Sequence
from factory.django import DjangoModelFactory

from .models import User


class StaffUserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Sequence(lambda i: f"user_{i}")
    password = "password"
    is_staff = True
