import uuid
from django.db import models
from django.contrib.auth.models import User

RETENTION_PERIOD_CHOICES = [30, 60, 180]


class TimestampedModel(models.Model):
    """
    Abstract base class model that provides self-managed "created_at" and "modified_at" fields.
    """

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UuidModel(models.Model):
    """
    Abstract base class model that provides a separate UUID field for external access,
    to avoid revealing the enumerable internal ID.
    """

    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False, verbose_name='ID')

    class Meta:
        abstract = True


class Project(TimestampedModel, UuidModel):
    """
    Model for a project, which is a grouping for feedback prompts and data collected from a particular domain.
    """

    name = models.CharField(max_length=128)
    domain = models.CharField(max_length=256)
    retention_period = models.IntegerField(choices={choice: choice for choice in RETENTION_PERIOD_CHOICES})
    owned_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, editable=False, related_name="created_projects")

    def __str__(self):
        return self.name
