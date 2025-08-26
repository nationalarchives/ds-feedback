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
        Project, on_delete=models.PROTECT, related_name="feedback_forms"
    )

    def is_enabled(self):
        return self.disabled_at is None

    def get_parent_project(self):
        return self.project

    def __str__(self):
        return self.name


class PathPattern(TimestampedModelMixin, UUIDModelMixin, CreatedByModelMixin):
    pattern = models.CharField(max_length=512)
    is_wildcard = models.BooleanField(default=False)
    feedback_form = models.ForeignKey(
        FeedbackForm, on_delete=models.CASCADE, related_name="path_patterns"
    )
    project = models.ForeignKey(
        Project, on_delete=models.PROTECT, related_name="+"
    )

    @property
    def pattern_with_wildcard(self):
        return self.pattern + ("*" if self.is_wildcard else "")

    @pattern_with_wildcard.setter
    def pattern_with_wildcard(self, pattern):
        self.is_wildcard = pattern.endswith("*")
        self.pattern = pattern[:-1] if self.is_wildcard else pattern

    def get_parent_project(self):
        return self.feedback_form.project

    def clean(self):
        super().clean()

        if django.VERSION >= (5, 2):
            warnings.warn(
                "Custom validation no longer needed, since UniqueConstraint now supports custom error messages",
                DeprecationWarning,
            )

        if (
            PathPattern.objects.filter(
                pattern__iexact=self.pattern,
                project_id=self.project_id,
                is_wildcard=self.is_wildcard,
            )
            .exclude(id=self.id)
            .exists()
        ):
            raise ValidationError(
                {
                    "pattern_with_wildcard": "You cannot use the same pattern twice in a project."
                }
            )

    class Meta:
        constraints = [
            UniqueConstraint(
                "project",
                Lower("pattern"),
                "is_wildcard",
                name="unique_project_pattern",
                violation_error_message="You cannot use the same pattern twice in a project.",
            )
        ]

    def __str__(self):
        return self.pattern_with_wildcard
