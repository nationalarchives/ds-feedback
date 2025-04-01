from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

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
from app.responses.models import PromptResponse
from app.users.factories import StaffUserFactory
from app.utils.testing import (
    ResetFactorySequencesMixin,
    get_change_list_results,
    get_inline_formset,
    reverse_with_query,
)


class TestAdminResponseView(ResetFactorySequencesMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)

    # As an Admin user I can view a list of responses for a feedback form in Django admin
    def test_search_responses(self):
        project = ProjectFactory.create(created_by=self.admin_user)
        feedback_form = FeedbackFormFactory.create(
            created_by=self.admin_user,
            project=project,
        )

        feedback_response = ResponseFactory.create(feedback_form=feedback_form)

        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse_with_query(
                "admin:responses_response_changelist",
                {"feedback_form__id__exact": feedback_form.id},
            )
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(get_change_list_results(response), [feedback_response])

    # As an Admin user I can view the answers within a response in Django admin
    def test_view_response(self):
        project = ProjectFactory.create(created_by=self.admin_user)
        feedback_form = FeedbackFormFactory.create(
            created_by=self.admin_user,
            project=project,
        )
        text_prompt = TextPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=feedback_form,
            text="How could it be improved?",
        )
        binary_prompt = BinaryPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=feedback_form,
            text="What is your impression of the author?",
            positive_answer_label="Positive",
            negative_answer_label="Negative",
        )
        ranged_prompt = RangedPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=feedback_form,
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
        satisfied = RangedPromptOptionFactory.create(
            ranged_prompt=ranged_prompt,
            label="Satisfied",
        )

        feedback_response = ResponseFactory.create(feedback_form=feedback_form)
        TextPromptResponseFactory.create(
            prompt=text_prompt,
            response=feedback_response,
            value="More pictures of cats please!",
        )
        BinaryPromptResponseFactory.create(
            prompt=binary_prompt, response=feedback_response, value=True
        )
        RangedPromptResponseFactory.create(
            prompt=ranged_prompt, response=feedback_response, value=satisfied
        )

        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse(
                "admin:responses_response_change",
                kwargs={"object_id": feedback_response.id},
            ),
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        formset = get_inline_formset(response.context, PromptResponse)
        responses = [form.instance for form in formset.forms]

        self.assertEqual(responses[0].prompt.text, "How could it be improved?")
        self.assertEqual(responses[0].answer(), "More pictures of cats please!")

        self.assertEqual(
            responses[1].prompt.text, "What is your impression of the author?"
        )
        self.assertEqual(responses[1].answer(), "Positive")

        self.assertEqual(
            responses[2].prompt.text, "Are you satisfied with page?"
        )
        self.assertEqual(responses[2].answer(), "Satisfied")
