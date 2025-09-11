from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

import factory


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
        skip_postgeneration_save = True

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
            perm_instance = Permission.objects.get(codename="add_project")
            self.user_permissions.add(perm_instance)
            self.save()
