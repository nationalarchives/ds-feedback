import uuid
from typing import Self

from django.apps import apps
from django.db import models

from model_utils.managers import InheritanceManager

from app.users.models import User


class TimestampedModelMixin(models.Model):
    """
    Abstract base class model that provides self-managed "created_at" and "modified_at" fields.
    """

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModelMixin(models.Model):
    """
    Abstract base class model that provides a separate UUID field for external access,
    to avoid revealing the enumerable internal ID.
    """

    uuid = models.UUIDField(
        unique=True, default=uuid.uuid4, editable=False, verbose_name="ID"
    )

    class Meta:
        abstract = True


class DisableableModelMixin(models.Model):
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


class CreatedByModelMixin(models.Model):
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


class CreateSubclassModelMixin(models.Model):
    """
    Abstract base class model that provides create_subclass helper to create a subclassed version of a model.
    Assumes default *_ptr field name.
    """

    def create_subclass(self, subclass: type[Self]):
        """
        Converts a model into a multi-table inheritance subclass
        """
        assert issubclass(
            subclass, type(self)
        ), f"{subclass} must be a subclass of {type(self)}"

        instance = subclass()
        setattr(instance, subclass._meta.model_name + "_ptr", self)
        instance.__dict__.update(self.__dict__)
        return instance

    class Meta:
        abstract = True


class GetSubclassesModelMixin(models.Model):
    """
    Abstract base class model that provides helper to get model subclasses and
    subclasses by model name
    """

    @classmethod
    def get_subclasses_mapping(cls) -> dict[str, type[Self]]:
        """
        Uses the InheritanceManager to return a mapping of model names to subclasses
        """
        assert isinstance(
            cls.objects, InheritanceManager
        ), f"{cls} must use InheritanceManager to support LookupSubclasses"

        return {
            model_name: apps.get_model(
                app_label=cls._meta.app_label, model_name=model_name
            )
            for model_name in cls.objects.all()._get_subclasses_recurse(cls)
        }

    @classmethod
    def get_subclass_by_name(cls, name: str):
        """
        Returns a model subclass from its model name
        """
        return cls.get_subclasses_mapping()[name]

    class Meta:
        abstract = True
