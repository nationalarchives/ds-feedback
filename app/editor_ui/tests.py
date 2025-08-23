from django.test import TestCase
from django.urls import reverse

from app.editor_ui.factories import UserFactory
from app.feedback_forms.factories import FeedbackFormFactory
from app.projects.factories import ProjectFactory
from app.projects.models import (
    RETENTION_PERIOD_CHOICES,
    Project,
    ProjectMembership,
)
from app.prompts.factories import TextPromptFactory


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


class ProjectMembershipAccessTests(TestCase):
    def setUp(self):
        # User1 owns project1 and its feedback form
        self.project_1_owner = UserFactory()
        self.project_1 = ProjectFactory(created_by=self.project_1_owner)
        self.project_1_form = FeedbackFormFactory(
            project=self.project_1, created_by=self.project_1_owner
        )
        ProjectMembership.objects.create(
            project=self.project_1,
            user=self.project_1_owner,
            role="owner",
            created_by=self.project_1_owner,
        )

        # User2 owns project2 and its feedback form
        self.project_2_owner = UserFactory()
        self.project_2 = ProjectFactory(created_by=self.project_2_owner)
        self.project_2_form = FeedbackFormFactory(
            project=self.project_2, created_by=self.project_2_owner
        )
        ProjectMembership.objects.create(
            project=self.project_2,
            user=self.project_2_owner,
            role="owner",
            created_by=self.project_2_owner,
        )

        # Add a prompt to form2 (which owner should NOT be able to access)
        self.project_2_form_prompt = TextPromptFactory(
            feedback_form=self.project_2_form, created_by=self.project_2_owner
        )

    def test_user_cannot_access_prompt_from_other_project(self):
        """
        Ensure a user cannot access a prompt from a feedback form in a project they do not belong to,
        even if they know the prompt's and feedback form's UUIDs.
        """
        self.client.force_login(self.project_1_owner)
        # Try to access prompt2 (from project2) using project1's UUID in the URL
        url = reverse(
            "editor_ui:project__feedback_form__prompt_detail",
            args=[
                str(self.project_1.uuid),
                str(self.project_2_form.uuid),
                str(self.project_2_form_prompt.uuid),
            ],
        )
        response = self.client.get(url)
        self.assertIn(
            response.status_code,
            (403, 404),
            "Should not allow cross-project access to nested resources",
        )
