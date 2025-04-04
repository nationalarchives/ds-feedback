from http import HTTPStatus

from django.urls import reverse

from rest_framework.test import APITestCase

from app.api.factories import APIAccessLifespanFactory, TokenFactory
from app.api.types import APIRole
from app.feedback_forms.factories import FeedbackFormFactory, PathPatternFactory
from app.projects.factories import ProjectFactory
from app.prompts.factories import (
    BinaryPromptFactory,
    RangedPromptFactory,
    RangedPromptOptionFactory,
    TextPromptFactory,
)
from app.users.factories import StaffUserFactory, UserFactory
from app.utils.testing import (
    ResetFactorySequencesMixin,
    ignore_request_warnings,
)


class TestFeedbackFormDetail(APITestCase, ResetFactorySequencesMixin):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.token = TokenFactory(user=cls.user)

        cls.admin_user = StaffUserFactory(is_superuser=True)
        cls.admin_token = TokenFactory(user=cls.admin_user)

        cls.project = ProjectFactory.create(created_by=cls.admin_user)

        cls.feedback_form = FeedbackFormFactory.create(
            name="Test feedback form",
            project=cls.project,
            created_by=cls.admin_user,
        )

        cls.text_prompt = TextPromptFactory.create(
            created_by=cls.admin_user,
            feedback_form=cls.feedback_form,
            order=1,
            text="How could it be improved?",
        )
        cls.binary_prompt = BinaryPromptFactory.create(
            created_by=cls.admin_user,
            feedback_form=cls.feedback_form,
            order=2,
            text="Was this page helpful?",
            positive_answer_label="Yes",
            negative_answer_label="No",
        )
        cls.ranged_prompt = RangedPromptFactory.create(
            created_by=cls.admin_user,
            feedback_form=cls.feedback_form,
            order=3,
            text="Are you satisfied with page?",
        )
        cls.option_1 = RangedPromptOptionFactory.create(
            ranged_prompt=cls.ranged_prompt,
            label="Unsatisfied",
        )
        cls.option_2 = RangedPromptOptionFactory.create(
            ranged_prompt=cls.ranged_prompt,
            label="Neutral",
        )
        cls.option_3 = RangedPromptOptionFactory.create(
            ranged_prompt=cls.ranged_prompt,
            label="Satisfied",
        )

    def test_get_feedback_form(self):
        response = self.client.get(
            reverse(
                "api:feedback-form_detail",
                kwargs={
                    "project": self.project.uuid,
                    "id": self.feedback_form.uuid,
                },
            ),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertEqual(response.data["name"], "Test feedback form")
        self.assertEqual(response.data["is_enabled"], True)
        self.assertEqual(len(response.data["prompts"]), 3)

        prompt_1 = response.data["prompts"][0]
        self.assertEqual(prompt_1["prompt_type"], self.text_prompt.type())
        self.assertEqual(prompt_1["text"], self.text_prompt.text)
        self.assertEqual(prompt_1["is_enabled"], self.text_prompt.is_enabled())
        self.assertEqual(prompt_1["max_length"], self.text_prompt.max_length)

        prompt_2 = response.data["prompts"][1]
        self.assertEqual(prompt_2["prompt_type"], self.binary_prompt.type())
        self.assertEqual(prompt_2["text"], self.binary_prompt.text)
        self.assertEqual(
            prompt_2["is_enabled"], self.binary_prompt.is_enabled()
        )
        self.assertEqual(
            prompt_2["positive_answer_label"],
            self.binary_prompt.positive_answer_label,
        )
        self.assertEqual(
            prompt_2["negative_answer_label"],
            self.binary_prompt.negative_answer_label,
        )

        prompt_3 = response.data["prompts"][2]
        self.assertEqual(prompt_3["prompt_type"], self.ranged_prompt.type())
        self.assertEqual(prompt_3["text"], self.ranged_prompt.text)
        self.assertEqual(
            prompt_3["is_enabled"], self.ranged_prompt.is_enabled()
        )
        self.assertEqual(len(prompt_3["options"]), 3)
        self.assertEqual(prompt_3["options"][0]["label"], self.option_1.label)
        self.assertEqual(prompt_3["options"][1]["label"], self.option_2.label)
        self.assertEqual(prompt_3["options"][2]["label"], self.option_3.label)

    def test_get_feedback_form_with_explore_role(self):
        APIAccessLifespanFactory(
            project=self.project,
            grantee=self.user,
            role=APIRole.READ_ONLY,
            created_by=self.admin_user,
        )

        response = self.client.get(
            reverse(
                "api:feedback-form_detail",
                kwargs={
                    "project": self.project.uuid,
                    "id": self.feedback_form.uuid,
                },
            ),
            headers={"Authorization": f"Token {self.token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_feedback_form_with_submit_role(self):
        APIAccessLifespanFactory(
            project=self.project,
            grantee=self.user,
            role=APIRole.RESPONSE_SUBMITTER,
            created_by=self.admin_user,
        )

        response = self.client.get(
            reverse(
                "api:feedback-form_detail",
                kwargs={
                    "project": self.project.uuid,
                    "id": self.feedback_form.uuid,
                },
            ),
            headers={"Authorization": f"Token {self.token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_feedback_form_fails_without_role(self):
        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:feedback-form_detail",
                    kwargs={
                        "project": self.project.uuid,
                        "id": self.feedback_form.uuid,
                    },
                ),
                headers={"Authorization": f"Token {self.token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_feedback_form_fails_without_auth(self):
        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:feedback-form_detail",
                    kwargs={
                        "project": self.project.uuid,
                        "id": self.feedback_form.uuid,
                    },
                ),
            )

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)


class TestFeedbackFormList(APITestCase, ResetFactorySequencesMixin):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.token = TokenFactory(user=cls.user)

        cls.admin_user = StaffUserFactory(is_superuser=True)
        cls.admin_token = TokenFactory(user=cls.admin_user)

        cls.project_1 = ProjectFactory.create(created_by=cls.admin_user)
        cls.project_2 = ProjectFactory.create(created_by=cls.admin_user)

        cls.feedback_form_1 = FeedbackFormFactory.create(
            name="Test feedback form 1",
            project=cls.project_1,
            created_by=cls.admin_user,
        )

        cls.feedback_form_2 = FeedbackFormFactory.create(
            name="Test feedback form 2",
            project=cls.project_1,
            created_by=cls.admin_user,
        )

        cls.feedback_form_3 = FeedbackFormFactory.create(
            name="Test feedback form 3",
            project=cls.project_2,
            created_by=cls.admin_user,
        )

        cls.text_prompt = TextPromptFactory.create(
            created_by=cls.admin_user,
            feedback_form=cls.feedback_form_1,
            order=1,
            text="How could it be improved?",
        )

        cls.binary_prompt = BinaryPromptFactory.create(
            created_by=cls.admin_user,
            feedback_form=cls.feedback_form_1,
            order=2,
            text="Was this page helpful?",
            positive_answer_label="Yes",
            negative_answer_label="No",
        )

        cls.ranged_prompt = RangedPromptFactory.create(
            created_by=cls.admin_user,
            feedback_form=cls.feedback_form_2,
            order=3,
            text="Are you satisfied with page?",
        )
        cls.option_1 = RangedPromptOptionFactory.create(
            ranged_prompt=cls.ranged_prompt,
            label="Unsatisfied",
        )
        cls.option_2 = RangedPromptOptionFactory.create(
            ranged_prompt=cls.ranged_prompt,
            label="Neutral",
        )
        cls.option_3 = RangedPromptOptionFactory.create(
            ranged_prompt=cls.ranged_prompt,
            label="Satisfied",
        )

    def test_get_feedback_form_list(self):
        response = self.client.get(
            reverse(
                "api:feedback-form_list",
                kwargs={"project": self.project_1.uuid},
            ),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertEqual(len(response.data), 2)

        feedback_form_1 = response.data[0]
        self.assertEqual(feedback_form_1["name"], self.feedback_form_1.name)
        self.assertEqual(
            feedback_form_1["is_enabled"], self.feedback_form_1.is_enabled()
        )
        self.assertEqual(
            len(feedback_form_1["prompts"]),
            self.feedback_form_1.prompts.count(),
        )

        feedback_form_2 = response.data[1]
        self.assertEqual(feedback_form_2["name"], self.feedback_form_2.name)
        self.assertEqual(
            feedback_form_2["is_enabled"], self.feedback_form_2.is_enabled()
        )

        self.assertEqual(
            len(feedback_form_2["prompts"]),
            self.feedback_form_2.prompts.count(),
        )

    def test_get_feedback_form_list_with_explore_role(self):
        APIAccessLifespanFactory(
            project=self.project_1,
            grantee=self.user,
            role=APIRole.READ_ONLY,
            created_by=self.admin_user,
        )

        response = self.client.get(
            reverse(
                "api:feedback-form_list",
                kwargs={"project": self.project_1.uuid},
            ),
            headers={"Authorization": f"Token {self.token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_feedback_form_list_with_submit_role(self):
        APIAccessLifespanFactory(
            project=self.project_1,
            grantee=self.user,
            role=APIRole.RESPONSE_SUBMITTER,
            created_by=self.admin_user,
        )

        response = self.client.get(
            reverse(
                "api:feedback-form_list",
                kwargs={"project": self.project_1.uuid},
            ),
            headers={"Authorization": f"Token {self.token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_feedback_form_list_fails_without_role(self):
        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:feedback-form_list",
                    kwargs={"project": self.project_1.uuid},
                ),
                headers={"Authorization": f"Token {self.token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_feedback_form_list_fails_without_auth(self):
        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:feedback-form_list",
                    kwargs={"project": self.project_1.uuid},
                ),
            )

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)


class TestFeedbackFormPathPatternDetail(
    APITestCase, ResetFactorySequencesMixin
):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.token = TokenFactory(user=cls.user)

        cls.admin_user = StaffUserFactory(is_superuser=True)
        cls.admin_token = TokenFactory(user=cls.admin_user)

        cls.project_1 = ProjectFactory.create(created_by=cls.admin_user)
        cls.project_2 = ProjectFactory.create(created_by=cls.admin_user)

        cls.feedback_form_1 = FeedbackFormFactory.create(
            name="Test feedback form 1",
            project=cls.project_1,
            created_by=cls.admin_user,
        )
        cls.feedback_form_2 = FeedbackFormFactory.create(
            name="Test feedback form 2",
            project=cls.project_1,
            created_by=cls.admin_user,
        )
        cls.feedback_form_3 = FeedbackFormFactory.create(
            name="Test feedback form 3",
            project=cls.project_2,
            created_by=cls.admin_user,
        )
        cls.feedback_form_4 = FeedbackFormFactory.create(
            name="Test feedback form 4",
            project=cls.project_2,
            created_by=cls.admin_user,
        )

        cls.path_pattern_1 = PathPatternFactory.create(
            feedback_form=cls.feedback_form_1,
            pattern="/foo/",
            is_wildcard=True,
        )
        cls.path_pattern_2 = PathPatternFactory.create(
            feedback_form=cls.feedback_form_1,
            pattern="/foo/zim/",
            is_wildcard=False,
        )
        cls.path_pattern_3 = PathPatternFactory.create(
            feedback_form=cls.feedback_form_2,
            pattern="/foo/bar/",
            is_wildcard=False,
        )
        cls.path_pattern_4 = PathPatternFactory.create(
            feedback_form=cls.feedback_form_2,
            pattern="/foo/zim/",
            is_wildcard=True,
        )

        cls.path_pattern_5 = PathPatternFactory.create(
            feedback_form=cls.feedback_form_3,
            pattern="/",
            is_wildcard=True,
        )
        cls.path_pattern_6 = PathPatternFactory.create(
            feedback_form=cls.feedback_form_3,
            pattern="/foo/",
            is_wildcard=True,
        )
        cls.path_pattern_7 = PathPatternFactory.create(
            feedback_form=cls.feedback_form_4,
            pattern="/foo/bar/",
            is_wildcard=True,
        )

    def test_get_feedback_form_from_exact_path(self):
        response = self.client.get(
            reverse(
                "api:feedback-form-path_detail",
                kwargs={
                    "project": self.project_1.uuid,
                    "path": "/foo/zim/",
                },
            ),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.data["id"], str(self.feedback_form_1.uuid))

    def test_get_feedback_form_from_wildcard_path(self):
        response = self.client.get(
            reverse(
                "api:feedback-form-path_detail",
                kwargs={
                    "project": self.project_1.uuid,
                    "path": "/foo/zim/gir",
                },
            ),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.data["id"], str(self.feedback_form_2.uuid))

    def test_get_feedback_form_from_exact_path_over_wildcard(self):
        response = self.client.get(
            reverse(
                "api:feedback-form-path_detail",
                kwargs={
                    "project": self.project_1.uuid,
                    "path": "/foo/zim",
                },
            ),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.data["id"], str(self.feedback_form_1.uuid))

    def test_get_feedback_form_from_nested_wildcard(self):
        response = self.client.get(
            reverse(
                "api:feedback-form-path_detail",
                kwargs={
                    "project": self.project_2.uuid,
                    "path": "/foo/bar/zim",
                },
            ),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.data["id"], str(self.feedback_form_4.uuid))

    def test_get_feedback_form_with_explore_role(self):
        APIAccessLifespanFactory(
            project=self.project_1,
            grantee=self.user,
            role=APIRole.READ_ONLY,
            created_by=self.admin_user,
        )

        response = self.client.get(
            reverse(
                "api:feedback-form-path_detail",
                kwargs={"project": self.project_1.uuid, "path": "/foo/zim/"},
            ),
            headers={"Authorization": f"Token {self.token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_feedback_form_fails_without_role(self):
        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:feedback-form-path_detail",
                    kwargs={
                        "project": self.project_1.uuid,
                        "path": "/foo/zim/",
                    },
                ),
                headers={"Authorization": f"Token {self.token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_feedback_form_fails_without_auth(self):
        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:feedback-form-path_detail",
                    kwargs={
                        "project": self.project_1.uuid,
                        "path": "/foo/zim/",
                    },
                ),
            )

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
