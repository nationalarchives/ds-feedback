import json
import uuid
from http import HTTPStatus

from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APITestCase

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
from app.users.factories import StaffUserFactory
from app.utils.testing import (
    ResetFactorySequencesMixin,
    ignore_request_warnings,
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

    def test_get_feedback_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "api:feedback-form_detail",
                kwargs={
                    "project_id": self.project.uuid,
                    "feedback_form_id": self.feedback_form.uuid,
                },
            ),
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertEqual(response.data["name"], "Test feedback form")
        self.assertEqual(response.data["is_enabled"], True)
        self.assertEqual(response.data["prompts"], [])

    def test_get_feedback_form_with_prompts(self):
        text_prompt = TextPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=self.feedback_form,
            order=1,
            text="How could it be improved?",
        )
        binary_prompt = BinaryPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=self.feedback_form,
            order=2,
            text="Was this page helpful?",
            positive_answer_label="Yes",
            negative_answer_label="No",
        )
        ranged_prompt = RangedPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=self.feedback_form,
            order=3,
            text="Are you satisfied with page?",
        )
        option_1 = RangedPromptOptionFactory.create(
            ranged_prompt=ranged_prompt,
            label="Unsatisfied",
        )
        option_2 = RangedPromptOptionFactory.create(
            ranged_prompt=ranged_prompt,
            label="Neutral",
        )
        option_3 = RangedPromptOptionFactory.create(
            ranged_prompt=ranged_prompt,
            label="Satisfied",
        )

        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "api:feedback-form_detail",
                kwargs={
                    "project_id": self.project.uuid,
                    "feedback_form_id": self.feedback_form.uuid,
                },
            )
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertEqual(response.data["name"], "Test feedback form")
        self.assertEqual(response.data["is_enabled"], True)
        self.assertEqual(len(response.data["prompts"]), 3)

        prompt_1 = response.data["prompts"][0]
        self.assertEqual(prompt_1["prompt_type"], text_prompt.field_label)
        self.assertEqual(prompt_1["text"], text_prompt.text)
        self.assertEqual(prompt_1["is_enabled"], text_prompt.is_enabled())
        self.assertEqual(prompt_1["max_length"], text_prompt.max_length)

        prompt_2 = response.data["prompts"][1]
        self.assertEqual(prompt_2["prompt_type"], binary_prompt.field_label)
        self.assertEqual(prompt_2["text"], binary_prompt.text)
        self.assertEqual(prompt_2["is_enabled"], binary_prompt.is_enabled())
        self.assertEqual(
            prompt_2["positive_answer_label"],
            binary_prompt.positive_answer_label,
        )
        self.assertEqual(
            prompt_2["negative_answer_label"],
            binary_prompt.negative_answer_label,
        )

        prompt_3 = response.data["prompts"][2]
        self.assertEqual(prompt_3["prompt_type"], ranged_prompt.field_label)
        self.assertEqual(prompt_3["text"], ranged_prompt.text)
        self.assertEqual(prompt_3["is_enabled"], ranged_prompt.is_enabled())
        self.assertEqual(len(prompt_3["options"]), 3)
        self.assertEqual(prompt_3["options"][0]["label"], option_1.label)
        self.assertEqual(prompt_3["options"][1]["label"], option_2.label)
        self.assertEqual(prompt_3["options"][2]["label"], option_3.label)

    def test_get_mismatched_project(self):
        other_project = ProjectFactory.create(created_by=self.admin_user)

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:feedback-form_detail",
                    kwargs={
                        "project_id": other_project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                    },
                )
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            "No FeedbackForm matches the given query.",
        )


