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
from django.views.generic import DetailView, UpdateView

from app.editor_ui.forms import (
    PROMPT_FORM_MAP,
    PromptForm,
    RangedPromptOptionForm,
)
from app.editor_ui.mixins import (
    BreadCrumbsMixin,
    CreatedByUserMixin,
    ProjectMembershipRequiredMixin,
)
from app.editor_ui.views.base_views import BaseCreateView, CustomUpdateView
from app.feedback_forms.models import FeedbackForm
from app.prompts.models import (
    Prompt,
    RangedPrompt,
    RangedPromptOption,
)

MAX_ACTIVE_PROMPTS = 3


class PromptCreateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    CreatedByUserMixin,
    BreadCrumbsMixin,
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
    model_display_name = "Prompt"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["editor", "owner"]
    parent_model = FeedbackForm
    parent_lookup_kwarg = "feedback_form_uuid"

    breadcrumb = None

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
            # Lock the prompts rows of the feedback form to
            # prevent race conditions when calculating order, and active count
            feedback_form = FeedbackForm.objects.get(uuid=feedback_form_uuid)
            prompts_locked = feedback_form.prompts.select_for_update().all()

            # Count active prompts (not disabled) **after** acquiring the lock
            active_count = prompts_locked.filter(
                disabled_at__isnull=True
            ).count()
            will_be_active = not data.get("is_disabled", False)
            if will_be_active and active_count >= MAX_ACTIVE_PROMPTS:
                form.add_error(
                    "is_disabled",
                    f"Cannot have more than {MAX_ACTIVE_PROMPTS} active prompts.",
                )
                return self.form_invalid(form)

            # Calculate the next order value for the new prompt
            next_order = (
                prompts_locked.aggregate(m=Max("order"))["m"] or 0
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


class PromptDetailView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    BreadCrumbsMixin,
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

    breadcrumb_field = "text"

    def get_queryset(self):
        prompt_uuid = self.kwargs.get("prompt_uuid")

        is_ranged = RangedPrompt.objects.filter(uuid=prompt_uuid).exists()
        qs = (
            Prompt.objects.filter(uuid=prompt_uuid)
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


class PromptUpdateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    BreadCrumbsMixin,
    CustomUpdateView,
):
    template_name = "editor_ui/prompts/prompt_update.html"
    slug_field = "uuid"
    slug_url_kwarg = "prompt_uuid"

    model_display_name = "Prompt"

    # ProjectOwnerMembershipMixin mixin attributes
    project_roles_required = ["owner"]

    breadcrumb = None

    def get_queryset(self):
        return Prompt.objects.select_subclasses().select_related(
            "created_by",
            "disabled_by",
            "feedback_form",
            "feedback_form__project",
        )

    def get_initial(self):
        initial = super().get_initial()
        initial["is_disabled"] = bool(self.object.disabled_at)
        return initial

    def get_form_class(self):
        form = PROMPT_FORM_MAP.get(self.object.__class__, None)
        if not form:
            raise ValueError("No form found for prompt type")
        return form

    def form_valid(self, form):
        data = form.cleaned_data
        feedback_form_uuid = self.kwargs["feedback_form_uuid"]

        with transaction.atomic():
            # Lock the prompts rows of the feedback form to
            # prevent race conditions when calculating order, and active count
            feedback_form = FeedbackForm.objects.get(uuid=feedback_form_uuid)
            prompts_locked = feedback_form.prompts.select_for_update().all()

            # Count active prompts (not disabled) **after** acquiring the lock
            active_count = prompts_locked.filter(
                disabled_at__isnull=True
            ).count()
            will_be_active = not data.get("is_disabled", False)
            if will_be_active and active_count >= MAX_ACTIVE_PROMPTS:
                form.add_error(
                    "is_disabled",
                    f"Cannot have more than {MAX_ACTIVE_PROMPTS} active prompts.",
                )
                return self.form_invalid(form)

            # If the prompt should be disabled, set the disabled timestamp
            if data.get("is_disabled"):
                self.object.disabled_at = timezone.now()
                self.object.disabled_by = self.request.user
            else:
                self.object.disabled_at = None
                self.object.disabled_by = None

            self.object.save()

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            "editor_ui:project__feedback_form__prompt_detail",
            kwargs={
                "prompt_uuid": self.object.uuid,
                "feedback_form_uuid": self.object.feedback_form.uuid,
                "project_uuid": self.object.feedback_form.project.uuid,
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "prompt_uuid": self.object.uuid,
                "feedback_form_uuid": self.object.feedback_form.uuid,
                "project_uuid": self.object.feedback_form.project.uuid,
            }
        )

        return context


class RangedPromptOptionUpdateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    BreadCrumbsMixin,
    CustomUpdateView,
):
    form_class = RangedPromptOptionForm
    queryset = RangedPromptOption.objects.all()
    template_name = "editor_ui/prompts/prompt_update.html"
    slug_field = "uuid"
    slug_url_kwarg = "option_uuid"

    model_display_name = "Prompt Option"

    # ProjectOwnerMembershipMixin mixin attributes
    project_roles_required = ["editor", "owner"]

    breadcrumb = None

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "ranged_prompt",
                "ranged_prompt__feedback_form",
                "ranged_prompt__feedback_form__project",
            )
        )

    def get_success_url(self):
        return reverse(
            "editor_ui:project__feedback_form__prompt_detail",
            kwargs={
                "prompt_uuid": self.object.ranged_prompt.uuid,
                "feedback_form_uuid": self.object.ranged_prompt.feedback_form.uuid,
                "project_uuid": self.object.ranged_prompt.feedback_form.project.uuid,
            },
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "prompt_uuid": self.object.ranged_prompt.uuid,
                "feedback_form_uuid": self.object.ranged_prompt.feedback_form.uuid,
                "project_uuid": self.object.ranged_prompt.feedback_form.project.uuid,
            }
        )

        return context


class RangedPromptOptionCreateView(
    LoginRequiredMixin,
    ProjectMembershipRequiredMixin,
    BreadCrumbsMixin,
    BaseCreateView,
):
    form_class = RangedPromptOptionForm
    model_display_name = "Range Prompt Option"

    # ProjectMembershipRequiredMixin mixin attributes
    project_roles_required = ["editor", "owner"]
    parent_model = RangedPrompt
    parent_lookup_kwarg = "prompt_uuid"

    breadcrumb = None

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
