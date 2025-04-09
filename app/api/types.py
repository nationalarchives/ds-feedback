from django.db.models import IntegerChoices, TextChoices


class APIRole(TextChoices):
    SUBMIT_RESPONSES = "submit-responses"
    EXPLORE_RESPONSES = "explore-responses"


class APIAccessLifespan(IntegerChoices):
    DAYS_30 = 30, "30 days"
    DAYS_60 = 60, "60 days"
    DAYS_90 = 90, "90 days"
    DAYS_180 = 180, "180 days"