class TestPromptList(APITestCase, ResetFactorySequencesMixin):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)
        cls.project = ProjectFactory.create(created_by=cls.admin_user)
        cls.feedback_form = FeedbackFormFactory.create(
            name="Test feedback form",
            project=cls.project,
            created_by=cls.admin_user,
        )

    def test_get_prompts(self):
        text_prompt = TextPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=self.feedback_form,
            order=1,
            text="How could it be improved?",
        )

        binary_prompt = BinaryPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=self.feedback_form,
            order=2,
            text="Was this page helpful?",
            positive_answer_label="Yes",
            negative_answer_label="No",
        )

        ranged_prompt = RangedPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=self.feedback_form,
            order=3,
            text="Are you satisfied with page?",
        )
        option_1 = RangedPromptOptionFactory.create(
            ranged_prompt=ranged_prompt,
            label="Unsatisfied",
        )
        option_2 = RangedPromptOptionFactory.create(
            ranged_prompt=ranged_prompt,
            label="Neutral",
        )
        option_3 = RangedPromptOptionFactory.create(
            ranged_prompt=ranged_prompt,
            label="Satisfied",
        )

        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "api:prompt_list",
                kwargs={
                    "project_id": self.project.uuid,
                    "feedback_form_id": self.feedback_form.uuid,
                },
            )
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertEqual(len(response.data), 3)

        prompt_1 = response.data[0]
        self.assertEqual(prompt_1["prompt_type"], text_prompt.field_label)
        self.assertEqual(prompt_1["text"], text_prompt.text)
        self.assertEqual(prompt_1["is_enabled"], text_prompt.is_enabled())
        self.assertEqual(prompt_1["max_length"], text_prompt.max_length)

        prompt_2 = response.data[1]
        self.assertEqual(prompt_2["prompt_type"], binary_prompt.field_label)
        self.assertEqual(prompt_2["text"], binary_prompt.text)
        self.assertEqual(prompt_2["is_enabled"], binary_prompt.is_enabled())
        self.assertEqual(
            prompt_2["positive_answer_label"],
            binary_prompt.positive_answer_label,
        )
        self.assertEqual(
            prompt_2["negative_answer_label"],
            binary_prompt.negative_answer_label,
        )

        prompt_3 = response.data[2]
        self.assertEqual(prompt_3["prompt_type"], ranged_prompt.field_label)
        self.assertEqual(prompt_3["text"], ranged_prompt.text)
        self.assertEqual(prompt_3["is_enabled"], ranged_prompt.is_enabled())
        self.assertEqual(len(prompt_3["options"]), 3)
        self.assertEqual(prompt_3["options"][0]["label"], option_1.label)
        self.assertEqual(prompt_3["options"][1]["label"], option_2.label)
        self.assertEqual(prompt_3["options"][2]["label"], option_3.label)


