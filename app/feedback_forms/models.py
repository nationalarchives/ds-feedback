import warnings

import django
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower

from app.projects.models import Project
from app.utils.models import (
    CreatedByModelMixin,
    DisableableModelMixin,
    TimestampedModelMixin,
    UUIDModelMixin,
)


class FeedbackForm(
    TimestampedModelMixin,
    UUIDModelMixin,
    CreatedByModelMixin,
    DisableableModelMixin,
):
    name = models.CharField(max_length=128)
    project = models.ForeignKey(
        Project, on_delete=models.PROTECT, related_name="+"
    )

    def is_enabled(self):
        return self.disabled_at is None

    def __str__(self):
        return self.name


class PathPattern(TimestampedModelMixin, UUIDModelMixin, CreatedByModelMixin):
    pattern = models.CharField(max_length=512)
    feedback_form = models.ForeignKey(
        FeedbackForm, on_delete=models.CASCADE, related_name="path_patterns"
    )
    project = models.ForeignKey(
        Project, on_delete=models.PROTECT, related_name="+"
    )

    def clean(self):
        super().clean()

        if django.VERSION >= (5, 2):
            warnings.warn(
                "Custom validation no longer needed, since UniqueConstraint now supports custom error messages",
                DeprecationWarning,
            )

        if (
            PathPattern.objects.filter(
                pattern__iexact=self.pattern, project_id=self.project_id
            )
            .exclude(id=self.id)
            .exists()
        ):
            raise ValidationError(
                {
                    "pattern": "You cannot use the same pattern twice in a project."
                }
            )

    class Meta:
        constraints = [
            UniqueConstraint(
                "project",
                Lower("pattern"),
                name="unique_project_pattern",
                violation_error_message="You cannot use the same pattern twice in a project.",
            )
        ]

    def __str__(self):
        return self.pattern
