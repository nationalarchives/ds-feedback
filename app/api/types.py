from django.db.models import TextChoices, IntegerChoices


class APIRole(TextChoices):
    RESPONSE_SUBMITTER = "response-submitter"
    READ_ONLY = "read-only"


class APIAccessLifespan(IntegerChoices):
    DAYS_30 = 30, "30 days"
    DAYS_60 = 60, "60 days"
    DAYS_90 = 90, "90 days"
    DAYS_180 = 180, "180 days"