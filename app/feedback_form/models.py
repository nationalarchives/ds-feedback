from django.db import models

from app.projects.models import Project
from app.users.models import User
from app.utils.models import TimestampedModel, UUIDModel


class FeedbackForm(TimestampedModel, UUIDModel):
    name = models.CharField(max_length=128)
    project = models.ForeignKey(
        Project, on_delete=models.PROTECT, related_name="+"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, editable=False, related_name="+"
    )
    disabled_at = models.DateTimeField(null=True, blank=True)
    disabled_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        editable=False,
        null=True,
        blank=True,
        related_name="+",
    )

    def __str__(self):
        return self.name


class PathPattern(TimestampedModel, UUIDModel):
    pattern = models.CharField(max_length=512)
    feedback_form = models.ForeignKey(
        FeedbackForm, on_delete=models.CASCADE, related_name="path_patterns"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.PROTECT, editable=False, related_name="+"
    )

    def __str__(self):
        return self.pattern
