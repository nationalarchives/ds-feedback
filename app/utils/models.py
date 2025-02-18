import uuid

from django.db import models


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
