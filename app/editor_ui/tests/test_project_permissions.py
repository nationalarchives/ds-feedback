from django.test import TestCase
from django.urls import reverse

from app.editor_ui.factories import UserFactory
from app.projects.factories import ProjectFactory
from app.projects.models import (
    RETENTION_PERIOD_CHOICES,
    Project,
    ProjectMembership,
)


class ProjectCreationTests(TestCase):
    """Tests for project creation permissions and redirects."""

    def setUp(self):
        """Set up users and project creation URL for each test."""
        self.creator_user = UserFactory(add_project_creation_permission=True)
        self.other_user = UserFactory()
        self.project_create_url = reverse("editor_ui:project_create")

    def test_user_with_add_project_acl_can_create_project(self):
        """
        A user with the 'add_project' permission can create a project and is redirected
        to the project detail page.
        """
        self.assertTrue(
            self.creator_user.has_perm("projects.add_project"),
            "creator_user should have the 'projects.add_project' permission",
        )

        self.client.force_login(self.creator_user)

        response = self.client.post(
            self.project_create_url,
            {
                "name": "Owner Project",
                "domain": "https://owner.domain.com",
                "retention_period_days": RETENTION_PERIOD_CHOICES[0],
                "created_by": self.creator_user,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Project.objects.count(),
            1,
            "Project count should be 1 after creation",
        )

        project = Project.objects.get(name="Owner Project")
        expected_url = reverse(
            "editor_ui:project_detail",
            kwargs={"project_uuid": str(project.uuid)},
        )

        self.assertEqual(
            response.url,
            expected_url,
            "Redirect to the project detail page is expected after creation",
        )

    def test_user_without_add_project_acl_can_not_create_project(self):
        """
        A user without the 'add_project' permission cannot create a project.
        """
        self.assertFalse(
            self.other_user.has_perm("projects.add_project"),
            "other_user should not have the 'projects.add_project' permission",
        )

        self.client.force_login(self.other_user)

        response = self.client.post(
            self.project_create_url,
            {
                "name": "Other Project",
                "domain": "https://other.domain.com",
                "retention_period_days": RETENTION_PERIOD_CHOICES[0],
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            Project.objects.count(), 0, "No projects should be created"
        )


class ProjectMembershipAssignmentTests(TestCase):
    """Tests for project membership assignment."""

    def setUp(self):
        """Set up users and project creation URL for each test."""
        self.creator_user = UserFactory(add_project_creation_permission=True)
        self.other_user = UserFactory()
        self.project_create_url = reverse("editor_ui:project_create")

    def test_project_creator_gets_owner_membership_on_creation(self):
        """
        Project creator is assigned an 'owner' ProjectMembership
        when a project is created.
        """
        self.assertTrue(
            self.creator_user.has_perm("projects.add_project"),
            "creator_user should have the 'projects.add_project' permission",
        )

        self.client.force_login(self.creator_user)

        response = self.client.post(
            self.project_create_url,
            {
                "name": "Owner Project",
                "domain": "https://owner.domain.com",
                "retention_period_days": 30,
            },
        )

        self.assertEqual(
            Project.objects.count(),
            1,
            "Project count should be 1 after creation",
        )
        self.assertEqual(response.status_code, 302)

        project = Project.objects.get(name="Owner Project")
        membership_exists = ProjectMembership.objects.filter(
            user=self.creator_user, project=project, role="owner"
        ).exists()

        self.assertTrue(
            membership_exists,
            "Project creator should have an 'owner' ProjectMembership for the new project",
        )


class ProjectAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.owner = UserFactory()
        cls.editor = UserFactory()
        cls.other_user = UserFactory()
        cls.superuser = UserFactory(is_superuser=True)

        # Users authorised to access project detail
        cls.authorised_users = [cls.superuser, cls.owner, cls.editor]

        # Project and membership
        cls.project = ProjectFactory(created_by=cls.superuser)
        ProjectMembership.objects.create(
            project=cls.project,
            user=cls.owner,
            role="owner",
            created_by=cls.superuser,
        )
        ProjectMembership.objects.create(
            project=cls.project,
            user=cls.editor,
            role="editor",
            created_by=cls.superuser,
        )

        # Another project for cross-project access tests
        cls.other_project = ProjectFactory(created_by=cls.superuser)

    def project_detail_url(self, project):
        """Helper to get project detail URL."""
        return reverse(
            "editor_ui:project_detail",
            kwargs={"project_uuid": str(project.uuid)},
        )

    def get_project_update_url(self, project):
        """Helper to get project update URL."""
        return reverse(
            "editor_ui:project_update",
            kwargs={"project_uuid": str(project.uuid)},
        )

    def test_authorised_users_can_access_project_detail(self):
        for user in self.authorised_users:
            with self.subTest(user=user):
                self.client.force_login(user)
                response = self.client.get(
                    self.project_detail_url(self.project)
                )
                self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_access_project_detail(self):
        self.client.force_login(self.other_user)
        response = self.client.get(self.project_detail_url(self.project))
        self.assertIn(response.status_code, (403, 404))

    def test_owner_cannot_access_other_project_detail(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.project_detail_url(self.other_project))
        self.assertIn(response.status_code, (403, 404))

    def test_editor_with_project_membership_cannot_access_project_update(self):
        self.client.force_login(self.editor)
        response = self.client.get(self.get_project_update_url(self.project))
        self.assertEqual(response.status_code, 403)

    def test_superuser_can_access_any_projects_detail(self):
        for project in [self.project, self.other_project]:
            with self.subTest(project=project):
                self.client.force_login(self.superuser)
                response = self.client.get(self.project_detail_url(project))
                self.assertEqual(response.status_code, 200)


class ProjectMembershipAccessTests(TestCase):
    """Tests for access permissions on Project Membership Views"""

    def setUp(self):
        """Set up specific objects for project membership deletion tests."""
        # Users
        self.owner = UserFactory()
        self.editor = UserFactory()
        self.other_user = UserFactory()
        self.superuser = UserFactory(is_superuser=True)

        # Users authorised to view project permissions
        self.authorised_users = [self.superuser, self.owner]

        # Project and membership
        self.project = ProjectFactory(created_by=self.superuser)
        self.owner_membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.owner,
            role="owner",
            created_by=self.superuser,
        )
        self.editor_membership = ProjectMembership.objects.create(
            project=self.project,
            user=self.editor,
            role="editor",
            created_by=self.superuser,
        )

        # Another project and membership for cross-project access tests
        self.other_project = ProjectFactory(created_by=self.superuser)
        self.other_member = UserFactory()
        self.other_membership = ProjectMembership.objects.create(
            project=self.other_project,
            user=self.other_member,
            role="owner",
            created_by=self.superuser,
        )

    def get_project_membership_list_url(self, project):
        """Helper to get project membership list URL."""
        return reverse(
            "editor_ui:project__memberships",
            kwargs={"project_uuid": str(project.uuid)},
        )

    def get_project_membership_edit_url(self, project, membership):
        """Helper to get the project membership edit URL."""
        return reverse(
            "editor_ui:project__memberships_edit",
            kwargs={
                "project_uuid": str(project.uuid),
                "membership_uuid": str(membership.uuid),
            },
        )

    def get_project_membership_delete_url(self, project, membership):
        """Helper to get the project membership delete URL."""
        return reverse(
            "editor_ui:project__memberships_delete",
            kwargs={
                "project_uuid": str(project.uuid),
                "membership_uuid": str(membership.uuid),
            },
        )

    def test_authorised_users_can_access_project_membership_views(self):
        for user in self.authorised_users:
            for url in [
                self.get_project_membership_list_url(self.project),
                self.get_project_membership_delete_url(
                    self.project, self.owner_membership
                ),
                self.get_project_membership_edit_url(
                    self.project, self.owner_membership
                ),
            ]:
                with self.subTest(user=user, url=url):
                    self.client.force_login(user)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)

    def test_unauthorised_users_cannot_access_project_membership_views(self):
        for url in [
            self.get_project_membership_list_url(self.project),
            self.get_project_membership_delete_url(
                self.project, self.owner_membership
            ),
            self.get_project_membership_edit_url(
                self.project, self.owner_membership
            ),
        ]:
            with self.subTest(url=url):
                self.client.force_login(self.other_user)
                response = self.client.get(url)
                self.assertIn(response.status_code, (403, 404))

    def test_editor_user_can_only_access_project_membership_views_if_project_member(
        self,
    ):
        for url in [
            self.get_project_membership_list_url(self.project),
            self.get_project_membership_delete_url(
                self.project, self.editor_membership
            ),
        ]:
            with self.subTest(url=url):
                self.client.force_login(self.editor)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

        for url in [
            self.get_project_membership_list_url(self.other_project),
            self.get_project_membership_delete_url(
                self.other_project, self.other_membership
            ),
        ]:
            with self.subTest(url=url):
                self.client.force_login(self.editor)
                response = self.client.get(url)
                self.assertIn(response.status_code, [403, 404])

    def test_editor_with_project_membership_cannot_add_users(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "editor_ui:project__memberships_add", args=[self.project.uuid]
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_editor_with_project_membership_can_remove_self(self):
        self.client.force_login(self.editor)
        editor_membership = ProjectMembership.objects.get(
            project=self.project, user=self.editor
        )
        response = self.client.post(
            reverse(
                "editor_ui:project__memberships_delete",
                args=[self.project.uuid, editor_membership.uuid],
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, reverse("editor_ui:project_list"))
        self.assertFalse(
            ProjectMembership.objects.filter(
                project=self.project, user=self.editor
            ).exists()
        )

    def test_editor_with_project_membership_cannot_remove_others(self):
        self.client.force_login(self.editor)
        owner_membership = ProjectMembership.objects.get(
            project=self.project, user=self.owner
        )
        response = self.client.post(
            reverse(
                "editor_ui:project__memberships_delete",
                args=[self.project.uuid, owner_membership.uuid],
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            ProjectMembership.objects.filter(
                project=self.project, user=self.owner, role="owner"
            ).exists()
        )

    def test_owner_cannot_access_project_membership_delete_view_for_other_project(
        self,
    ):
        url = self.get_project_membership_delete_url(
            self.other_project, self.other_membership
        )
        self.client.force_login(self.owner)
        response = self.client.get(url)
        self.assertIn(response.status_code, (403, 404))

    def test_cross_project_project_membership_delete_view_denied(self):
        """
        Test that mixing project and membership UUIDs from different projects is denied.
        """
        url = self.get_project_membership_delete_url(
            self.project, self.other_membership
        )
        self.client.force_login(self.owner)
        response = self.client.get(url)
        self.assertIn(response.status_code, (403, 404))

    def test_owner_cannot_delete_their_own_membership_if_only_one_owner(self):
        """
        Test that a project owner cannot delete their own membership if they are the
        only owner. This is an important restriction to prevent orphaned projects.
        """
        # Project with single owner membership
        project_with_single_owner = ProjectFactory(created_by=self.owner)
        self.owner_membership = ProjectMembership.objects.create(
            project=project_with_single_owner,
            user=self.owner,
            role="owner",
            created_by=self.owner,
        )

        self.assertEqual(
            ProjectMembership.objects.filter(
                project=project_with_single_owner
            ).count(),
            1,
            "Project should have exactly one owner membership before deletion attempt",
        )

        # Try to remove the only owner membership
        url = self.get_project_membership_delete_url(
            project_with_single_owner, self.owner_membership
        )
        self.client.force_login(self.owner)
        response = self.client.post(url, follow=True)

        self.assertRedirects(
            response,
            self.get_project_membership_list_url(project_with_single_owner),
        )
        self.assertContains(
            response,
            f"Cannot remove {self.owner.email}. Each project must have at least one owner.",
            status_code=200,
        )
        self.assertEqual(
            ProjectMembership.objects.filter(
                project=project_with_single_owner
            ).count(),
            1,
            "Project should have exactly one owner membership after deletion attempt",
        )
