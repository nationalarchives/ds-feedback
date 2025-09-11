from django.test import TestCase
from django.urls import reverse

from app.editor_ui.factories import UserFactory
from app.feedback_forms.factories import FeedbackFormFactory, PathPatternFactory
from app.projects.factories import ProjectFactory
from app.projects.models import ProjectMembership


class FeedbackFormAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.owner = UserFactory()
        cls.editor = UserFactory()
        cls.other_user = UserFactory()
        cls.superuser = UserFactory(is_superuser=True)

        # Users authorised to access feedback forms list/create/detail/delete
        cls.authorised_users = [cls.superuser, cls.owner, cls.editor]

        # Project, membership and feedback form
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

        # Another project/feedback form for cross-project access tests
        cls.other_project = ProjectFactory(created_by=cls.superuser)
        cls.other_feedback_form = FeedbackFormFactory(
            project=cls.other_project, created_by=cls.superuser
        )

    def get_feedback_form_list_url(self, project):
        """Helper to get feedback form list URL."""
        return reverse(
            "editor_ui:project__feedback_form_list",
            args=[str(project.uuid)],
        )

    def get_feedback_form_detail_url(self, project, feedback_form):
        """Helper to get feedback form detail URL."""
        return reverse(
            "editor_ui:project__feedback_form_detail",
            args=[
                str(project.uuid),
                str(feedback_form.uuid),
            ],
        )

    def get_feedback_form_create_url(self, project):
        """Helper to get feedback form create URL."""
        return reverse(
            "editor_ui:project__feedback_form_create",
            args=[str(project.uuid)],
        )

    def get_feedback_form_delete_url(self, project, feedback_form):
        """Helper to get the feedback form delete URL."""
        return reverse(
            "editor_ui:project__feedback_form_delete",
            kwargs={
                "project_uuid": str(project.uuid),
                "feedback_form_uuid": str(feedback_form.uuid),
            },
        )

    def test_authorised_users_can_access_feedback_form_views(self):
        for user in self.authorised_users:
            for url in [
                self.get_feedback_form_list_url(self.project),
                self.get_feedback_form_create_url(self.project),
                self.get_feedback_form_detail_url(
                    self.project, self.feedback_form
                ),
                self.get_feedback_form_delete_url(
                    self.project, self.feedback_form
                ),
            ]:
                with self.subTest(user=user, url=url):
                    self.client.force_login(user)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)

    def test_unauthorised_user_cannot_access_feedback_form_views(self):
        for url in [
            self.get_feedback_form_list_url(self.project),
            self.get_feedback_form_create_url(self.project),
            self.get_feedback_form_detail_url(self.project, self.feedback_form),
            self.get_feedback_form_delete_url(self.project, self.feedback_form),
        ]:
            with self.subTest(url=url):
                self.client.force_login(self.other_user)
                response = self.client.get(url)
                self.assertIn(response.status_code, (403, 404))

    def test_owner_cannot_access_feedback_form_views_for_other_project(self):
        for url in [
            self.get_feedback_form_list_url(self.other_project),
            self.get_feedback_form_create_url(self.other_project),
            self.get_feedback_form_detail_url(
                self.other_project, self.other_feedback_form
            ),
            self.get_feedback_form_delete_url(
                self.other_project, self.other_feedback_form
            ),
        ]:
            with self.subTest(url=url):
                self.client.force_login(self.owner)
                response = self.client.get(url)
                self.assertIn(response.status_code, (403, 404))

    def test_cross_uuid_feedback_form_detail_denied(self):
        """
        User cannot access a feedback form by mixing project and feedback form UUIDs from different projects.
        """
        self.client.force_login(self.owner)
        response = self.client.get(
            self.get_feedback_form_detail_url(
                self.project, self.other_feedback_form
            )
        )
        self.assertIn(response.status_code, (403, 404))

    def test_nonexistent_feedback_form_returns_404(self):
        self.client.force_login(self.owner)
        url = self.get_feedback_form_detail_url(
            self.project,
            type(
                "Fake", (), {"uuid": "00000000-0000-0000-0000-000000000000"}
            )(),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class PathPatternAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.owner = UserFactory()
        cls.editor = UserFactory()
        cls.other_user = UserFactory()
        cls.superuser = UserFactory(is_superuser=True)

        # Users authorised to access path patterns create/update/delete
        cls.authorised_users = [cls.superuser, cls.owner, cls.editor]

        # Project, membership, feedback form and path pattern
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
        cls.path_pattern = PathPatternFactory(
            pattern="Path Pattern", feedback_form=cls.feedback_form
        )

        # Another project/feedback form/path pattern for cross-project access tests
        cls.other_project = ProjectFactory(created_by=cls.superuser)
        cls.other_feedback_form = FeedbackFormFactory(
            project=cls.other_project, created_by=cls.superuser
        )
        cls.other_path_pattern = PathPatternFactory(
            pattern="Other Path Pattern", feedback_form=cls.other_feedback_form
        )

    def get_feedback_form_detail_url(self, project, feedback_form):
        """Helper to get feedback form detail URL."""
        return reverse(
            "editor_ui:project__feedback_form_detail",
            args=[
                str(project.uuid),
                str(feedback_form.uuid),
            ],
        )

    def get_path_pattern_create_url(self, project, feedback_form):
        return reverse(
            "editor_ui:project__feedback_form__path_pattern_create",
            args=[str(project.uuid), str(feedback_form.uuid)],
        )

    def get_path_pattern_update_url(self, project, feedback_form, path_pattern):
        return reverse(
            "editor_ui:project__feedback_form__path_pattern_edit",
            args=[
                str(project.uuid),
                str(feedback_form.uuid),
                str(path_pattern.uuid),
            ],
        )

    def get_path_pattern_delete_url(self, project, feedback_form, path_pattern):
        """Helper to get the path pattern delete URL."""
        return reverse(
            "editor_ui:project__feedback_form__path_pattern_delete",
            kwargs={
                "project_uuid": str(project.uuid),
                "feedback_form_uuid": str(feedback_form.uuid),
                "path_pattern_uuid": str(path_pattern.uuid),
            },
        )

    def test_authorised_users_can_access_path_pattern_views(self):
        for user in self.authorised_users:
            for url in [
                self.get_path_pattern_create_url(
                    self.project, self.feedback_form
                ),
                self.get_path_pattern_update_url(
                    self.project, self.feedback_form, self.path_pattern
                ),
                self.get_path_pattern_delete_url(
                    self.project, self.feedback_form, self.path_pattern
                ),
            ]:
                with self.subTest(user=user, url=url):
                    self.client.force_login(user)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)

    def test_unauthorised_user_cannot_access_path_pattern_views(self):
        for url in [
            self.get_path_pattern_create_url(self.project, self.feedback_form),
            self.get_path_pattern_update_url(
                self.project, self.feedback_form, self.path_pattern
            ),
            self.get_path_pattern_delete_url(
                self.project, self.feedback_form, self.path_pattern
            ),
        ]:
            with self.subTest(url=url):
                self.client.force_login(self.other_user)
                response = self.client.get(url)
                self.assertIn(response.status_code, (403, 404))

    def test_owner_cannot_access_path_pattern_create_for_other_project(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            self.get_path_pattern_create_url(
                self.other_project, self.other_feedback_form
            )
        )
        self.assertIn(response.status_code, (403, 404))

    def test_authenticated_users_can_view_path_pattern_in_feedback_form_detail(
        self,
    ):
        for user in self.authorised_users:
            with self.subTest(user=user):
                self.client.force_login(user)
                response = self.client.get(
                    self.get_feedback_form_detail_url(
                        self.project, self.feedback_form
                    )
                )
                self.assertContains(
                    response, self.path_pattern.pattern, status_code=200
                )
