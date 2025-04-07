from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from app.feedback_forms.factories import FeedbackFormFactory
from app.feedback_forms.models import FeedbackForm, PathPattern
from app.projects.factories import ProjectFactory
from app.prompts.models import BinaryPrompt, Prompt, RangedPrompt, TextPrompt
from app.users.factories import StaffUserFactory
from app.utils.testing import (
    ResetFactorySequencesMixin,
    get_change_list_results,
    get_inline_formset,
    reverse_with_query,
)


class TestAdminFeedbackFormView(ResetFactorySequencesMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)

    # As an Admin user I can create a feedback form in Django admin
    def test_create_feedback_form(self):
        project = ProjectFactory.create(created_by=self.admin_user)

        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("admin:feedback_forms_feedbackform_add"),
            {
                "name": "Test Feedback Form",
                "project": project.pk,
                "path_patterns-TOTAL_FORMS": 1,
                "path_patterns-INITIAL_FORMS": 0,
                "prompts-TOTAL_FORMS": 1,
                "prompts-INITIAL_FORMS": 0,
                "prompts-0-text": "",
                "prompts-0-order": "",
                "prompts-0-max_length": "1000",
            },
        )
        list_url = reverse("admin:feedback_forms_feedbackform_changelist")
        self.assertRedirects(response, list_url)

        feedback_form = FeedbackForm.objects.get(name="Test Feedback Form")
        self.assertEqual(feedback_form.created_by, self.admin_user)

    # As an Admin user I can create a feedback form with multiple path patterns in Django admin
    def test_create_feedback_form_with_path_patterns(self):
        project = ProjectFactory.create(created_by=self.admin_user)

        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("admin:feedback_forms_feedbackform_add"),
            {
                "name": "Test feedback form",
                "project": project.pk,
                "path_patterns-TOTAL_FORMS": 2,
                "path_patterns-INITIAL_FORMS": 0,
                "path_patterns-0-pattern_with_wildcard": "/foo/*",
                "path_patterns-1-pattern_with_wildcard": "/bar",
                "prompts-TOTAL_FORMS": 1,
                "prompts-INITIAL_FORMS": 0,
                "prompts-0-text": "",
                "prompts-0-order": "",
                "prompts-0-max_length": "1000",
            },
        )
        list_url = reverse("admin:feedback_forms_feedbackform_changelist")
        self.assertRedirects(response, list_url)

        feedback_form = FeedbackForm.objects.prefetch_related(
            "path_patterns"
        ).get(name="Test feedback form")
        patterns = feedback_form.path_patterns.all()
        self.assertEqual(len(patterns), 2)
        self.assertEqual(patterns[0].pattern, "/foo/")
        self.assertEqual(patterns[0].is_wildcard, True)
        self.assertEqual(patterns[0].feedback_form, feedback_form)
        self.assertEqual(patterns[1].pattern, "/bar")
        self.assertEqual(patterns[1].is_wildcard, False)
        self.assertEqual(patterns[1].feedback_form, feedback_form)

    # As an Admin user I cannot create a feedback form with duplicate patterns in Django admin
    def test_create_feedback_form_with_duplicate_path_patterns(self):
        project = ProjectFactory.create(created_by=self.admin_user)

        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("admin:feedback_forms_feedbackform_add"),
            {
                "name": "Test feedback form",
                "project": project.pk,
                "path_patterns-TOTAL_FORMS": 2,
                "path_patterns-INITIAL_FORMS": 0,
                "path_patterns-0-pattern_with_wildcard": "/foo",
                "path_patterns-1-pattern_with_wildcard": "/foo",
                "prompts-TOTAL_FORMS": 1,
                "prompts-INITIAL_FORMS": 0,
                "prompts-0-text": "",
                "prompts-0-order": "",
                "prompts-0-max_length": "1000",
            },
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        path_pattern_formset = get_inline_formset(response.context, PathPattern)
        self.assertEqual(
            path_pattern_formset[1].errors["pattern_with_wildcard"],
            ["You cannot use the same pattern twice in a project."],
        )

    # As an Admin user I cannot create a feedback form which duplicates a pattern in the project in Django admin
    def test_create_feedback_form_with_duplicate_project_path_patterns(self):
        project = ProjectFactory.create(created_by=self.admin_user)

        FeedbackFormFactory.create(
            created_by=self.admin_user,
            project=project,
            path_patterns=["/foo", "/bar"],
        )

        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("admin:feedback_forms_feedbackform_add"),
            {
                "name": "Test feedback form",
                "project": project.pk,
                "path_patterns-TOTAL_FORMS": 2,
                "path_patterns-INITIAL_FORMS": 0,
                "path_patterns-0-pattern_with_wildcard": "/foo",
                "prompts-TOTAL_FORMS": 1,
                "prompts-INITIAL_FORMS": 0,
                "prompts-0-text": "",
                "prompts-0-order": "",
                "prompts-0-max_length": "1000",
            },
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        path_pattern_formset = get_inline_formset(response.context, PathPattern)
        self.assertEqual(
            path_pattern_formset[0].errors["pattern_with_wildcard"],
            ["You cannot use the same pattern twice in a project."],
        )

    # As an Admin user I can search for feedback forms in Django admin
    def test_search_feedback_forms(self):
        project = ProjectFactory.create(created_by=self.admin_user)
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

    # As an Admin user I can create a feedback form with multiple prompts in Django admin
    def test_create_feedback_form_with_text_prompts(self):
        project = ProjectFactory.create(created_by=self.admin_user)

        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("admin:feedback_forms_feedbackform_add"),
            {
                "name": "Test feedback form",
                "project": project.pk,
                "path_patterns-TOTAL_FORMS": 1,
                "path_patterns-INITIAL_FORMS": 0,
                "prompts-TOTAL_FORMS": 3,
                "prompts-INITIAL_FORMS": 0,
                "prompts-0-prompt_type": BinaryPrompt._meta.model_name,
                "prompts-0-text": "Was this page useful?",
                "prompts-0-order": "1",
                "prompts-1-prompt_type": TextPrompt._meta.model_name,
                "prompts-1-text": "How could it be improved?",
                "prompts-1-order": "2",
                "prompts-2-prompt_type": RangedPrompt._meta.model_name,
                "prompts-2-text": "How would you rate it?",
                "prompts-2-order": "3",
                "prompts-2-is_disabled": "on",
            },
        )
        list_url = reverse("admin:feedback_forms_feedbackform_changelist")
        self.assertRedirects(response, list_url)

        feedback_form = FeedbackForm.objects.prefetch_related(
            "path_patterns"
        ).get(name="Test feedback form")
        prompts = feedback_form.prompts.all().select_subclasses()
        self.assertEqual(len(prompts), 3)
        self.assertIsInstance(prompts[0], BinaryPrompt)
        self.assertEqual(prompts[0].text, "Was this page useful?")
        self.assertEqual(prompts[0].order, 1)
        self.assertIsInstance(prompts[1], TextPrompt)
        self.assertEqual(prompts[1].text, "How could it be improved?")
        self.assertEqual(prompts[1].order, 2)
        self.assertIsInstance(prompts[2], RangedPrompt)
        self.assertEqual(prompts[2].text, "How would you rate it?")
        self.assertEqual(prompts[2].order, 3)
        self.assertEqual(prompts[2].disabled_by, self.admin_user)

    # As an Admin user I cannot create a feedback form with more than 3 enabled text prompts in Django admin
    def test_create_feedback_form_with_excessive_text_prompts(self):
        project = ProjectFactory.create(created_by=self.admin_user)

        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("admin:feedback_forms_feedbackform_add"),
            {
                "name": "Test feedback form",
                "project": project.pk,
                "path_patterns-TOTAL_FORMS": 1,
                "path_patterns-INITIAL_FORMS": 0,
                "prompts-TOTAL_FORMS": 4,
                "prompts-INITIAL_FORMS": 0,
                "prompts-0-prompt_type": BinaryPrompt._meta.model_name,
                "prompts-0-text": "Was this page useful?",
                "prompts-0-order": "1",
                "prompts-1-prompt_type": TextPrompt._meta.model_name,
                "prompts-1-text": "How could it be improved?",
                "prompts-1-order": "2",
                "prompts-2-prompt_type": RangedPrompt._meta.model_name,
                "prompts-2-text": "How would you rate it?",
                "prompts-2-order": "3",
                "prompts-3-prompt_type": TextPrompt._meta.model_name,
                "prompts-3-text": "What else would you like to know?",
                "prompts-3-order": "4",
            },
        )

        text_prompt_formset = get_inline_formset(response.context, Prompt)
        self.assertEqual(
            text_prompt_formset[3].errors["text"],
            ["You cannot have more than 3 enabled prompts"],
        )

    # As an Admin user I cannot create a feedback form with text prompts with a duplicate order in Django admin
    def test_create_feedback_form_with_duplicate_order_text_prompts(self):
        project = ProjectFactory.create(created_by=self.admin_user)

        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("admin:feedback_forms_feedbackform_add"),
            {
                "name": "Test feedback form",
                "project": project.pk,
                "path_patterns-TOTAL_FORMS": 1,
                "path_patterns-INITIAL_FORMS": 0,
                "prompts-TOTAL_FORMS": 3,
                "prompts-INITIAL_FORMS": 0,
                "prompts-0-prompt_type": BinaryPrompt._meta.model_name,
                "prompts-0-text": "Was this page useful?",
                "prompts-0-order": "1",
                "prompts-1-prompt_type": TextPrompt._meta.model_name,
                "prompts-1-text": "How could it be improved?",
                "prompts-1-order": "2",
                "prompts-2-prompt_type": RangedPrompt._meta.model_name,
                "prompts-2-text": "How would you rate it?",
                "prompts-2-order": "2",
            },
        )

        text_prompt_formset = get_inline_formset(response.context, Prompt)
        self.assertEqual(
            text_prompt_formset[2].errors["order"],
            ["This order number is used in another prompt"],
        )
