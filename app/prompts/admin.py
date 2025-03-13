from django.contrib import admin
from django.forms import BaseInlineFormSet

from app.prompts.models import (
    BinaryPrompt,
    RangedPrompt,
    RangedPromptOption,
    TextPrompt,
)
from app.utils.admin import (
    IsDisabledHiddenCheckboxForm,
    SetDisabledByWhenDisabledAdmin,
    disallow_duplicates,
)


class TextPromptForm(IsDisabledHiddenCheckboxForm):
    class Meta:
        model = TextPrompt
        fields = "__all__"


class BinaryPromptForm(IsDisabledHiddenCheckboxForm):
    class Meta:
        model = BinaryPrompt
        fields = "__all__"


class RangedPromptForm(IsDisabledHiddenCheckboxForm):
    class Meta:
        model = RangedPrompt
        fields = "__all__"


class TextPromptAdmin(SetDisabledByWhenDisabledAdmin):
    model = TextPrompt
    form = TextPromptForm
    extra = 1
    ordering = ["feedback_form", "order"]
    fields = [
        "uuid",
        "feedback_form",
        "order",
        "is_disabled",
        "disabled",
        "text",
        "max_length",
        "created_by",
    ]
    readonly_fields = [
        "uuid",
        "feedback_form",
        "order",
        "disabled",
        "created_by",
    ]
    list_display = ["text", "feedback_form", "order", "uuid"]
    list_filter = ["feedback_form"]
    search_fields = ["text", "uuid"]

    def disabled(self, instance):
        return "Yes" if instance.disabled_at else "No"

    disabled.short_description = "Disabled"

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        query_set = super().get_queryset(request)
        return query_set.select_related("created_by", "disabled_by")


class BinaryPromptAdmin(SetDisabledByWhenDisabledAdmin):
    model = BinaryPrompt
    form = BinaryPromptForm
    extra = 1
    ordering = ["feedback_form", "order"]
    fields = [
        "uuid",
        "feedback_form",
        "order",
        "is_disabled",
        "disabled",
        "text",
        "positive_answer_label",
        "negative_answer_label",
        "created_by",
    ]
    readonly_fields = [
        "uuid",
        "feedback_form",
        "order",
        "disabled",
        "created_by",
    ]
    list_display = [
        "text",
        "positive_answer_label",
        "negative_answer_label",
        "feedback_form",
        "order",
        "uuid",
    ]
    list_filter = ["feedback_form"]
    search_fields = [
        "text",
        "positive_answer_label",
        "negative_answer_label",
        "uuid",
    ]

    def disabled(self, instance):
        return "Yes" if instance.disabled_at else "No"

    disabled.short_description = "Disabled"

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        query_set = super().get_queryset(request)
        return query_set.select_related("created_by", "disabled_by")


class RangedPromptOptionFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        disallow_duplicates(
            self.forms, "value", "This value is used in another option"
        )
        disallow_duplicates(
            self.forms, "label", "This label is used in another option"
        )


class RangedPromptOptionAdmin(admin.TabularInline):
    model = RangedPromptOption
    formset = RangedPromptOptionFormSet
    extra = 1
    ordering = ["value"]
    fields = [
        "label",
        "value",
    ]


class RangedPromptAdmin(SetDisabledByWhenDisabledAdmin):
    model = RangedPrompt
    form = RangedPromptForm
    inlines = [RangedPromptOptionAdmin]
    extra = 1
    ordering = ["feedback_form", "order"]
    fields = [
        "uuid",
        "feedback_form",
        "order",
        "is_disabled",
        "disabled",
        "text",
        "created_by",
    ]
    readonly_fields = [
        "uuid",
        "feedback_form",
        "order",
        "disabled",
        "created_by",
    ]
    list_display = ["text", "options", "feedback_form", "order", "uuid"]
    list_filter = ["feedback_form"]
    search_fields = ["text", "uuid", "options__label"]

    def disabled(self, instance):
        return "Yes" if instance.disabled_at else "No"

    disabled.short_description = "Disabled"

    def has_add_permission(self, request, obj=None):
        return False

    def options(self, obj):
        return ", ".join(
            option.label for option in obj.options.all().order_by("value")
        )

    options.short_description = "Path patterns"

    def get_queryset(self, request):
        query_set = super().get_queryset(request)
        # Prefetch only changelist page
        id = request.resolver_match.kwargs.get("object_id")
        if not id:
            query_set = query_set.prefetch_related("options")

        return query_set.select_related("created_by", "disabled_by")


admin.site.register(TextPrompt, TextPromptAdmin)
admin.site.register(BinaryPrompt, BinaryPromptAdmin)
admin.site.register(RangedPrompt, RangedPromptAdmin)
