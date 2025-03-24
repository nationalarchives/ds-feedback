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
from app.prompts.models import RangedPromptOption
from app.users.factories import StaffUserFactory
from app.utils.testing import (
    ResetFactorySequencesMixin,
    get_change_list_results,
    get_inline_formset,
    reverse_with_query,
)


class TestAdminTextPromptsView(ResetFactorySequencesMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)

    # As an Admin user I can search for text prompts in Django admin
    def test_search_text_prompts(self):
        project = ProjectFactory.create(created_by=self.admin_user)
        feedback_form = FeedbackFormFactory.create(
            created_by=self.admin_user,
            project=project,
        )
        TextPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=feedback_form,
            text="How could it be improved?",
        )
        text_prompt_2 = TextPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=feedback_form,
            text="What would you like to know next?",
        )
        text_prompt_3 = TextPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=feedback_form,
            text="Which stories stood out to you?",
        )

        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse_with_query(
                "admin:prompts_textprompt_changelist", {"q": "you"}
            )
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            get_change_list_results(response),
            [text_prompt_2, text_prompt_3],
        )


class TestAdminBinaryPromptsView(ResetFactorySequencesMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)

    # As an Admin user I can search for binary prompts in Django admin
    def test_search_binary_prompts(self):
        project = ProjectFactory.create(created_by=self.admin_user)
        feedback_form = FeedbackFormFactory.create(
            created_by=self.admin_user,
            project=project,
        )
        BinaryPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=feedback_form,
            text="Was this page helpful?",
            positive_answer_label="Yes",
            negative_answer_label="No",
        )
        binary_prompt_2 = BinaryPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=feedback_form,
            text="Would you recommend it?",
            positive_answer_label="Yes",
            negative_answer_label="No",
        )
        BinaryPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=feedback_form,
            text="What is your impression of the author?",
            positive_answer_label="Positive",
            negative_answer_label="Negative",
        )

        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse_with_query(
                "admin:prompts_binaryprompt_changelist", {"q": "you yes"}
            )
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            get_change_list_results(response),
            [binary_prompt_2],
        )


class TestAdminRangedPromptsView(ResetFactorySequencesMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = StaffUserFactory(is_superuser=True)

    # As an Admin user I can search for binary prompts in Django admin
    def test_search_range_prompts(self):
        project = ProjectFactory.create(created_by=self.admin_user)
        feedback_form = FeedbackFormFactory.create(
            created_by=self.admin_user,
            project=project,
        )

        ranged_prompt_1 = RangedPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=feedback_form,
            text="Are you likely to recommend this page?",
        )
        RangedPromptOptionFactory.create(
            ranged_prompt=ranged_prompt_1,
            label="Unlikely",
        )
        RangedPromptOptionFactory.create(
            ranged_prompt=ranged_prompt_1,
            label="Likely",
        )

        ranged_prompt_2 = RangedPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=feedback_form,
            text="Are you satisfied with page?",
        )
        RangedPromptOptionFactory.create(
            ranged_prompt=ranged_prompt_2,
            label="Unsatisfied",
        )
        RangedPromptOptionFactory.create(
            ranged_prompt=ranged_prompt_2,
            label="Neutral",
        )
        RangedPromptOptionFactory.create(
            ranged_prompt=ranged_prompt_2,
            label="Satisfied",
        )

        self.client.force_login(self.admin_user)
        response = self.client.get(
            reverse_with_query(
                "admin:prompts_rangedprompt_changelist", {"q": "page neutral"}
            )
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            get_change_list_results(response),
            [ranged_prompt_2],
        )

    # As an Admin user I can create options for a range prompt in Django admin
    def test_create_range_prompt_options(self):
        project = ProjectFactory.create(created_by=self.admin_user)
        feedback_form = FeedbackFormFactory.create(
            created_by=self.admin_user,
            project=project,
        )
        ranged_prompt = RangedPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=feedback_form,
            text="Are you likely to recommend this page?",
        )

        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "admin:prompts_rangedprompt_change",
                kwargs={"object_id": ranged_prompt.id},
            ),
            {
                "text": "Are you likely to recommend this page?",
                "options-TOTAL_FORMS": 2,
                "options-INITIAL_FORMS": 0,
                "options-0-label": "Unlikely",
                "options-0-value": "1",
                "options-1-label": "Likely",
                "options-1-value": "2",
            },
        )
        list_url = reverse("admin:prompts_rangedprompt_changelist")
        self.assertRedirects(response, list_url)

        prompt_options = RangedPromptOption.objects.filter(
            ranged_prompt=ranged_prompt
        ).all()
        self.assertEqual(len(prompt_options), 2)
        self.assertEqual(prompt_options[0].label, "Unlikely")
        self.assertEqual(prompt_options[0].value, 1)
        self.assertEqual(prompt_options[1].label, "Likely")
        self.assertEqual(prompt_options[1].value, 2)

    # As an Admin user I cannot create duplicate options for a range prompt in Django admin
    def test_create_range_duplicate_prompt_options(self):
        project = ProjectFactory.create(created_by=self.admin_user)
        feedback_form = FeedbackFormFactory.create(
            created_by=self.admin_user,
            project=project,
        )
        ranged_prompt = RangedPromptFactory.create(
            created_by=self.admin_user,
            feedback_form=feedback_form,
            text="Are you likely to recommend this page?",
        )

        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse(
                "admin:prompts_rangedprompt_change",
                kwargs={"object_id": ranged_prompt.id},
            ),
            {
                "text": "Are you likely to recommend this page?",
                "options-TOTAL_FORMS": 2,
                "options-INITIAL_FORMS": 0,
                "options-0-label": "Unlikely",
                "options-0-value": "1",
                "options-1-label": "Unlikely",
                "options-1-value": "1",
            },
        )

        text_prompt_formset = get_inline_formset(
            response.context, RangedPromptOption
        )
        self.assertEqual(
            text_prompt_formset[1].errors["label"],
            ["This label is used in another option"],
        )
        self.assertEqual(
            text_prompt_formset[1].errors["value"],
            ["This value is used in another option"],
        )
