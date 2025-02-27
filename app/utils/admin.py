from django import forms
from django.contrib import admin
from django.utils import timezone


class HideReadOnlyOnCreationAdmin(admin.ModelAdmin):
    """
    Mixin to hide readonly fields in model creation form
    """

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj=obj))
        if obj is None:
            for field in self.readonly_fields:
                fields.remove(field)
        return fields


class SetCreatedByOnCreationAdmin(admin.ModelAdmin):
    """
    Mixin to set created_by field to the current user on model creation
    """

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class SetDisabledByWhenDisabledAdmin(admin.ModelAdmin):
    """
    Mixin to set disabled_by when disabled_at is set
    """

    def save_model(self, request, obj, form, change):
        if obj.disabled_at and not obj.disabled_by:
            obj.disabled_by = request.user
        if not obj.disabled_at:
            obj.disabled_by = None

        super().save_model(request, obj, form, change)


class IsDisabledCheckboxForm(forms.ModelForm):
    """
    Mixin to add an is_disabled field which sets or unsets a disabled_at Date field
    """

    is_disabled = forms.BooleanField(
        label="disabled", required=False, initial=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.disabled_at:
            self.fields["is_disabled"].initial = True

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data["is_disabled"] and not self.instance.disabled_at:
            self.instance.disabled_at = timezone.now()
        if not self.cleaned_data["is_disabled"]:
            self.instance.disabled_at = None

        return cleaned_data
