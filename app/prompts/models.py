from django.db import models

from app.feedback_form.models import FeedbackForm
from app.users.models import User
from app.utils.models import TimestampedModel, UUIDModel


class Prompt(TimestampedModel, UUIDModel):
    text = models.CharField(max_length=128)
    feedback_form = models.ForeignKey(
        FeedbackForm, on_delete=models.CASCADE, related_name="prompts"
    )
    order = models.PositiveSmallIntegerField()
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
        return self.text


class TextPrompt(Prompt):
    max_length = models.PositiveSmallIntegerField(default=1000)
