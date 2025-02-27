import uuid
from typing import Self, Type

from django.db import models

from app.users.models import User


class TimestampedModel(models.Model):
    """
    Abstract base class model that provides self-managed "created_at" and "modified_at" fields.
    """

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    Abstract base class model that provides a separate UUID field for external access,
    to avoid revealing the enumerable internal ID.
    """

    uuid = models.UUIDField(
        unique=True, default=uuid.uuid4, editable=False, verbose_name="ID"
    )

    class Meta:
        abstract = True


class DisableableModel(models.Model):
    """
    Abstract base class model that provides "disabled_at" and "disabled_by" fields
    """

    disabled_at = models.DateTimeField(null=True, blank=True)
    disabled_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        editable=False,
        null=True,
        blank=True,
        related_name="+",
    )

    def update_disabled_by(self, user: User):
        if self.disabled_at and not self.disabled_by_id:
            self.disabled_by = user
        if not self.disabled_at:
            self.disabled_by = None

    class Meta:
        abstract = True


class CreatedByModel(models.Model):
    """
    Abstract base class model that provides "created_by" field
    """

    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, editable=False, related_name="+"
    )

    def set_initial_created_by(self, user: User):
        if not self.created_by_id:
            self.created_by = user

    class Meta:
        abstract = True


class Specialisable(models.Model):
    """
    Abstract base class model that provides "specialise" helper to create a specialised version of a model.
    Assumes default *_ptr field name.
    """

    def specialise(self, Subclass: Type[Self]):
        specialised = Subclass()
        setattr(specialised, Subclass._meta.model_name + "_ptr", self)
        specialised.__dict__.update(self.__dict__)
        return specialised

    class Meta:
        abstract = True
