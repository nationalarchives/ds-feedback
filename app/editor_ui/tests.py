from django.http import Http404
from django.test import TestCase
from django.urls import reverse

from app.editor_ui.factories import ProjectFactory, UserFactory
from app.editor_ui.mixins import ProjectMembershipRequiredMixin
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
                "domain": "owner.domain.com",
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
                "domain": "other.domain.com",
                "retention_period_days": RETENTION_PERIOD_CHOICES[0],
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            Project.objects.count(), 0, "No projects should be created"
        )


class ProjectMembershipTests(TestCase):
    """Tests for project membership assignment and access."""

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
                "domain": "owner.domain.com",
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


class DummyView(ProjectMembershipRequiredMixin):
    """
    Dummy view class for directly testing ProjectMembershipRequiredMixin methods.
    """

    def __init__(self, kwargs):
        self.kwargs = kwargs


class ProjectMembershipRequiredMixinTests(TestCase):
    """Tests for the project resolution logic in ProjectMembershipRequiredMixin."""

    @classmethod
    def setUpTestData(cls):
        """Set up a user and a project for all tests in this class."""
        cls.creator_user = UserFactory(add_project_creation_permission=True)
        cls.project = ProjectFactory.create(created_by=cls.creator_user)

    def test_get_project_returns_correct_project_with_valid_uuid(self):
        """
        get_project returns the correct Project instance when given a valid UUID.
        """
        view = DummyView(kwargs={"project_uuid": self.project.uuid})
        resolved_project = view.get_project()
        self.assertEqual(resolved_project, self.project)

    def test_get_project_raises_404_project_test_with_non_matching_uuid(self):
        """
        get_project raises Http404 when given a UUID that does not match any project.
        """
        non_matching_uuid = "00000000-0000-0000-0000-000000000000"
        view = DummyView(kwargs={"project_uuid": non_matching_uuid})
        with self.assertRaises(Http404):
            view.get_project()

    def test_get_project_raises_if_uuid_missing(self):
        """
        get_project raises ImproperlyConfigured if the UUID is missing from the kwargs.
        """
        view = DummyView(kwargs={})
        with self.assertRaisesMessage(
            Exception, "No project UUID found in URL kwargs"
        ):
            view.get_project(kwargs={})
