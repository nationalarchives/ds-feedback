from typing import Generic, TypeVar

from django.contrib.auth.models import User

from factory import base, Sequence
from factory.django import DjangoModelFactory

T = TypeVar("T")


class BaseMetaFactory(Generic[T], base.FactoryMetaClass):
    def __call__(self, *args, **kwargs) -> T:
        return super().__call__(*args, **kwargs)


class StaffUserFactory(DjangoModelFactory, metaclass=BaseMetaFactory[User]):
    class Meta:  # type: ignore
        model = User

    username = Sequence(lambda i: f"user_{i}")
    password = "password"
    is_staff = True
