from django.db import models
from django.db.models.constraints import CheckConstraint

from app.users.models import User
from app.utils.models import (
    CreatedByModelMixin,
    TimestampedModelMixin,
    UUIDModelMixin,
)

RETENTION_PERIOD_CHOICES: list[int] = [30, 60, 180]

ROLE_CHOICES = [
    ("owner", "Owner"),
    ("editor", "Editor"),
]


class ProjectMembership(models.Model):
    project = models.ForeignKey("Project", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)

    class Meta:
        unique_together = ("user", "project")


class Project(TimestampedModelMixin, UUIDModelMixin, CreatedByModelMixin):
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
    members = models.ManyToManyField(
        User, through="ProjectMembership", related_name="project_memberships"
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
