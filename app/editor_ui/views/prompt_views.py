from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import (
    BooleanField,
    ExpressionWrapper,
    Max,
    Prefetch,
    Q,
)
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView

from app.editor_ui.forms import (
    PromptForm,
    RangedPromptOptionsForm,
)
from app.editor_ui.mixins import (
    CreatedByUserMixin,
    ProjectMembershipRequiredMixin,
)
from app.editor_ui.views.base_views import BaseCreateView
from app.feedback_forms.models import FeedbackForm
from app.prompts.models import (
    Prompt,
    RangedPrompt,
    RangedPromptOption,
)


class PromptCreateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    CreatedByUserMixin,
    BaseCreateView,
):
    """
    View for creating a new Prompt (TextPrompt, BinaryPrompt, or RangedPrompt) within a
    feedback form.

    - Determines the prompt subclass to create based on form input.
    - Calculates the next order value for the prompt within the feedback form, using a
      database lock to prevent race conditions.
    - Sets ownership and creation metadata via mixins and custom form validation.
    - Redirects to the prompt detail page upon successful creation.
    """

    form_class = PromptForm
    object_name = "Prompt"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["editor", "owner"]
    parent_model = FeedbackForm
    parent_lookup_kwarg = "feedback_form_uuid"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["editor", "owner"]
    parent_model = FeedbackForm
    parent_lookup_kwarg = "feedback_form_uuid"

    MAX_ACTIVE_PROMPTS = 3

    def get_feedback_form(self):
        """Helper method to get the feedback form"""
        return FeedbackForm.objects.get(
            uuid=self.kwargs.get("feedback_form_uuid")
        )

    def form_valid(self, form):
        data = form.cleaned_data
        feedback_form_uuid = self.kwargs["feedback_form_uuid"]
        model_cls = Prompt.PROMPT_MAP[data["prompt_type"]]

        with transaction.atomic():
            # Lock the feedback form row to prevent race conditions when calculating
            # order
            form_locked = FeedbackForm.objects.select_for_update().get(
                uuid=feedback_form_uuid
            )

            # Count active prompts (not disabled) **after** acquiring the lock
            active_count = form_locked.prompts.filter(
                disabled_at__isnull=True
            ).count()
            will_be_active = not data.get("is_disabled", False)
            if will_be_active and active_count >= self.MAX_ACTIVE_PROMPTS:
                form.add_error(
                    None,
                    f"Cannot have more than {self.MAX_ACTIVE_PROMPTS} active prompts.",
                )
                return self.form_invalid(form)

            # Calculate the next order value for the new prompt
            next_order = (
                form_locked.prompts.aggregate(m=Max("order"))["m"] or 0
            ) + 1

            # Create the appropriate Prompt subclass instance with required fields
            self.object = model_cls(
                text=data["text"],
                order=next_order,
                feedback_form=self.get_feedback_form(),
                created_by=self.request.user,
            )

            # If the prompt should be disabled, set the disabled timestamp
            if data.get("is_disabled"):
                self.object.disabled_at = timezone.now()
                self.object.disabled_by = self.request.user

            self.object.save()

        return redirect(self.get_success_url())

    def get_success_url(self):
        prompt_uuid = self.object.uuid
        feedback_form_uuid = self.kwargs.get("feedback_form_uuid")
        project_uuid = self.kwargs.get("project_uuid")

        return reverse(
            "editor_ui:project__feedback_form__prompt_detail",
            kwargs={
                "project_uuid": project_uuid,
                "feedback_form_uuid": feedback_form_uuid,
                "prompt_uuid": prompt_uuid,
            },
        )

    def get_context_data(self, **kwargs):
        """
        Adds the object name to the template context for generic form rendering.

        The object name is used by the generic create template to display
        appropriate headings and labels.
        """
        context = super().get_context_data(**kwargs)
        context["object_name"] = "Prompt"
        return context


class PromptDetailView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    DetailView,
):
    """
    Displays the details of a single Prompt, including its options if it is a RangedPrompt.

    - Fetches the prompt by UUID and, if it is a RangedPrompt, prefetches its options.
    - Passes project UUID, feedback form UUID, and prompt options to the template
      context.
    """

    model = Prompt
    template_name = "editor_ui/prompts/prompt_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "prompt_uuid"
    context_object_name = "prompt"
    project_roles_required = ["editor", "owner"]

    def get_queryset(self):
        prompt_uuid = self.kwargs.get("prompt_uuid")

        is_ranged = RangedPrompt.objects.filter(uuid=prompt_uuid).exists()
        qs = (
            Prompt.objects.filter(uuid=prompt_uuid)
            .annotate(
                is_enabled=ExpressionWrapper(
                    Q(disabled_at__isnull=True), output_field=BooleanField()
                )
            )
            .select_related("created_by")
            .select_related("disabled_by")
            .select_subclasses()
        )

        if is_ranged:
            qs = qs.prefetch_related(
                Prefetch(
                    "options",
                    queryset=RangedPromptOption.objects.order_by("-value"),
                    to_attr="ordered_options",
                )
            )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        prompt_options = []

        if self.object.__class__.__name__ == "RangedPrompt":
            prompt_options = getattr(self.object, "ordered_options", [])

        context.update(
            {
                "project_uuid": self.kwargs.get("project_uuid"),
                "feedback_form_uuid": self.kwargs.get("feedback_form_uuid"),
                "prompt_options": prompt_options,
            }
        )
        return context


class RangedPromptOptionsCreateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    BaseCreateView,
):
    form_class = RangedPromptOptionsForm
    object_name = "Range Prompt Option"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["editor", "owner"]
    parent_model = FeedbackForm
    parent_lookup_kwarg = "feedback_form_uuid"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["editor", "owner"]
    parent_model = RangedPrompt
    parent_lookup_kwarg = "prompt_uuid"

    def get_success_url(self):
        prompt_uuid = self.kwargs.get("prompt_uuid")
        feedback_form_uuid = self.kwargs.get("feedback_form_uuid")
        project_uuid = self.kwargs.get("project_uuid")

        return reverse(
            "editor_ui:project__feedback_form__prompt_detail",
            kwargs={
                "project_uuid": project_uuid,
                "feedback_form_uuid": feedback_form_uuid,
                "prompt_uuid": prompt_uuid,
            },
        )

    def form_valid(self, form):
        """
        Associates the ranged prompt option with its parent prompt using the UUID.
        """
        instance = form.save(commit=False)
        instance.ranged_prompt = Prompt.objects.select_subclasses().get(
            uuid=self.kwargs.get("prompt_uuid")
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """
        Adds the object name to the template context for generic form rendering.

        The object name is used by the generic create template to display
        appropriate headings and labels.
        """
        context = super().get_context_data(**kwargs)
        context["object_name"] = "Ranged Prompt Options"
        return context
