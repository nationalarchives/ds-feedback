import json
import uuid
from http import HTTPStatus

from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APITestCase

from app.feedback_forms.factories import FeedbackFormFactory, PathPatternFactory
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
from app.users.factories import StaffUserFactory
from app.utils.testing import (
    ResetFactorySequencesMixin,
    ignore_request_warnings,
    reverse_with_query,
)


class TestFeedbackFormDetail(APITestCase, ResetFactorySequencesMixin):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)
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
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "api:feedback-form_detail",
                kwargs={
                    "project": self.project.uuid,
                    "id": self.feedback_form.uuid,
                },
            )
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


class TestFeedbackFormList(APITestCase, ResetFactorySequencesMixin):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)
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

    def test_get_feedback_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "api:feedback-form_list",
                kwargs={
                    "project": self.project_1.uuid,
                },
            )
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


class TestResponseListCreate(APITestCase, ResetFactorySequencesMixin):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)

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
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("api:response_list"))

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
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse_with_query(
                "api:response_list", {"project": self.project_1.uuid}
            )
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.data), 1)

    def test_get_responses_by_feedback_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse_with_query(
                "api:response_list",
                {"feedback_form": self.feedback_form_2.uuid},
            )
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.data), 1)

    def test_create_response(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("api:response_create"),
            {
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
        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:response_create"),
                {
                    "feedback_form": self.feedback_form_1.uuid,
                    "url": "https://example.com/path/1",
                    "metadata": {"user-agent": "Mozilla/5.0 Firefox/133.0"},
                    "first_prompt_response": {
                        "prompt": self.binary_prompt.uuid,
                        "value": True,
                    },
                },
                format="json",
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
        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:response_create"),
                {
                    "feedback_form": self.feedback_form_1.uuid,
                    "url": "https://example.com/path/1",
                    "metadata": {"user-agent": "Mozilla/5.0 Firefox/133.0"},
                    "first_prompt_response": {
                        "prompt": self.disabled_prompt.uuid,
                        "value": "I did not like it",
                    },
                },
                format="json",
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
        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:response_create"),
                {
                    "feedback_form": self.feedback_form_1.uuid,
                    "url": "https://example.com/path/1",
                    "metadata": {"user-agent": "Mozilla/5.0 Firefox/133.0"},
                },
                format="json",
            )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

        content = json.loads(response.content)
        self.assertEqual(
            content,
            {"first_prompt_response": {"prompt": "This field is required."}},
        )

    def test_create_response_fails_for_disabled_feedback_form(self):
        self.client.force_login(self.admin_user)

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
                {
                    "feedback_form": feedback_form.uuid,
                    "url": "https://example.com/path/1",
                    "metadata": {},
                    "first_prompt_response": {
                        "prompt": text_prompt.uuid,
                        "value": "More pictures of cats please!",
                    },
                },
                format="json",
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Feedback form id={feedback_form.uuid} is disabled.",
        )


class ResponseDetail(APITestCase, ResetFactorySequencesMixin):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)
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

    def test_get_responses(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "api:response_detail",
                kwargs={"id": self.response.uuid},
            ),
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
        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.get(
                reverse("api:response_detail", kwargs={"id": uuid.uuid4()}),
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


class TestPromptResponseListCreate(APITestCase, ResetFactorySequencesMixin):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)

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
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse("api:prompt-response_list"),
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

    def test_create_text_prompt_response(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("api:prompt-response_create"),
            {
                "prompt": self.text_prompt.uuid,
                "response": self.response_2.uuid,
                "value": "More pictures of cats please!",
            },
            format="json",
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

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:prompt-response_create"),
                {
                    "response": self.response_1.uuid,
                    "prompt": invalid_prompt.uuid,
                    "value": "More pictures of cats please!",
                },
                format="json",
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

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:prompt-response_create"),
                {
                    "response": feedback_response.uuid,
                    "prompt": disabled_prompt.uuid,
                    "value": "More pictures of cats please!",
                },
                format="json",
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
        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.post(
                reverse("api:prompt-response_create"),
                {
                    "response": self.response_1.uuid,
                    "prompt": self.text_prompt.uuid,
                    "value": "Yet more pictures of cats please!!",
                },
                format="json",
            )

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

        content = json.loads(response.content)
        self.assertEqual(
            content["prompt"],
            [
                f"Prompt response already exists for prompt id={self.text_prompt.uuid} and response id={self.response_1.uuid}."
            ],
        )

    def test_get_prompt_responses_by_project(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse_with_query(
                "api:prompt-response_list", {"project": self.project_1.uuid}
            )
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.data), 3)

    def test_get_prompt_responses_by_feedback_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse_with_query(
                "api:prompt-response_list",
                {"feedback_form": self.feedback_form_2.uuid},
            )
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.data), 0)

    def test_get_prompt_responses_by_response(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse_with_query(
                "api:prompt-response_list",
                {"response": self.response_1.uuid},
            )
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.data), 3)

    def test_get_prompt_responses_by_prompt(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse_with_query(
                "api:prompt-response_list",
                {"prompt": self.text_prompt.uuid},
            )
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.data), 1)


class TestPromptResponseDetail(APITestCase, ResetFactorySequencesMixin):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)
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
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "api:prompt-response_detail",
                kwargs={"id": self.prompt_response.uuid},
            ),
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

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:prompt-response_detail",
                    kwargs={"id": uuid.uuid4()},
                ),
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


class TestFeedbackFormPathPatternDetail(
    APITestCase, ResetFactorySequencesMixin
):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)

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
            disabled_at=timezone.now(),
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
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "api:feedback-form-path_detail",
                kwargs={
                    "project": self.project_1.uuid,
                    "path": "/foo/zim/",
                },
            ),
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.data["id"], str(self.feedback_form_1.uuid))

    def test_get_feedback_form_from_wildcard_path(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "api:feedback-form-path_detail",
                kwargs={
                    "project": self.project_1.uuid,
                    "path": "/foo/zim/gir",
                },
            ),
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.data["id"], str(self.feedback_form_2.uuid))

    def test_get_feedback_form_from_exact_path_over_wildcard(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "api:feedback-form-path_detail",
                kwargs={
                    "project": self.project_1.uuid,
                    "path": "/foo/zim",
                },
            ),
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.data["id"], str(self.feedback_form_1.uuid))

    def test_get_feedback_form_from_nested_wildcard(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "api:feedback-form-path_detail",
                kwargs={
                    "project": self.project_2.uuid,
                    "path": "/foo/bar/zim",
                },
            ),
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.data["id"], str(self.feedback_form_4.uuid))

    def test_get_feedback_form_ignores_disabled(self):
        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:feedback-form-path_detail",
                    kwargs={
                        "project": self.project_2.uuid,
                        "path": "/",
                    },
                ),
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
