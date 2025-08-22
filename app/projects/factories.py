from factory import LazyAttribute, Sequence
from factory.django import DjangoModelFactory

from app.projects.models import RETENTION_PERIOD_CHOICES, Project


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    name = Sequence(lambda i: f"Test project {i}")
    domain = Sequence(lambda i: f"test{i}.domain.com")
    retention_period_days = RETENTION_PERIOD_CHOICES[0]
