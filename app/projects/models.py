import re

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


class ProjectMembership(
    TimestampedModelMixin, UUIDModelMixin, CreatedByModelMixin
):
    project = models.ForeignKey("Project", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES)

    def get_parent_project(self):
        """Helper to get the parent Project for use in mixins."""
        return self.project

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
    members = models.ManyToManyField(
        User,
        through="ProjectMembership",
        through_fields=("project", "user"),
        related_name="project_memberships",
    )
    normalised_domain = models.CharField(
        max_length=256, editable=False, null=True
    )

    def clean(self):
        # Create normalized version for uniqueness check
        if self.domain:
            normalised = self.domain.lower()
            normalised = re.sub(r"^https://", "", normalised)
            normalised = re.sub(r"^www\.", "", normalised)
            normalised = normalised.rstrip("/")
            self.normalised_domain = normalised

        return super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            CheckConstraint(
                condition=models.Q(
                    retention_period_days__in=RETENTION_PERIOD_CHOICES
                ),
                name="retention_period_days_choices",
            ),
            models.UniqueConstraint(
                fields=["normalised_domain"],
                name="unique_normalised_domain",
                violation_error_message="This domain is already in use with another project.",
            ),
        ]

    def __str__(self):
        return self.name
