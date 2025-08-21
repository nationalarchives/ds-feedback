from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

import factory
import factory.fuzzy

from app.projects.models import RETENTION_PERIOD_CHOICES, Project


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.Faker("email")
    password = factory.django.Password("changeMe")

    @factory.post_generation
    def add_project_creation_permission(self, create, extracted, **kwargs):
        """
        If 'add_project_permission=True' is passed to the factory, the user will be
        given the 'projects.add_project' permission.
        """
        if not create:
            return
        if extracted:
            perm = Permission.objects.get(codename="add_project")
            self.user_permissions.add(perm)


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Faker("sentence", nb_words=3)
    domain = factory.Faker("url")
    retention_period_days = factory.fuzzy.FuzzyChoice(RETENTION_PERIOD_CHOICES)
    created_by = factory.SubFactory(UserFactory)
