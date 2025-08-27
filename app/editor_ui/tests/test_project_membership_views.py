from django.test import TestCase
from django.urls import reverse

from app.editor_ui.factories import UserFactory
from app.projects.factories import ProjectFactory
from app.projects.models import ProjectMembership


class ProjectListViewTests(TestCase):
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
            reverse("editor_ui:project_memberships", args=[self.project.uuid])
        )

        self.assertEqual(response.status_code, 200)
        content = (
            response.content.decode()
            .replace("\n", "")
            .replace("\r", "")
            .replace("  ", " ")
        )
        self.assertRegex(content, r'<a [^>]*class="tna-button"[^>]*>Edit</a>')
        self.assertRegex(content, r'<a [^>]*class="tna-button"[^>]*>Delete</a>')

    def test_owner_sees_all_user_management_actions(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("editor_ui:project_memberships", args=[self.project.uuid])
        )

        self.assertEqual(response.status_code, 200)
        content = (
            response.content.decode()
            .replace("\n", "")
            .replace("\r", "")
            .replace("  ", " ")
        )
        self.assertRegex(content, r'<a [^>]*class="tna-button"[^>]*>Edit</a>')
        self.assertRegex(content, r'<a [^>]*class="tna-button"[^>]*>Delete</a>')

    def test_editor_sees_limited_user_management_actions(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse("editor_ui:project_memberships", args=[self.project.uuid])
        )

        self.assertEqual(response.status_code, 200)
        content = (
            response.content.decode()
            .replace("\n", "")
            .replace("\r", "")
            .replace("  ", " ")
        )
        self.assertRegex(content, r'<a [^>]*class="tna-button"[^>]*>Delete</a>')
        self.assertNotRegex(content, r'<a [^>]*class="tna-button"[^>]*>Edit</a>')

    def test_editor_with_project_membership_cannot_add_users(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse("editor_ui:project_memberships_add", args=[self.project.uuid])
        )

        self.assertEqual(response.status_code, 403)