class TestResponseListCreate(APITestCase, ResetFactorySequencesMixin):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)
        cls.project = ProjectFactory.create(created_by=cls.admin_user)
        cls.feedback_form = FeedbackFormFactory.create(
            name="Test feedback form",
            project=cls.project,
            created_by=cls.admin_user,
        )

        cls.disabled_prompt = TextPromptFactory.create(
            created_by=cls.admin_user,
            feedback_form=cls.feedback_form,
            order=1,
            text="What did you think of this page?",
            disabled_at=timezone.now(),
        )
        cls.text_prompt = TextPromptFactory.create(
            created_by=cls.admin_user,
            feedback_form=cls.feedback_form,
            order=2,
            text="How could it be improved?",
        )
        cls.binary_prompt = BinaryPromptFactory.create(
            created_by=cls.admin_user,
            feedback_form=cls.feedback_form,
            order=3,
            text="Was this page helpful?",
            positive_answer_label="Yes",
            negative_answer_label="No",
        )
        cls.ranged_prompt = RangedPromptFactory.create(
            created_by=cls.admin_user,
            feedback_form=cls.feedback_form,
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

    def test_get_no_responses(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "api:response_list",
                kwargs={
                    "project_id": self.project.uuid,
                    "feedback_form_id": self.feedback_form.uuid,
                },
            )
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.data, [])

    def test_get_mismatched_project(self):
        other_project = ProjectFactory.create(created_by=self.admin_user)

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:response_list",
                    kwargs={
                        "project_id": other_project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                    },
                )
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Feedback form id={self.feedback_form.uuid} does not exist in project id={other_project.uuid}.",
        )

    def test_get_missing_feedback_form(self):
        self.client.force_login(self.admin_user)

        feedback_form_id = uuid.uuid4()

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:response_list",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": feedback_form_id,
                    },
                )
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Feedback form id={feedback_form_id} does not exist in project id={self.project.uuid}.",
        )

    def test_get_responses(self):
        response_1 = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/1",
        )
        TextPromptResponseFactory.create(
            prompt=self.text_prompt,
            response=response_1,
            value="More pictures of cats please!",
        )
        BinaryPromptResponseFactory.create(
            prompt=self.binary_prompt, response=response_1, value=True
        )
        RangedPromptResponseFactory.create(
            prompt=self.ranged_prompt,
            response=response_1,
            value=self.option_satisfied,
        )

        response_2 = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/2",
        )
        TextPromptResponseFactory.create(
            prompt=self.text_prompt,
            response=response_2,
            value="Less pictures of cats please!",
        )
        BinaryPromptResponseFactory.create(
            prompt=self.binary_prompt, response=response_2, value=False
        )
        RangedPromptResponseFactory.create(
            prompt=self.ranged_prompt,
            response=response_2,
            value=self.option_unsatisfied,
        )

        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "api:response_list",
                kwargs={
                    "project_id": self.project.uuid,
                    "feedback_form_id": self.feedback_form.uuid,
                },
            )
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

    def test_create_response(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "api:response_list",
                kwargs={
                    "project_id": self.project.uuid,
                    "feedback_form_id": self.feedback_form.uuid,
                },
            ),
            {
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
            response.data["feedback_form"], self.feedback_form.uuid
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

    def test_create_response_fails_with_second_prompt(self):
        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.post(
                reverse(
                    "api:response_list",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                    },
                ),
                {
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
                f"Prompt must be the first enabled prompt in the feedback form {self.feedback_form.uuid}"
            ],
        )

    def test_create_response_fails_with_disabled_prompt(self):
        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.post(
                reverse(
                    "api:response_list",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                    },
                ),
                {
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
                f"Prompt must be the first enabled prompt in the feedback form {self.feedback_form.uuid}"
            ],
        )

    def test_create_response_fails_with_no_prompt(self):
        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.post(
                reverse(
                    "api:response_list",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                    },
                ),
                {
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

    def test_create_response_fails_mismatched_project(self):
        other_project = ProjectFactory.create(created_by=self.admin_user)

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.post(
                reverse(
                    "api:response_list",
                    kwargs={
                        "project_id": other_project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                    },
                ),
                {},
                format="json",
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Feedback form id={self.feedback_form.uuid} does not exist or is disabled in project id={other_project.uuid}.",
        )

    def test_create_response_fails_missing_feedback_form(self):
        self.client.force_login(self.admin_user)

        feedback_form_uuid = uuid.uuid4()

        with ignore_request_warnings():
            response = self.client.post(
                reverse(
                    "api:response_list",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": feedback_form_uuid,
                    },
                ),
                {},
                format="json",
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Feedback form id={feedback_form_uuid} does not exist or is disabled in project id={self.project.uuid}.",
        )

    def test_create_response_fails_disabled_feedback_form(self):
        self.client.force_login(self.admin_user)

        feedback_form = FeedbackFormFactory.create(
            name="Disabled feedback form",
            project=self.project,
            created_by=self.admin_user,
            disabled_at=timezone.now(),
        )

        with ignore_request_warnings():
            response = self.client.post(
                reverse(
                    "api:response_list",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": feedback_form.uuid,
                    },
                ),
                {},
                format="json",
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Feedback form id={feedback_form.uuid} does not exist or is disabled in project id={self.project.uuid}.",
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

    def test_get_responses(self):
        text_prompt = TextPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=self.feedback_form,
            order=1,
            text="How could it be improved?",
        )

        binary_prompt = BinaryPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=self.feedback_form,
            order=2,
            text="Was this page helpful?",
            positive_answer_label="Yes",
            negative_answer_label="No",
        )

        ranged_prompt = RangedPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=self.feedback_form,
            order=3,
            text="Are you satisfied with page?",
        )
        RangedPromptOptionFactory.create(
            ranged_prompt=ranged_prompt,
            label="Unsatisfied",
        )
        RangedPromptOptionFactory.create(
            ranged_prompt=ranged_prompt,
            label="Neutral",
        )
        option_satisfied = RangedPromptOptionFactory.create(
            ranged_prompt=ranged_prompt,
            label="Satisfied",
        )

        feedback_response = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/1",
        )
        TextPromptResponseFactory.create(
            prompt=text_prompt,
            response=feedback_response,
            value="More pictures of cats please!",
        )
        BinaryPromptResponseFactory.create(
            prompt=binary_prompt, response=feedback_response, value=True
        )
        RangedPromptResponseFactory.create(
            prompt=ranged_prompt,
            response=feedback_response,
            value=option_satisfied,
        )

        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "api:response_detail",
                kwargs={
                    "project_id": self.project.uuid,
                    "feedback_form_id": self.feedback_form.uuid,
                    "response_id": feedback_response.uuid,
                },
            ),
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertEqual(response.data["url"], "https://example.com/path/1")

        response_prompts = response.data["prompt_responses"]
        self.assertEqual(len(response_prompts), 3)
        self.assertEqual(response_prompts[0]["prompt"], text_prompt.uuid)
        self.assertEqual(
            response_prompts[0]["value"], "More pictures of cats please!"
        )
        self.assertEqual(response_prompts[1]["prompt"], binary_prompt.uuid)
        self.assertEqual(response_prompts[1]["value"], True)
        self.assertEqual(response_prompts[2]["prompt"], ranged_prompt.uuid)
        self.assertEqual(response_prompts[2]["value"], option_satisfied.uuid)

    def test_get_missing_response(self):
        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:response_detail",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                        "response_id": uuid.uuid4(),
                    },
                ),
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_get_mismatched_project(self):
        feedback_response = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/1",
        )

        other_project = ProjectFactory.create(created_by=self.admin_user)

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:response_detail",
                    kwargs={
                        "project_id": other_project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                        "response_id": feedback_response.uuid,
                    },
                ),
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Feedback form id={self.feedback_form.uuid} does not exist in project id={other_project.uuid}.",
        )

    def test_get_missing_feedback_form(self):
        feedback_response = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/1",
        )

        self.client.force_login(self.admin_user)

        feedback_form_uuid = uuid.uuid4()

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:response_detail",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": feedback_form_uuid,
                        "response_id": feedback_response.uuid,
                    },
                ),
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Feedback form id={feedback_form_uuid} does not exist in project id={self.project.uuid}.",
        )


