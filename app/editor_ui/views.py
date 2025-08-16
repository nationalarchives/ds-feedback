from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.aggregates import StringAgg
from django.db import transaction
from django.db.models import Count, F, Max, Prefetch, Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView

from app.editor_ui.forms import FeedbackFormForm, ProjectForm, PromptForm
from app.editor_ui.mixins import OwnedByUserMixin, SuperuserRequiredMixin
from app.feedback_forms.models import FeedbackForm
from app.projects.models import Project
from app.prompts.models import (
    BinaryPrompt,
    Prompt,
    RangedPrompt,
    RangedPromptOption,
    TextPrompt,
)


class ProjectCreateView(
    OwnedByUserMixin, SuperuserRequiredMixin, LoginRequiredMixin, CreateView
):
    model = Project
    form_class = ProjectForm
    template_name = "editor_ui/projects/project_create.html"

    def get_success_url(self):
        return reverse(
            "editor_ui:project_detail", kwargs={"uuid": self.object.uuid}
        )


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "editor_ui/projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        if self.request.user.is_superuser:
            qs = Project.objects.all().select_related("owned_by")
        else:
            qs = Project.objects.filter(owned_by=self.request.user)
        return qs


class ProjectDetailView(SuperuserRequiredMixin, LoginRequiredMixin, DetailView):
    model = Project
    template_name = "editor_ui/projects/project_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        return (
            Project.objects.all()
            .select_related("owned_by")
            .annotate(
                forms_count=Count(
                    "feedback_forms",
                    filter=Q(feedback_forms__disabled_at=None),
                ),
                responses_count=Count(
                    "feedback_forms__responses",
                    filter=Q(feedback_forms__disabled_at=None),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        context["forms_count"] = project.forms_count
        context["responses_count"] = project.responses_count

        return context


class FeedbackFormListView(
    SuperuserRequiredMixin, LoginRequiredMixin, ListView
):
    """
    Displays a list of feedback forms for a given project.

    - Fetches all feedback forms associated with parent project.
    - Prefetches related path patterns and project data.
    - Annotates each feedback form with its project UUID and prompt count.
    - Passes the project UUID to the context for use in links.
    """

    model = FeedbackForm
    template_name = "editor_ui/feedback_forms/feedback_form_list.html"
    context_object_name = "feedback_forms"

    def get_queryset(self):
        qs = (
            FeedbackForm.objects.all()
            .prefetch_related("path_patterns")
            .select_related("project")
            .annotate(project_uuid=F("project__uuid"))
            .annotate(
                prompts_count=Count("prompts", distinct=True),
                path_patterns_str=StringAgg(
                    "path_patterns__pattern", delimiter=", ", distinct=True
                ),
            )
        )

        return qs.filter(project__uuid=self.kwargs.get("project_uuid"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_uuid"] = self.kwargs.get("project_uuid")

        return context


class FeedbackFormCreateView(
    OwnedByUserMixin, SuperuserRequiredMixin, LoginRequiredMixin, CreateView
):
    """
    View for creating a new FeedbackForm within a project.

    - Associates the new feedback form with its parent project using the project UUID
      from the URL.
    - Redirects to the new feedback form's detail page upon successful creation.

    Notes:
        Requires superuser access and authentication
        Ownership (created_by, owned_by) is handled by OwnedByUserMixin
    """

    model = FeedbackForm
    form_class = FeedbackFormForm
    template_name = "editor_ui/feedback_forms/feedback_form_create.html"

    def form_valid(self, form):
        """
        Associates the feedback form with its parent project using the project UUID.
        """
        instance = form.save(commit=False)
        instance.project = Project.objects.get(
            uuid=self.kwargs.get("project_uuid")
        )

        return super().form_valid(form)

    def get_success_url(self):
        feedback_form_uuid = self.object.uuid
        project_uuid = self.object.project.uuid

        return reverse(
            "editor_ui:project__feedback_form_detail",
            kwargs={
                "project_uuid": project_uuid,
                "feedback_form_uuid": feedback_form_uuid,
            },
        )


class FeedbackFormDetailView(
    SuperuserRequiredMixin, LoginRequiredMixin, DetailView
):
    """
    Displays the details of a single FeedbackForm, including its prompts and path
    patterns.

    - Fetches the feedback form by UUID and prefetches related path patterns and
      prompts.
    - Passes project UUID, path patterns, and ordered prompts to the template context.
    """

    model = FeedbackForm
    template_name = "editor_ui/feedback_forms/feedback_form_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "feedback_form_uuid"
    context_object_name = "feedback_form"

    def get_queryset(self):
        return (
            FeedbackForm.objects.all()
            .prefetch_related("path_patterns")
            .prefetch_related(
                Prefetch(
                    "prompts",
                    queryset=Prompt.objects.select_subclasses().select_related(
                        "created_by"
                    ),
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "project_uuid": self.kwargs.get("project_uuid"),
                "path_patterns": self.object.path_patterns.all(),
                "prompts": self.object.prompts.select_subclasses().order_by(
                    "order"
                ),
            }
        )
        return context


class PromptCreateView(
    OwnedByUserMixin, SuperuserRequiredMixin, LoginRequiredMixin, CreateView
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

    model = Prompt
    form_class = PromptForm
    template_name = "editor_ui/create.html"

    PROMPT_TYPES = {
        "TextPrompt": TextPrompt,
        "BinaryPrompt": BinaryPrompt,
        "RangedPrompt": RangedPrompt,
    }

    def get_feedback_form(self):
        """Helper method to get the feedback form"""
        return FeedbackForm.objects.get(
            uuid=self.kwargs.get("feedback_form_uuid")
        )

    def form_valid(self, form):
        data = form.cleaned_data
        feedback_form_uuid = self.kwargs["feedback_form_uuid"]
        model_cls = self.PROMPT_TYPES[data["prompt_type"]]

        with transaction.atomic():
            # Lock the feedback form row to prevent race conditions when calculating
            # order
            form_locked = FeedbackForm.objects.select_for_update().get(
                uuid=feedback_form_uuid
            )

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


class PromptDetailView(SuperuserRequiredMixin, LoginRequiredMixin, DetailView):
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

    def get_queryset(self):
        prompt_uuid = self.kwargs.get("prompt_uuid")

        is_ranged = RangedPrompt.objects.filter(uuid=prompt_uuid).exists()
        qs = Prompt.objects.filter(uuid=prompt_uuid).select_subclasses()

        if is_ranged:
            qs = qs.prefetch_related(
                Prefetch(
                    "options",
                    queryset=RangedPromptOption.objects.order_by("value"),
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
