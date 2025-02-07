from http import HTTPStatus
from urllib.parse import urlparse
from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from factory.django import DjangoModelFactory
from factory import Sequence, LazyAttribute

from app.projects.models import Project, RETENTION_PERIOD_CHOICES


def get_change_list_results(response):
    """
    Returns the change list results from a response
    """
    return list(response.context['cl'].result_list)


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    name = Sequence(lambda i: f"Test project {i}")
    domain = Sequence(lambda i: f"test{i}.domain.com")
    retention_period = RETENTION_PERIOD_CHOICES[0]
    owned_by = LazyAttribute(lambda project: project.created_by)


class TestAdminProjectsView(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestAdminProjectsView, cls).setUpClass()
        cls.admin_user = User.objects.create_user(username="test", password="password", is_staff=True, is_superuser=True)

    def test_list_projects_by_most_recent(self):
        project1 = ProjectFactory.create(created_at=datetime(2000, 1, 2), created_by=self.admin_user)
        project2 = ProjectFactory.create(created_at=datetime(2000, 1, 1), created_by=self.admin_user)
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin:projects_project_changelist"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(get_change_list_results(response), [project2, project1])

    def test_create_project_sets_created_by(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(reverse("admin:projects_project_add"), {
            "name": "Test Project",
            "domain": "test.domain.com",
            "retention_period": 60,
            "owned_by": self.admin_user.id,
        })
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(urlparse(response.headers["Location"]).path, reverse("admin:projects_project_changelist"))

        project = Project.objects.get(name="Test Project")
        self.assertEqual(project.created_by, self.admin_user)
