from django.test import TestCase
from django.urls import reverse

from app.api.factories import APIAccessLifespanFactory
from app.api.types import APIRole
from app.editor_ui.factories import UserFactory
from app.projects.factories import ProjectFactory
from app.projects.models import ProjectMembership


class APIAccessPermissionTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create users
        cls.superuser = UserFactory(is_superuser=True)
        cls.project_owner = UserFactory(email="owner@example.com")
        cls.project_editor = UserFactory(email="editor@example.com")
        cls.other_project_owner = UserFactory(email="other_owner@example.com")
        cls.regular_user = UserFactory(email="regular@example.com")

        # Create projects
        cls.project = ProjectFactory(created_by=cls.superuser)
        cls.other_project = ProjectFactory(created_by=cls.superuser)

        # Create project memberships
        ProjectMembership.objects.create(
            project=cls.project,
            user=cls.project_owner,
            role="owner",
            created_by=cls.superuser,
        )
        ProjectMembership.objects.create(
            project=cls.project,
            user=cls.project_editor,
            role="editor",
            created_by=cls.superuser,
        )
        ProjectMembership.objects.create(
            project=cls.other_project,
            user=cls.other_project_owner,
            role="owner",
            created_by=cls.superuser,
        )

        # Create an API access for testing delete permissions
        cls.editor_api_access = APIAccessLifespanFactory(
            project=cls.project,
            grantee=cls.project_editor,
            role=APIRole.EXPLORE_RESPONSES,
            created_by=cls.project_owner,
        )
        cls.owner_api_access = APIAccessLifespanFactory(
            project=cls.project,
            grantee=cls.project_owner,
            role=APIRole.EXPLORE_RESPONSES,
            created_by=cls.superuser,
        )


class APIAccessListViewPermissionTests(APIAccessPermissionTestCase):
    def get_list_url(self, project):
        return reverse(
            "editor_ui:projects:api_access:list",
            kwargs={"project_uuid": str(project.uuid)},
        )

    def test_superuser_can_access_list_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.get_list_url(self.project))
        self.assertEqual(response.status_code, 200)

    def test_project_owner_can_access_list_view(self):
        self.client.force_login(self.project_owner)
        response = self.client.get(self.get_list_url(self.project))
        self.assertEqual(response.status_code, 200)

    def test_project_editor_can_access_list_view(self):
        self.client.force_login(self.project_editor)
        response = self.client.get(self.get_list_url(self.project))
        self.assertEqual(response.status_code, 200)

    def test_non_project_member_cannot_access_list_view(self):
        self.client.force_login(self.regular_user)
        response = self.client.get(self.get_list_url(self.project))
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(self.get_list_url(self.project))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login/", response.url)

    def test_cross_project_access_denied(self):
        self.client.force_login(self.other_project_owner)
        response = self.client.get(self.get_list_url(self.project))
        self.assertEqual(response.status_code, 403)


class APIAccessCreateViewPermissionTests(APIAccessPermissionTestCase):
    def get_create_url(self, project):
        return reverse(
            "editor_ui:projects:api_access:create",
            kwargs={"project_uuid": str(project.uuid)},
        )

    def test_superuser_can_access_create_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.get_create_url(self.project))
        self.assertEqual(response.status_code, 200)

    def test_project_owner_can_access_create_view(self):
        self.client.force_login(self.project_owner)
        response = self.client.get(self.get_create_url(self.project))
        self.assertEqual(response.status_code, 200)

    def test_project_editor_can_access_create_view(self):
        self.client.force_login(self.project_editor)
        response = self.client.get(self.get_create_url(self.project))
        self.assertEqual(response.status_code, 200)

    def test_non_project_member_cannot_access_create_view(self):
        self.client.force_login(self.regular_user)
        response = self.client.get(self.get_create_url(self.project))
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(self.get_create_url(self.project))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login/", response.url)

    def test_cross_project_access_denied(self):
        self.client.force_login(self.other_project_owner)
        response = self.client.get(self.get_create_url(self.project))
        self.assertEqual(response.status_code, 403)


class APIAccessDeleteViewPermissionTests(APIAccessPermissionTestCase):
    def get_delete_url(self, project, api_access):
        return reverse(
            "editor_ui:projects:api_access:delete",
            kwargs={
                "project_uuid": str(project.uuid),
                "api_access_uuid": str(api_access.uuid),
            },
        )

    def test_superuser_can_access_delete_view(self):
        self.client.force_login(self.superuser)
        response = self.client.get(
            self.get_delete_url(self.project, self.editor_api_access)
        )
        self.assertEqual(response.status_code, 200)

    def test_project_owner_can_delete_any_project_api_access(self):
        self.client.force_login(self.project_owner)
        response = self.client.get(
            self.get_delete_url(self.project, self.editor_api_access)
        )
        self.assertEqual(response.status_code, 200)

    def test_editor_can_delete_own_api_access(self):
        self.client.force_login(self.project_editor)
        response = self.client.get(
            self.get_delete_url(self.project, self.editor_api_access)
        )
        self.assertEqual(response.status_code, 200)

    def test_editor_cannot_delete_others_api_access(self):
        self.client.force_login(self.project_editor)
        response = self.client.get(
            self.get_delete_url(self.project, self.owner_api_access)
        )
        self.assertEqual(response.status_code, 403)

    def test_non_project_member_cannot_delete_api_access(self):
        self.client.force_login(self.regular_user)
        response = self.client.get(
            self.get_delete_url(self.project, self.editor_api_access)
        )
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(
            self.get_delete_url(self.project, self.editor_api_access)
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login/", response.url)

    def test_cross_project_access_denied(self):
        self.client.force_login(self.other_project_owner)
        response = self.client.get(
            self.get_delete_url(self.project, self.editor_api_access)
        )
        self.assertEqual(response.status_code, 403)
