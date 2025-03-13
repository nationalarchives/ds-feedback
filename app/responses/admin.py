from django import forms
from django.contrib import admin
from django.db.models import Prefetch
from django.urls import reverse
from django.utils.html import format_html

from app.prompts.models import Prompt
from app.responses.models import PromptResponse, Response
from app.utils.admin import (
    HideReadOnlyOnCreationAdmin,
    SetCreatedByOnCreationAdmin,
)


class PromptResponseForm(forms.ModelForm):
    answer = forms.CharField(required=False)

    class Meta:
        model = PromptResponse
        fields = "__all__"


class PromptResponseInline(admin.TabularInline):
    model = PromptResponse
    form = PromptResponseForm
    extra = 0
    can_delete = False
    ordering = ["prompt__order"]
    fields = ["prompt_link", "answer", "uuid"]
    list_display = ["uuid"]
    readonly_fields = ["uuid", "prompt_link"]

    def prompt_link(self, instance: Prompt):
        """
        Replaces prompt field in order to include link to the prompt
        """
        prompt: Prompt = instance.get_subclass_prompt()
        url = reverse(prompt.get_viewname(), kwargs={"object_id": prompt.id})
        return format_html('<a href="{url}">{text}</a>', url=url, text=prompt)

    prompt_link.short_description = "Prompt"

    def get_queryset(self, request):
        query_set = super().get_queryset(request)
        return query_set.prefetch_related(
            Prefetch("prompt", queryset=Prompt.objects.select_subclasses()),
        ).select_subclasses()


class ResponseAdmin(HideReadOnlyOnCreationAdmin, SetCreatedByOnCreationAdmin):
    model = Response
    inlines = [PromptResponseInline]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    ordering = ["-created_at"]
    readonly_fields = ["uuid", "feedback_form", "url", "metadata"]
    fields = [
        "uuid",
        "feedback_form",
        "url",
        "metadata",
    ]
    list_display = [
        "url",
        "prompt_response_count",
        "feedback_form",
        "created_at",
        "uuid",
    ]
    list_filter = [
        "feedback_form",
        "feedback_form__project",
    ]
    search_fields = ["url", "metadata", "uuid"]

    def prompt_response_count(self, obj):
        return obj.prompt_responses.count()

    prompt_response_count.short_description = "Prompt responses"


admin.site.register(Response, ResponseAdmin)
