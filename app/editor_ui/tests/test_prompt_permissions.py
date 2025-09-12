from django.test import TestCase
from django.urls import reverse

from app.editor_ui.factories import UserFactory
from app.feedback_forms.factories import FeedbackFormFactory
from app.projects.factories import ProjectFactory
from app.projects.models import ProjectMembership
from app.prompts.factories import (
    RangedPromptFactory,
    RangedPromptOptionFactory,
    TextPromptFactory,
)


class PromptAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.owner = UserFactory(email="owner@example.com")
        cls.editor = UserFactory(email="editor@example.com")
        cls.other_user = UserFactory(email="other_user@example.com")
        cls.superuser = UserFactory(
            email="superuser@example.com", is_superuser=True
        )

        # Users authorised to access prompts create/update/delete views
        cls.authorised_users = [cls.superuser, cls.owner, cls.editor]

        # Project, membership, feedback form and prompt
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

    def get_feedback_form_detail_url(self, project, feedback_form):
        return reverse(
            "editor_ui:project__feedback_form_detail",
            args=[
                str(project.uuid),
                str(feedback_form.uuid),
            ],
        )

    def get_prompt_create_url(self, project, feedback_form):
        return reverse(
            "editor_ui:project__feedback_form__prompt_create",
            args=[str(project.uuid), str(feedback_form.uuid)],
        )

    def get_prompt_detail_url(self, project, feedback_form, prompt):
        return reverse(
            "editor_ui:project__feedback_form__prompt_detail",
            args=[
                str(project.uuid),
                str(feedback_form.uuid),
                str(prompt.uuid) if hasattr(prompt, "uuid") else prompt,
            ],
        )

    def get_prompt_update_url(self, project, feedback_form, prompt):
        return reverse(
            "editor_ui:project__feedback_form__prompt_edit",
            args=[
                str(project.uuid),
                str(feedback_form.uuid),
                str(prompt.uuid),
            ],
        )

    def test_authorised_users_can_view_prompt_in_feedback_form_detail(self):
        for user in self.authorised_users:
            with self.subTest(user=user):
                self.client.force_login(user)
                response = self.client.get(
                    self.get_feedback_form_detail_url(
                        self.project, self.feedback_form
                    )
                )
                self.assertContains(response, self.prompt.text, status_code=200)

    def test_authorised_users_can_access_prompt_detail(self):
        for user in self.authorised_users:
            for url in [
                self.get_prompt_create_url(self.project, self.feedback_form),
                self.get_prompt_detail_url(
                    self.project, self.feedback_form, self.prompt
                ),
                self.get_prompt_update_url(
                    self.project, self.feedback_form, self.prompt
                ),
            ]:
                with self.subTest(user=user, url=url):
                    self.client.force_login(user)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_cannot_access_prompt_views(self):
        for url in [
            self.get_prompt_create_url(self.project, self.feedback_form),
            self.get_prompt_detail_url(
                self.project, self.feedback_form, self.prompt
            ),
            self.get_prompt_update_url(
                self.project, self.feedback_form, self.prompt
            ),
        ]:
            with self.subTest(url=url):
                self.client.force_login(self.other_user)
                response = self.client.get(url)
                self.assertIn(response.status_code, (403, 404))

    def test_other_user_cannot_access_prompt_detail(self):
        self.client.force_login(self.other_user)
        response = self.client.get(
            self.get_prompt_detail_url(
                self.project, self.feedback_form, self.prompt
            )
        )
        self.assertIn(response.status_code, (403, 404))

    def test_owner_cannot_access_prompt_create_for_other_project(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            self.get_prompt_create_url(
                self.other_project, self.other_feedback_form
            )
        )
        self.assertIn(response.status_code, (403, 404))

    def test_owner_can_only_view_related_prompts_in_feedback_form_detail_view(
        self,
    ):
        self.client.force_login(self.owner)
        response = self.client.get(
            self.get_feedback_form_detail_url(self.project, self.feedback_form)
        )
        self.assertNotContains(
            response, self.other_prompt.text, status_code=200
        )

    def test_owner_cannot_access_prompt_from_other_project_with_no_membership(
        self,
    ):
        self.client.force_login(self.owner)
        response = self.client.get(
            self.get_prompt_detail_url(
                self.project, self.other_feedback_form, self.other_prompt
            )
        )
        self.assertIn(response.status_code, (403, 404))

    def test_nonexistent_prompt_returns_404(self):
        self.client.force_login(self.owner)
        url = self.get_prompt_detail_url(
            self.project,
            self.feedback_form,
            prompt="00000000-0000-0000-0000-000000000000",
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_cross_uuid_prompt_detail_denied(self):
        """
        User cannot access a prompt by mixing project, feedback form, and prompt UUIDs from different projects.
        """
        self.client.force_login(self.owner)
        response = self.client.get(
            self.get_prompt_detail_url(
                self.project, self.other_feedback_form, self.other_prompt
            )
        )
        self.assertIn(response.status_code, (403, 404))


class RangedPromptAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.owner = UserFactory()
        cls.editor = UserFactory()
        cls.other_user = UserFactory()
        cls.superuser = UserFactory(is_superuser=True)

        # Users authorised to access ranged prompt options create/update/delete views
        cls.authorised_users = [cls.superuser, cls.owner, cls.editor]

        # Project, membership, feedback form and ranged prompt
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
        cls.feedback_form = FeedbackFormFactory(
            project=cls.project, created_by=cls.owner
        )

        cls.ranged_prompt = RangedPromptFactory(
            text="Ranged Prompt",
            feedback_form=cls.feedback_form,
            created_by=cls.owner,
        )
        cls.ranged_prompt_option = RangedPromptOptionFactory(
            ranged_prompt=cls.ranged_prompt,
            label="Ranged Prompt Option",
            value=1,
        )

        # Another project/feedback form/ranged prompt for cross-project access tests
        cls.other_project = ProjectFactory(created_by=cls.superuser)
        cls.other_feedback_form = FeedbackFormFactory(
            project=cls.other_project, created_by=cls.superuser
        )
        cls.other_ranged_prompt = RangedPromptFactory(
            text="Other Ranged Prompt",
            feedback_form=cls.other_feedback_form,
            created_by=cls.superuser,
        )
        cls.other_ranged_prompt_option = RangedPromptOptionFactory(
            ranged_prompt=cls.other_ranged_prompt,
            label="Other Ranged Prompt Option",
            value=10,
        )

    def get_prompt_detail_url(self, project, form, prompt):
        return reverse(
            "editor_ui:project__feedback_form__prompt_detail",
            args=[
                str(project.uuid),
                str(form.uuid),
                str(prompt.uuid) if hasattr(prompt, "uuid") else prompt,
            ],
        )

    def get_ranged_prompt_options_create_url(
        self, project, form, ranged_prompt
    ):
        return reverse(
            "editor_ui:project__feedback_form__prompt__ranged_prompt_options_create",
            args=[str(project.uuid), str(form.uuid), str(ranged_prompt.uuid)],
        )

    def get_ranged_prompt_options_update_url(
        self, project, form, ranged_prompt, ranged_prompt_option
    ):
        return reverse(
            "editor_ui:project__feedback_form__prompt__ranged_prompt_options_edit",
            args=[
                str(project.uuid),
                str(form.uuid),
                str(ranged_prompt.uuid),
                str(ranged_prompt_option.uuid),
            ],
        )

    def get_ranged_prompt_options_delete_url(
        self, project, form, ranged_prompt, ranged_prompt_option
    ):
        return reverse(
            "editor_ui:project__feedback_form__prompt__ranged_prompt_options_delete",
            args=[
                str(project.uuid),
                str(form.uuid),
                str(ranged_prompt.uuid),
                str(ranged_prompt_option.uuid),
            ],
        )

    def test_authorised_users_can_view_ranged_prompts_options_in_prompt_detail(
        self,
    ):
        for user in self.authorised_users:
            with self.subTest(user=user):
                self.client.force_login(user)
                response = self.client.get(
                    self.get_prompt_detail_url(
                        self.project, self.feedback_form, self.ranged_prompt
                    )
                )
                self.assertContains(
                    response, self.ranged_prompt_option.label, status_code=200
                )

    def test_authorised_users_can_access_ranged_prompt_options_views(self):
        for user in self.authorised_users:
            for url in [
                self.get_ranged_prompt_options_create_url(
                    self.project, self.feedback_form, self.ranged_prompt
                ),
                self.get_ranged_prompt_options_update_url(
                    self.project,
                    self.feedback_form,
                    self.ranged_prompt,
                    self.ranged_prompt_option,
                ),
                self.get_ranged_prompt_options_delete_url(
                    self.project,
                    self.feedback_form,
                    self.ranged_prompt,
                    self.ranged_prompt_option,
                ),
            ]:
                with self.subTest(user=user, url=url):
                    self.client.force_login(user)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)

    def test_unauthorised_users_cannot_access_ranged_prompt_options_views(self):
        for url in [
            self.get_ranged_prompt_options_create_url(
                self.project, self.feedback_form, self.ranged_prompt
            ),
            self.get_ranged_prompt_options_update_url(
                self.project,
                self.feedback_form,
                self.ranged_prompt,
                self.ranged_prompt_option,
            ),
            self.get_ranged_prompt_options_delete_url(
                self.project,
                self.feedback_form,
                self.ranged_prompt,
                self.ranged_prompt_option,
            ),
        ]:
            with self.subTest(url=url):
                self.client.force_login(self.other_user)
                response = self.client.get(url)
                self.assertIn(response.status_code, (403, 404))

    def test_owner_cannot_access_ranged_prompt_options_create_for_other_project(
        self,
    ):
        self.client.force_login(self.owner)
        response = self.client.get(
            self.get_ranged_prompt_options_create_url(
                self.other_project,
                self.other_feedback_form,
                self.other_ranged_prompt,
            )
        )
        self.assertIn(response.status_code, (403, 404))

    def test_cross_uuid_ranged_prompt_options_create_denied(self):
        """
        User cannot access ranged prompt options create by mixing project, feedback form, and ranged prompt UUIDs from different projects.
        """
        self.client.force_login(self.owner)
        response = self.client.get(
            self.get_ranged_prompt_options_create_url(
                self.project, self.other_feedback_form, self.other_ranged_prompt
            )
        )
        self.assertIn(response.status_code, (403, 404))

    def test_nonexistent_ranged_prompt_returns_404(self):
        self.client.force_login(self.owner)
        url = self.get_ranged_prompt_options_create_url(
            self.project,
            self.feedback_form,
            type(
                "Fake", (), {"uuid": "00000000-0000-0000-0000-000000000000"}
            )(),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
