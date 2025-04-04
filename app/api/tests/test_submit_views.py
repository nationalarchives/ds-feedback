import json
from http import HTTPStatus

from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APITestCase

from app.api.factories import APIAccessLifespanFactory, TokenFactory
from app.api.types import APIRole
from app.feedback_forms.factories import FeedbackFormFactory
from app.projects.factories import ProjectFactory
from app.prompts.factories import (
    BinaryPromptFactory,
    RangedPromptFactory,
    RangedPromptOptionFactory,
    TextPromptFactory,
)
from app.responses.factories import (
    BinaryPromptResponseFactory,
    RangedPromptResponseFactory,
    ResponseFactory,
    TextPromptResponseFactory,
)
from app.users.factories import StaffUserFactory, UserFactory
from app.utils.testing import ResetFactorySequencesMixin, ignore_request_warnings


class TestResponseCreate(APITestCase, ResetFactorySequencesMixin):
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
            project=cls.project_2,
            created_by=cls.admin_user,
        )

        cls.disabled_prompt = TextPromptFactory.create(
            created_by=cls.admin_user,
            feedback_form=cls.feedback_form_1,
            order=1,
            text="What did you think of this page?",
            disabled_at=timezone.now(),
        )
        cls.text_prompt = TextPromptFactory.create(
            created_by=cls.admin_user,
            feedback_form=cls.feedback_form_1,
            order=2,
            text="How could it be improved?",
        )
        cls.binary_prompt = BinaryPromptFactory.create(
            created_by=cls.admin_user,
            feedback_form=cls.feedback_form_1,
            order=3,
            text="Was this page helpful?",
            positive_answer_label="Yes",
            negative_answer_label="No",
        )
        cls.ranged_prompt = RangedPromptFactory.create(
            created_by=cls.admin_user,
            feedback_form=cls.feedback_form_1,
            order=4,
            text="Are you satisfied with page?",
        )

        cls.option_unsatisfied = RangedPromptOptionFactory.create(
            ranged_prompt=cls.ranged_prompt,
            label="Unsatisfied",
        )
        cls.option_neutral = RangedPromptOptionFactory.create(
            ranged_prompt=cls.ranged_prompt,
            label="Neutral",
        )
        cls.option_satisfied = RangedPromptOptionFactory.create(
            ranged_prompt=cls.ranged_prompt,
            label="Satisfied",
        )

    def test_create_response(self):
        response = self.client.post(
            reverse("api:response_create"),
            data={
                "feedback_form": self.feedback_form_1.uuid,
                "url": "https://example.com/path/1",
                "metadata": {"user-agent": "Mozilla/5.0 Firefox/133.0"},
                "first_prompt_response": {
                    "prompt": self.text_prompt.uuid,
                    "value": "More pictures of cats please!",
                },
            },
            format="json",
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.CREATED)

        self.assertEqual(response.data["url"], "https://example.com/path/1")
        self.assertEqual(
            response.data["metadata"],
            {"user-agent": "Mozilla/5.0 Firefox/133.0"},
        )
        self.assertEqual(
            response.data["feedback_form"], self.feedback_form_1.uuid
        )
        self.assertEqual(len(response.data["prompt_responses"]), 1)
        self.assertEqual(
            response.data["prompt_responses"][0]["prompt"],
            self.text_prompt.uuid,
        )
        self.assertEqual(
            response.data["prompt_responses"][0]["value"],
            "More pictures of cats please!",
        )

    def test_create_response_fails_for_second_prompt(self):
        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:response_create"),
                data={
                    "feedback_form": self.feedback_form_1.uuid,
                    "url": "https://example.com/path/1",
                    "metadata": {"user-agent": "Mozilla/5.0 Firefox/133.0"},
                    "first_prompt_response": {
                        "prompt": self.binary_prompt.uuid,
                        "value": True,
                    },
                },
                format="json",
                headers={"Authorization": f"Token {self.admin_token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

        content = json.loads(response.content)
        self.assertEqual(
            content["prompt"],
            [
                f"Prompt must be the first enabled prompt in the feedback form {self.feedback_form_1.uuid}"
            ],
        )

    def test_create_response_fails_for_disabled_prompt(self):
        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:response_create"),
                data={
                    "feedback_form": self.feedback_form_1.uuid,
                    "url": "https://example.com/path/1",
                    "metadata": {"user-agent": "Mozilla/5.0 Firefox/133.0"},
                    "first_prompt_response": {
                        "prompt": self.disabled_prompt.uuid,
                        "value": "I did not like it",
                    },
                },
                format="json",
                headers={"Authorization": f"Token {self.admin_token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

        content = json.loads(response.content)
        self.assertEqual(
            content["prompt"],
            [
                f"Prompt must be the first enabled prompt in the feedback form {self.feedback_form_1.uuid}"
            ],
        )

    def test_create_response_fails_with_no_prompt(self):
        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:response_create"),
                data={
                    "feedback_form": self.feedback_form_1.uuid,
                    "url": "https://example.com/path/1",
                    "metadata": {"user-agent": "Mozilla/5.0 Firefox/133.0"},
                },
                format="json",
                headers={"Authorization": f"Token {self.admin_token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

        content = json.loads(response.content)
        self.assertEqual(
            content,
            {"first_prompt_response": {"prompt": "This field is required."}},
        )

    def test_create_response_fails_for_disabled_feedback_form(self):
        feedback_form = FeedbackFormFactory.create(
            name="Disabled feedback form",
            project=self.project_1,
            created_by=self.admin_user,
            disabled_at=timezone.now(),
        )

        text_prompt = TextPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=feedback_form,
            order=1,
            text="How could it be improved?",
        )

        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:response_create"),
                data={
                    "feedback_form": feedback_form.uuid,
                    "url": "https://example.com/path/1",
                    "metadata": {},
                    "first_prompt_response": {
                        "prompt": text_prompt.uuid,
                        "value": "More pictures of cats please!",
                    },
                },
                format="json",
                headers={"Authorization": f"Token {self.admin_token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Feedback form id={feedback_form.uuid} is disabled.",
        )

    def test_create_response_with_submit_role(self):
        APIAccessLifespanFactory(
            project=self.project_1,
            grantee=self.user,
            role=APIRole.RESPONSE_SUBMITTER,
            created_by=self.admin_user,
        )

        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:response_create"),
                data={
                    "feedback_form": self.feedback_form_1.uuid,
                    "url": "https://example.com/path/1",
                    "metadata": {"user-agent": "Mozilla/5.0 Firefox/133.0"},
                    "first_prompt_response": {
                        "prompt": self.text_prompt.uuid,
                        "value": "More pictures of cats please!",
                    },
                },
                format="json",
                headers={"Authorization": f"Token {self.token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.CREATED)

    def test_create_response_fails_without_submit_role(self):
        APIAccessLifespanFactory(
            project=self.project_1,
            grantee=self.user,
            role=APIRole.READ_ONLY,
            created_by=self.admin_user,
        )

        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:response_create"),
                data={
                    "feedback_form": self.feedback_form_1.uuid,
                    "url": "https://example.com/path/1",
                    "metadata": {"user-agent": "Mozilla/5.0 Firefox/133.0"},
                    "first_prompt_response": {
                        "prompt": self.text_prompt.uuid,
                        "value": "More pictures of cats please!",
                    },
                },
                format="json",
                headers={"Authorization": f"Token {self.token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_create_response_fails_without_auth(self):
        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:response_create"),
                data={
                    "feedback_form": self.feedback_form_1.uuid,
                    "url": "https://example.com/path/1",
                    "metadata": {"user-agent": "Mozilla/5.0 Firefox/133.0"},
                    "first_prompt_response": {
                        "prompt": self.text_prompt.uuid,
                        "value": "More pictures of cats please!",
                    },
                },
                format="json",
            )

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)


class TestPromptResponseCreate(APITestCase, ResetFactorySequencesMixin):
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
        cls.option_unsatisfied = RangedPromptOptionFactory.create(
            ranged_prompt=cls.ranged_prompt,
            label="Unsatisfied",
        )
        cls.option_neutral = RangedPromptOptionFactory.create(
            ranged_prompt=cls.ranged_prompt,
            label="Neutral",
        )
        cls.option_satisfied = RangedPromptOptionFactory.create(
            ranged_prompt=cls.ranged_prompt,
            label="Satisfied",
        )

        cls.response_1 = ResponseFactory.create(
            feedback_form=cls.feedback_form_1,
            url="https://example.com/path/1",
        )
        TextPromptResponseFactory.create(
            prompt=cls.text_prompt,
            response=cls.response_1,
            value="More pictures of cats please!",
        )
        BinaryPromptResponseFactory.create(
            prompt=cls.binary_prompt, response=cls.response_1, value=True
        )
        RangedPromptResponseFactory.create(
            prompt=cls.ranged_prompt,
            response=cls.response_1,
            value=cls.option_satisfied,
        )

        cls.response_2 = ResponseFactory.create(
            feedback_form=cls.feedback_form_1,
            url="https://example.com/path/2",
        )

    def test_create_text_prompt_response(self):
        response = self.client.post(
            reverse("api:prompt-response_create"),
            data={
                "prompt": self.text_prompt.uuid,
                "response": self.response_2.uuid,
                "value": "More pictures of cats please!",
            },
            format="json",
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.CREATED)

        self.assertEqual(response.data["prompt"], self.text_prompt.uuid)
        self.assertEqual(
            response.data["value"], "More pictures of cats please!"
        )

    def test_create_prompt_response_invalid_prompt(self):
        other_feedback_form = FeedbackFormFactory.create(
            name="Other feedback form",
            project=self.project_1,
            created_by=self.admin_user,
        )

        invalid_prompt = TextPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=other_feedback_form,
            order=4,
            text="What would you like to see next?",
        )

        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:prompt-response_create"),
                data={
                    "response": self.response_1.uuid,
                    "prompt": invalid_prompt.uuid,
                    "value": "More pictures of cats please!",
                },
                format="json",
                headers={"Authorization": f"Token {self.admin_token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

        content = json.loads(response.content)
        self.assertEqual(
            content["prompt"],
            [
                f"Prompt id={invalid_prompt.uuid} does not exist in feedback form id={self.feedback_form_1.uuid}."
            ],
        )

    def test_create_prompt_response_disabled_prompt(self):
        feedback_form = FeedbackFormFactory.create(
            name="Other feedback form",
            project=self.project_1,
            created_by=self.admin_user,
        )

        feedback_response = ResponseFactory.create(
            feedback_form=feedback_form,
            url="https://example.com/path/1",
        )

        disabled_prompt = TextPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=feedback_form,
            disabled_at=timezone.now(),
            order=4,
            text="What would you like to see next?",
        )

        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:prompt-response_create"),
                data={
                    "response": feedback_response.uuid,
                    "prompt": disabled_prompt.uuid,
                    "value": "More pictures of cats please!",
                },
                format="json",
                headers={"Authorization": f"Token {self.admin_token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

        content = json.loads(response.content)
        self.assertEqual(
            content["prompt"],
            [
                f"Prompt id={disabled_prompt.uuid} is not enabled in feedback form id={feedback_form.uuid}."
            ],
        )

    def test_create_duplicate_prompt_response(self):
        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:prompt-response_create"),
                data={
                    "response": self.response_1.uuid,
                    "prompt": self.text_prompt.uuid,
                    "value": "Yet more pictures of cats please!!",
                },
                format="json",
                headers={"Authorization": f"Token {self.admin_token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

        content = json.loads(response.content)
        self.assertEqual(
            content["prompt"],
            [
                f"Prompt response already exists for prompt id={self.text_prompt.uuid} and response id={self.response_1.uuid}."
            ],
        )

    def test_create_prompt_response_with_submit_role(self):
        APIAccessLifespanFactory(
            project=self.project_1,
            grantee=self.user,
            role=APIRole.RESPONSE_SUBMITTER,
            created_by=self.admin_user,
        )

        response = self.client.post(
            reverse("api:prompt-response_create"),
            data={
                "prompt": self.text_prompt.uuid,
                "response": self.response_2.uuid,
                "value": "More pictures of cats please!",
            },
            format="json",
            headers={"Authorization": f"Token {self.token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.CREATED)

    def test_create_prompt_response_fails_without_submit_role(self):
        APIAccessLifespanFactory(
            project=self.project_1,
            grantee=self.user,
            role=APIRole.READ_ONLY,
            created_by=self.admin_user,
        )

        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:prompt-response_create"),
                data={
                    "prompt": self.text_prompt.uuid,
                    "response": self.response_2.uuid,
                    "value": "More pictures of cats please!",
                },
                format="json",
                headers={"Authorization": f"Token {self.token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_create_prompt_response_fails_without_auth(self):
        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:prompt-response_create"),
                data={
                    "prompt": self.text_prompt.uuid,
                    "response": self.response_2.uuid,
                    "value": "More pictures of cats please!",
                },
                format="json",
            )

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
