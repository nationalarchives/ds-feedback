import uuid
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
from app.utils.testing import (
    ResetFactorySequencesMixin,
    ignore_request_warnings,
    reverse_with_query,
)


class TestResponseList(APITestCase, ResetFactorySequencesMixin):
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

        response_2 = ResponseFactory.create(
            feedback_form=cls.feedback_form_2,
            url="https://example.com/path/2",
        )
        TextPromptResponseFactory.create(
            prompt=cls.text_prompt,
            response=response_2,
            value="Less pictures of cats please!",
        )
        BinaryPromptResponseFactory.create(
            prompt=cls.binary_prompt, response=response_2, value=False
        )
        RangedPromptResponseFactory.create(
            prompt=cls.ranged_prompt,
            response=response_2,
            value=cls.option_unsatisfied,
        )

    def test_get_responses(self):
        response = self.client.get(
            reverse("api:response_list"),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.data), 2)

        response_1_data = response.data[0]
        self.assertEqual(response_1_data["url"], "https://example.com/path/1")

        response_1_prompts = response_1_data["prompt_responses"]
        self.assertEqual(len(response_1_prompts), 3)
        self.assertEqual(response_1_prompts[0]["prompt"], self.text_prompt.uuid)
        self.assertEqual(
            response_1_prompts[0]["value"], "More pictures of cats please!"
        )
        self.assertEqual(
            response_1_prompts[1]["prompt"], self.binary_prompt.uuid
        )
        self.assertEqual(response_1_prompts[1]["value"], True)
        self.assertEqual(
            response_1_prompts[2]["prompt"], self.ranged_prompt.uuid
        )
        self.assertEqual(
            response_1_prompts[2]["value"], self.option_satisfied.uuid
        )

        response_2_data = response.data[1]
        self.assertEqual(response_2_data["url"], "https://example.com/path/2")

        response_2_prompts = response_2_data["prompt_responses"]
        self.assertEqual(len(response_2_prompts), 3)
        self.assertEqual(response_2_prompts[0]["prompt"], self.text_prompt.uuid)
        self.assertEqual(
            response_2_prompts[0]["value"], "Less pictures of cats please!"
        )
        self.assertEqual(
            response_2_prompts[1]["prompt"], self.binary_prompt.uuid
        )
        self.assertEqual(response_2_prompts[1]["value"], False)
        self.assertEqual(
            response_2_prompts[2]["prompt"], self.ranged_prompt.uuid
        )
        self.assertEqual(
            response_2_prompts[2]["value"], self.option_unsatisfied.uuid
        )

    def test_get_responses_by_project(self):
        response = self.client.get(
            reverse_with_query(
                "api:response_list", {"project": self.project_1.uuid}
            ),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.data), 1)

    def test_get_responses_by_feedback_form(self):
        response = self.client.get(
            reverse_with_query(
                "api:response_list",
                {"feedback_form": self.feedback_form_2.uuid},
            ),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.data), 1)

    def test_get_responses_with_explore_role(self):
        APIAccessLifespanFactory(
            project=self.project_1,
            grantee=self.user,
            role=APIRole.READ_ONLY,
            created_by=self.admin_user,
        )

        response = self.client.get(
            reverse("api:response_list"),
            headers={"Authorization": f"Token {self.token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_responses_fails_without_explore_role(self):
        APIAccessLifespanFactory(
            project=self.project_1,
            grantee=self.user,
            role=APIRole.RESPONSE_SUBMITTER,
            created_by=self.admin_user,
        )

        with ignore_request_warnings():
            response = self.client.get(
                reverse("api:response_list"),
                headers={"Authorization": f"Token {self.token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_responses_fails_without_auth(self):
        with ignore_request_warnings():
            response = self.client.get(reverse("api:response_list"))

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)


class TestResponseDetail(APITestCase, ResetFactorySequencesMixin):
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
        RangedPromptOptionFactory.create(
            ranged_prompt=cls.ranged_prompt,
            label="Unsatisfied",
        )
        RangedPromptOptionFactory.create(
            ranged_prompt=cls.ranged_prompt,
            label="Neutral",
        )
        cls.option_satisfied = RangedPromptOptionFactory.create(
            ranged_prompt=cls.ranged_prompt,
            label="Satisfied",
        )

        cls.response = ResponseFactory.create(
            feedback_form=cls.feedback_form,
            url="https://example.com/path/1",
        )
        TextPromptResponseFactory.create(
            prompt=cls.text_prompt,
            response=cls.response,
            value="More pictures of cats please!",
        )
        BinaryPromptResponseFactory.create(
            prompt=cls.binary_prompt, response=cls.response, value=True
        )
        RangedPromptResponseFactory.create(
            prompt=cls.ranged_prompt,
            response=cls.response,
            value=cls.option_satisfied,
        )

    def test_get_response(self):
        response = self.client.get(
            reverse(
                "api:response_detail",
                kwargs={"id": self.response.uuid},
            ),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertEqual(response.data["url"], "https://example.com/path/1")

        response_prompts = response.data["prompt_responses"]
        self.assertEqual(len(response_prompts), 3)
        self.assertEqual(response_prompts[0]["prompt"], self.text_prompt.uuid)
        self.assertEqual(
            response_prompts[0]["value"], "More pictures of cats please!"
        )
        self.assertEqual(response_prompts[1]["prompt"], self.binary_prompt.uuid)
        self.assertEqual(response_prompts[1]["value"], True)
        self.assertEqual(response_prompts[2]["prompt"], self.ranged_prompt.uuid)
        self.assertEqual(
            response_prompts[2]["value"], self.option_satisfied.uuid
        )

    def test_get_missing_response(self):
        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:response_detail",
                    kwargs={"id": uuid.uuid4()},
                ),
                headers={"Authorization": f"Token {self.admin_token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_get_response_with_explore_role(self):
        APIAccessLifespanFactory(
            project=self.project,
            grantee=self.user,
            role=APIRole.READ_ONLY,
            created_by=self.admin_user,
        )

        response = self.client.get(
            reverse("api:response_detail", kwargs={"id": self.response.uuid}),
            headers={"Authorization": f"Token {self.token.key}"},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_response_fails_without_explore_role(self):
        APIAccessLifespanFactory(
            project=self.project,
            grantee=self.user,
            role=APIRole.RESPONSE_SUBMITTER,
            created_by=self.admin_user,
        )

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:response_detail", kwargs={"id": self.response.uuid}
                ),
                headers={"Authorization": f"Token {self.token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_response_fails_without_auth(self):
        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:response_detail", kwargs={"id": self.response.uuid}
                )
            )

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)


class TestPromptResponseList(APITestCase, ResetFactorySequencesMixin):
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

    def test_get_prompt_responses(self):
        response = self.client.get(
            reverse("api:prompt-response_list"),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]["prompt"], self.text_prompt.uuid)
        self.assertEqual(
            response.data[0]["value"], "More pictures of cats please!"
        )
        self.assertEqual(response.data[1]["prompt"], self.binary_prompt.uuid)
        self.assertEqual(response.data[1]["value"], True)
        self.assertEqual(response.data[2]["prompt"], self.ranged_prompt.uuid)
        self.assertEqual(response.data[2]["value"], self.option_satisfied.uuid)

    def test_get_prompt_responses_by_project(self):
        response = self.client.get(
            reverse_with_query(
                "api:prompt-response_list", {"project": self.project_1.uuid}
            ),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.data), 3)

    def test_get_prompt_responses_by_feedback_form(self):
        response = self.client.get(
            reverse_with_query(
                "api:prompt-response_list",
                {"feedback_form": self.feedback_form_2.uuid},
            ),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.data), 0)

    def test_get_prompt_responses_by_response(self):
        response = self.client.get(
            reverse_with_query(
                "api:prompt-response_list",
                {"response": self.response_1.uuid},
            ),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.data), 3)

    def test_get_prompt_responses_by_prompt(self):
        response = self.client.get(
            reverse_with_query(
                "api:prompt-response_list",
                {"prompt": self.text_prompt.uuid},
            ),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.data), 1)

    def test_get_prompt_responses_with_explore_role(self):
        APIAccessLifespanFactory(
            project=self.project_1,
            grantee=self.user,
            role=APIRole.READ_ONLY,
            created_by=self.admin_user,
        )

        response = self.client.get(
            reverse("api:prompt-response_list"),
            headers={"Authorization": f"Token {self.token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_prompt_responses_fails_without_explore_role(self):
        APIAccessLifespanFactory(
            project=self.project_1,
            grantee=self.user,
            role=APIRole.RESPONSE_SUBMITTER,
            created_by=self.admin_user,
        )

        with ignore_request_warnings():
            response = self.client.get(
                reverse("api:prompt-response_list"),
                headers={"Authorization": f"Token {self.token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_prompt_responses_fails_without_auth(self):
        with ignore_request_warnings():
            response = self.client.get(reverse("api:prompt-response_list"))

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)


class TestPromptResponseDetail(APITestCase, ResetFactorySequencesMixin):
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
        cls.feedback_response = ResponseFactory.create(
            feedback_form=cls.feedback_form,
            url="https://example.com/path/1",
        )
        cls.prompt_response = TextPromptResponseFactory.create(
            prompt=cls.text_prompt,
            response=cls.feedback_response,
            value="More pictures of cats please!",
        )

    def test_get_prompt_response(self):
        response = self.client.get(
            reverse(
                "api:prompt-response_detail",
                kwargs={"id": self.prompt_response.uuid},
            ),
            headers={"Authorization": f"Token {self.admin_token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertEqual(response.data["prompt"], self.text_prompt.uuid)
        self.assertEqual(
            response.data["value"], "More pictures of cats please!"
        )

    def test_get_missing_prompt_response(self):
        response = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/1",
        )

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:prompt-response_detail",
                    kwargs={"id": uuid.uuid4()},
                ),
                headers={"Authorization": f"Token {self.admin_token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_get_prompt_response_with_explore_role(self):
        APIAccessLifespanFactory(
            project=self.project,
            grantee=self.user,
            role=APIRole.READ_ONLY,
            created_by=self.admin_user,
        )

        response = self.client.get(
            reverse(
                "api:prompt-response_detail",
                kwargs={"id": self.prompt_response.uuid},
            ),
            headers={"Authorization": f"Token {self.token.key}"},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_prompt_response_fails_without_explore_role(self):
        APIAccessLifespanFactory(
            project=self.project,
            grantee=self.user,
            role=APIRole.RESPONSE_SUBMITTER,
            created_by=self.admin_user,
        )

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:prompt-response_detail",
                    kwargs={"id": self.prompt_response.uuid},
                ),
                headers={"Authorization": f"Token {self.token.key}"},
            )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_get_prompt_response_fails_without_auth(self):
        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:prompt-response_detail",
                    kwargs={"id": self.prompt_response.uuid},
                )
            )

        self.assertEqual(response.status_code, HTTPStatus.UNAUTHORIZED)
