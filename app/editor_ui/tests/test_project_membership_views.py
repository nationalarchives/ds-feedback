from django.test import TestCase
from django.urls import reverse

from app.editor_ui.factories import UserFactory
from app.projects.factories import ProjectFactory
from app.projects.models import ProjectMembership


class ProjectMembershipListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = UserFactory(is_superuser=True)
        cls.owner = UserFactory()
        cls.editor = UserFactory()
        cls.project = ProjectFactory(created_by=cls.admin)
        ProjectMembership.objects.create(
            project=cls.project,
            user=cls.owner,
            role="owner",
            created_by=cls.admin,
        )
        ProjectMembership.objects.create(
            project=cls.project,
            user=cls.editor,
            role="editor",
            created_by=cls.admin,
        )

    def test_admin_sees_all_user_management_actions(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "editor_ui:projects:memberships:list", args=[self.project.uuid]
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-testing-id="add-user-button"')
        self.assertContains(response, 'data-testing-id="edit-button"')
        self.assertContains(response, 'data-testing-id="delete-button"')

    def test_owner_sees_all_user_management_actions(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse(
                "editor_ui:projects:memberships:list", args=[self.project.uuid]
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-testing-id="add-user-button"')
        self.assertContains(response, 'data-testing-id="edit-button"')
        self.assertContains(response, 'data-testing-id="delete-button"')

    def test_editor_sees_limited_user_management_actions(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "editor_ui:projects:memberships:list", args=[self.project.uuid]
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-testing-id="delete-button"')
        self.assertNotContains(response, 'data-testing-id="add-user-button"')
        self.assertNotContains(response, 'data-testing-id="edit-button"')


class ProjectMembershipDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = UserFactory(is_superuser=True)
        cls.owner = UserFactory()
        cls.editor = UserFactory()
        cls.project = ProjectFactory(created_by=cls.admin)
        ProjectMembership.objects.create(
            project=cls.project,
            user=cls.owner,
            role="owner",
            created_by=cls.admin,
        )
        ProjectMembership.objects.create(
            project=cls.project,
            user=cls.editor,
            role="editor",
            created_by=cls.admin,
        )

    def test_admin_sees_project_management_actions(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("editor_ui:projects:detail", args=[self.project.uuid])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-testing-id="edit-project-button"')

    def test_owner_sees_project_management_actions(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("editor_ui:projects:detail", args=[self.project.uuid])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-testing-id="edit-project-button"')

    def test_editor_cannot_see_project_management_actions(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse("editor_ui:projects:detail", args=[self.project.uuid])
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response, 'data-testing-id="edit-project-button"'
        )
