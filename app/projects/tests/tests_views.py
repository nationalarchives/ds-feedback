from datetime import datetime
from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from app.projects.factories import ProjectFactory
from app.projects.models import Project
from app.users.factories import StaffUserFactory
from app.utils.testing import get_change_list_results


class TestAdminProjectsView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)

    def test_list_projects_by_most_recent(self):
        project1 = ProjectFactory.create(
            created_at=datetime(2000, 1, 2), created_by=self.admin_user
        )
        project2 = ProjectFactory.create(
            created_at=datetime(2000, 1, 1), created_by=self.admin_user
        )
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin:projects_project_changelist"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            get_change_list_results(response), [project2, project1]
        )

    def test_create_project_sets_created_by(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("admin:projects_project_add"),
            {
                "name": "Test Project",
                "domain": "test.domain.com",
                "retention_period_days": 60,
                "owned_by": self.admin_user.id,
            },
        )
        self.assertRedirects(
            response, reverse("admin:projects_project_changelist")
        )

        project = Project.objects.get(name="Test Project")
        self.assertEqual(project.created_by, self.admin_user)
