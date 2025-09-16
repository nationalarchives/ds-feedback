import datetime

from django.db import models
from django.utils import timezone

from app.projects.models import Project
from app.users.models import User
from app.utils.models import (
    CreatedByModelMixin,
    TimestampedModelMixin,
    UUIDModelMixin,
)

from .types import APIAccessLifespan, APIRole


class ProjectAPIAccessQuerySet(models.QuerySet):
    def active(self):
        return self.filter(expires_at__gte=timezone.now())


class ProjectAPIAccess(
    CreatedByModelMixin, TimestampedModelMixin, UUIDModelMixin, models.Model
):
    objects = ProjectAPIAccessQuerySet.as_manager()

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="accesses"
    )
    grantee = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=18, choices=APIRole.choices)
    expires_at = models.DateTimeField(editable=False)
    lifespan_days = models.PositiveSmallIntegerField(
        choices=APIAccessLifespan.choices
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=list(APIRole.values)),
                name="api_access_role_valid_choice",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    lifespan_days__in=list(APIAccessLifespan.values)
                ),
                name="api_access_role_valid_lifespan",
            ),
        ]
        indexes = [
            models.Index(fields=["expires_at"]),
        ]
        verbose_name = "project API access"
        verbose_name_plural = "project API accesses"

    @property
    def is_active(self) -> bool:
        return self.expires_at > timezone.now()

    def get_parent_project(self):
        """Helper to get the parent Project for use in mixins."""
        return self.project

    def save(self, *args, **kwargs):
        if self.id is None and self.expires_at is None:
            self.expires_at = timezone.now() + datetime.timedelta(
                days=self.lifespan_days
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return "ProjectAPIAccess"
