from django.contrib.auth.models import User
from django.db import models
from django.db.models.constraints import CheckConstraint

from app.utils.models import TimestampedModel, UUIDModel

RETENTION_PERIOD_CHOICES: list[int] = [30, 60, 180]


class Project(TimestampedModel, UUIDModel):
    """
    Model for a project, which is a grouping for feedback prompts and data collected from a particular domain.
    """

    name = models.CharField(max_length=128)
    domain = models.CharField(max_length=256)
    retention_period_days = models.PositiveSmallIntegerField(
        "Retention period",
        choices={
            choice: f"{choice} days" for choice in RETENTION_PERIOD_CHOICES
        },
    )
    owned_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="+"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, editable=False, related_name="+"
    )

    class Meta:
        constraints = [
            CheckConstraint(
                condition=models.Q(
                    retention_period_days__in=RETENTION_PERIOD_CHOICES
                ),
                name="retention_period_days_choices",
            )
        ]

    def __str__(self):
        return self.name