class TestPromptResponseListCreate(APITestCase, ResetFactorySequencesMixin):
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

    def test_get_prompt_responses(self):
        feedback_response = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/1",
        )
        TextPromptResponseFactory.create(
            prompt=self.text_prompt,
            response=feedback_response,
            value="More pictures of cats please!",
        )
        BinaryPromptResponseFactory.create(
            prompt=self.binary_prompt, response=feedback_response, value=True
        )
        RangedPromptResponseFactory.create(
            prompt=self.ranged_prompt,
            response=feedback_response,
            value=self.option_satisfied,
        )

        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse(
                "api:prompt-response_list",
                kwargs={
                    "project_id": self.project.uuid,
                    "feedback_form_id": self.feedback_form.uuid,
                    "response_id": feedback_response.uuid,
                },
            ),
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
        feedback_response = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/1",
        )

        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "api:prompt-response_list",
                kwargs={
                    "project_id": self.project.uuid,
                    "feedback_form_id": self.feedback_form.uuid,
                    "response_id": feedback_response.uuid,
                },
            ),
            {
                "prompt": self.text_prompt.uuid,
                "value": "More pictures of cats please!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, HTTPStatus.CREATED)

        self.assertEqual(response.data["prompt"], self.text_prompt.uuid)
        self.assertEqual(
            response.data["value"], "More pictures of cats please!"
        )

    def test_create_invalid_prompt_response(self):
        feedback_response = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/1",
        )

        other_project = ProjectFactory.create(created_by=self.admin_user)
        other_feedback_form = FeedbackFormFactory.create(
            name="Other feedback form",
            project=other_project,
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
                reverse(
                    "api:prompt-response_list",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                        "response_id": feedback_response.uuid,
                    },
                ),
                {
                    "response": feedback_response.uuid,
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
                f"Prompt id={invalid_prompt.uuid} does not exist in feedback form id={self.feedback_form.uuid}."
            ],
        )

    def test_create_duplicate_prompt_response(self):
        feedback_response = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/1",
        )

        TextPromptResponseFactory.create(
            prompt=self.text_prompt,
            response=feedback_response,
            value="More pictures of cats please!",
        )

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.post(
                reverse(
                    "api:prompt-response_list",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                        "response_id": feedback_response.uuid,
                    },
                ),
                {
                    "response": feedback_response.uuid,
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
                f"Prompt response already exists for prompt id={self.text_prompt.uuid} and response id={feedback_response.uuid}."
            ],
        )

    def test_get_mismatched_project(self):
        feedback_response = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/1",
        )

        other_project = ProjectFactory.create(created_by=self.admin_user)

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:prompt-response_list",
                    kwargs={
                        "project_id": other_project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                        "response_id": feedback_response.uuid,
                    },
                ),
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Feedback form id={self.feedback_form.uuid} does not exist in project id={other_project.uuid}.",
        )

    def test_get_mismatched_feedback_form(self):
        feedback_response = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/1",
        )

        other_feedback_form = FeedbackFormFactory.create(
            name="Other feedback form",
            project=self.project,
            created_by=self.admin_user,
        )

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:prompt-response_list",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": other_feedback_form.uuid,
                        "response_id": feedback_response.uuid,
                    },
                ),
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Response id={feedback_response.uuid} does not exist in feedback form id={other_feedback_form.uuid}.",
        )

    def test_get_missing_response(self):
        response_uuid = uuid.uuid4()

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:prompt-response_list",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                        "response_id": response_uuid,
                    },
                ),
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Response id={response_uuid} does not exist in feedback form id={self.feedback_form.uuid}.",
        )

    def test_create_prompt_response_mismatched_project(self):
        feedback_response = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/1",
        )

        other_project = ProjectFactory.create(created_by=self.admin_user)

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.post(
                reverse(
                    "api:prompt-response_list",
                    kwargs={
                        "project_id": other_project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                        "response_id": feedback_response.uuid,
                    },
                ),
                {},
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Feedback form id={self.feedback_form.uuid} does not exist or is disabled in project id={other_project.uuid}.",
        )

    def test_create_prompt_response_mismatched_feedback_form(self):
        feedback_response = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/1",
        )

        other_feedback_form = FeedbackFormFactory.create(
            name="Other feedback form",
            project=self.project,
            created_by=self.admin_user,
        )

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.post(
                reverse(
                    "api:prompt-response_list",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": other_feedback_form.uuid,
                        "response_id": feedback_response.uuid,
                    },
                ),
                {},
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Response id={feedback_response.uuid} does not exist in feedback form id={other_feedback_form.uuid}.",
        )

    def test_create_prompt_response_missing_response(self):
        response_uuid = uuid.uuid4()

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.post(
                reverse(
                    "api:prompt-response_list",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                        "response_id": response_uuid,
                    },
                ),
                {},
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Response id={response_uuid} does not exist in feedback form id={self.feedback_form.uuid}.",
        )


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
                kwargs={
                    "project_id": self.project.uuid,
                    "feedback_form_id": self.feedback_form.uuid,
                    "response_id": self.feedback_response.uuid,
                    "prompt_response_id": self.prompt_response.uuid,
                },
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
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                        "response_id": response.uuid,
                        "prompt_response_id": uuid.uuid4(),
                    },
                ),
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_get_mismatched_project(self):
        feedback_response = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/1",
        )

        other_project = ProjectFactory.create(created_by=self.admin_user)

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:prompt-response_detail",
                    kwargs={
                        "project_id": other_project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                        "response_id": feedback_response.uuid,
                        "prompt_response_id": self.prompt_response.uuid,
                    },
                ),
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Feedback form id={self.feedback_form.uuid} does not exist in project id={other_project.uuid}.",
        )

    def test_get_mismatched_feedback_form(self):
        feedback_response = ResponseFactory.create(
            feedback_form=self.feedback_form,
            url="https://example.com/path/1",
        )

        other_feedback_form = FeedbackFormFactory.create(
            name="Other feedback form",
            project=self.project,
            created_by=self.admin_user,
        )

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:prompt-response_detail",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": other_feedback_form.uuid,
                        "response_id": feedback_response.uuid,
                        "prompt_response_id": self.prompt_response.uuid,
                    },
                ),
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Response id={feedback_response.uuid} does not exist in feedback form id={other_feedback_form.uuid}.",
        )

    def test_get_missing_response(self):
        response_uuid = uuid.uuid4()

        self.client.force_login(self.admin_user)

        with ignore_request_warnings():
            response = self.client.get(
                reverse(
                    "api:prompt-response_detail",
                    kwargs={
                        "project_id": self.project.uuid,
                        "feedback_form_id": self.feedback_form.uuid,
                        "response_id": response_uuid,
                        "prompt_response_id": self.prompt_response.uuid,
                    },
                ),
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        content = json.loads(response.content)
        self.assertEqual(
            content["detail"],
            f"Response id={response_uuid} does not exist in feedback form id={self.feedback_form.uuid}.",
        )
