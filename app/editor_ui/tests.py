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
from app.prompts.models import Prompt, TextPrompt


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
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.owner = UserFactory()
        cls.editor = UserFactory()
        cls.other_user = UserFactory()
        cls.superuser = UserFactory(is_superuser=True)

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

        # Feedback form and prompt
        cls.feedback_form = FeedbackFormFactory(
            project=cls.project, created_by=cls.owner
        )
        cls.prompt = TextPromptFactory(
            text="Standard Prompt",
            feedback_form=cls.feedback_form,
            created_by=cls.owner,
        )

        # Another project/feedback form/prompt for cross-project access tests
        cls.other_project = ProjectFactory(created_by=cls.superuser)
        cls.other_feedback_form = FeedbackFormFactory(
            project=cls.other_project, created_by=cls.superuser
        )
        cls.other_prompt = TextPromptFactory(
            text="Other Prompt",
            feedback_form=cls.other_feedback_form,
            created_by=cls.superuser,
        )

    def prompt_detail_url(self, project, form, prompt: Prompt | str):
        return reverse(
            "editor_ui:project__feedback_form__prompt_detail",
            args=[
                str(project.uuid),
                str(form.uuid),
                str(prompt.uuid) if isinstance(prompt, TextPrompt) else prompt,
            ],
        )

    def prompt_create_url(self, project, form):
        return reverse(
            "editor_ui:project__feedback_form__prompt_create",
            args=[str(project.uuid), str(form.uuid)],
        )

    def feedback_form_detail_url(self, project, form):
        return reverse(
            "editor_ui:project__feedback_form_detail",
            args=[
                str(project.uuid),
                str(form.uuid),
            ],
        )

    def test_owner_can_access_prompt_detail(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            self.prompt_detail_url(
                self.project, self.feedback_form, self.prompt
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_editor_can_access_prompt_detail(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            self.prompt_detail_url(
                self.project, self.feedback_form, self.prompt
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_access_prompt_detail(self):
        self.client.force_login(self.other_user)
        response = self.client.get(
            self.prompt_detail_url(
                self.project, self.feedback_form, self.prompt
            )
        )
        self.assertIn(response.status_code, (403, 404))

    def test_superuser_can_access_prompt_detail(self):
        self.client.force_login(self.superuser)
        response = self.client.get(
            self.prompt_detail_url(
                self.project, self.feedback_form, self.prompt
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_redirected(self):
        response = self.client.get(
            self.prompt_detail_url(
                self.project, self.feedback_form, self.prompt
            )
        )
        self.assertIn(response.status_code, (302, 403))

    def test_owner_cannot_access_prompt_from_other_project_with_no_membership(
        self,
    ):
        self.client.force_login(self.owner)
        response = self.client.get(
            self.prompt_detail_url(
                self.project, self.other_feedback_form, self.other_prompt
            )
        )
        self.assertIn(response.status_code, (403, 404))

    def test_nonexistent_prompt_returns_404(self):
        self.client.force_login(self.owner)
        url = self.prompt_detail_url(
            self.project,
            self.feedback_form,
            prompt="00000000-0000-0000-0000-000000000000",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_owner_can_view_prompt_in_feedback_form_detail_view(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            self.feedback_form_detail_url(self.project, self.feedback_form)
        )
        self.assertContains(response, self.prompt.text, status_code=200)

    def test_owner_can_only_view_related_prompts_in_feedback_form_detail_view(
        self,
    ):
        self.client.force_login(self.owner)
        response = self.client.get(
            self.feedback_form_detail_url(self.project, self.feedback_form)
        )
        self.assertNotContains(response, self.other_prompt, 200)

    def test_owner_can_access_prompt_create(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            self.prompt_create_url(self.project, self.feedback_form)
        )
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_access_prompt_create(self):
        self.client.force_login(self.other_user)
        response = self.client.get(
            self.prompt_create_url(self.project, self.feedback_form)
        )
        self.assertIn(response.status_code, (403, 404))

    def test_removed_user_loses_access(self):
        ProjectMembership.objects.filter(
            user=self.editor, project=self.project
        ).delete()
        self.client.force_login(self.editor)
        response = self.client.get(
            self.prompt_detail_url(
                self.project, self.feedback_form, self.prompt
            )
        )
        self.assertIn(response.status_code, (403, 404))
