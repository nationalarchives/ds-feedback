from datetime import datetime
from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from app.feedback_forms.factories import FeedbackFormFactory
from app.feedback_forms.models import FeedbackForm
from app.projects.factories import ProjectFactory
from app.users.factories import StaffUserFactory
from app.utils.testing import get_change_list_results, reverse_with_query


class TestAdminProjectsView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)

    # As an Admin user I can create a feedback form in Django admin
    def test_create_feedback_form(self):
        project = ProjectFactory.create(
            created_at=datetime(2000, 1, 2), created_by=self.admin_user
        )

        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("admin:feedback_forms_feedbackform_add"),
            {
                "name": "Test Feedback Form",
                "project": project.pk,
                "path_patterns-TOTAL_FORMS": 1,
                "path_patterns-INITIAL_FORMS": 0,
            },
        )
        list_url = reverse("admin:feedback_forms_feedbackform_changelist")
        self.assertRedirects(response, list_url)

        feedback_form = FeedbackForm.objects.prefetch_related(
            "path_patterns"
        ).get(name="Test Feedback Form")

        self.assertEqual(feedback_form.created_by, self.admin_user)

    # As an Admin user I can create a feedback form with multiple path patterns in Django admin
    def test_create_feedback_form_with_path_patterns(self):
        project = ProjectFactory.create(
            created_at=datetime(2000, 1, 2), created_by=self.admin_user
        )

        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("admin:feedback_forms_feedbackform_add"),
            {
                "name": "Test feedback form",
                "project": project.pk,
                "path_patterns-TOTAL_FORMS": 2,
                "path_patterns-INITIAL_FORMS": 0,
                "path_patterns-0-pattern": "/foo/*",
                "path_patterns-1-pattern": "/bar",
            },
        )
        list_url = reverse("admin:feedback_forms_feedbackform_changelist")
        self.assertRedirects(response, list_url)

        feedback_form = FeedbackForm.objects.prefetch_related(
            "path_patterns"
        ).get(name="Test feedback form")

        patterns = feedback_form.path_patterns.all()
        self.assertEqual(len(patterns), 2)
        self.assertEqual(patterns[0].pattern, "/foo/*")
        self.assertEqual(patterns[0].feedback_form, feedback_form)
        self.assertEqual(patterns[1].pattern, "/bar")
        self.assertEqual(patterns[1].feedback_form, feedback_form)

    # As a Django Admin user I can search for feedback forms in Django admin
    def test_search_feedback_forms(self):
        project = ProjectFactory.create(
            created_at=datetime(2000, 1, 2), created_by=self.admin_user
        )
        feedback_form_1 = FeedbackFormFactory.create(
            created_by=self.admin_user,
            project=project,
            path_patterns=["/foo/*", "/bar"],
        )
        feedback_form_2 = FeedbackFormFactory.create(
            created_by=self.admin_user,
            project=project,
            path_patterns=["/foo/zim"],
        )
        FeedbackFormFactory.create(
            created_by=self.admin_user,
            project=project,
            path_patterns=[],
        )
        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse_with_query(
                "admin:feedback_forms_feedbackform_changelist", {"q": "/foo"}
            )
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            get_change_list_results(response),
            [feedback_form_1, feedback_form_2],
        )
