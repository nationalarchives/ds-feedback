from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils import timezone

from app.utils.models import CreatedByModelMixin, DisableableModelMixin


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
    Mixin to set created_by field on creation in form or inline forms
    """

    def save_model(self, request, obj, form, change):
        if isinstance(obj, CreatedByModelMixin):
            obj.set_initial_created_by(request.user, commit=False)

        super().save_model(request, obj, form, change)

    # Update created_by on inline forms
    def save_formset(self, request, form, formset, change):
        for form in formset.forms:
            if isinstance(form.instance, CreatedByModelMixin):
                form.instance.set_initial_created_by(request.user, commit=False)

        super().save_formset(request, form, formset, change)


class SetDisabledByWhenDisabledAdmin(admin.ModelAdmin):
    """
    Mixin to set disabled_by when disabled_at is set in form or inline forms
    """

    def save_model(self, request, obj, form, change):
        if isinstance(obj, DisableableModelMixin):
            obj.update_disabled_by(request.user, commit=False)

        super().save_model(request, obj, form, change)

    # Update disabled_by on inline forms
    def save_formset(self, request, form, formset, change):
        for form in formset.forms:
            if isinstance(form.instance, DisableableModelMixin):
                form.instance.update_disabled_by(request.user, commit=False)

        super().save_formset(request, form, formset, change)


class IsDisabledCheckboxForm(forms.ModelForm):
    """
    Mixin to add an is_disabled field which sets or unsets a disabled_at Date field
    """

    is_disabled = forms.BooleanField(label="disabled", required=False)

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


class IsDisabledHiddenCheckboxForm(IsDisabledCheckboxForm):
    """
    Mixin to add a hidden is_disabled field which sets or unsets a disabled_at Date field
    This is needed to stop the field being wiped when the form is submitted
    """

    is_disabled = forms.BooleanField(
        label="disabled", required=False, widget=forms.HiddenInput()
    )


def disallow_duplicates(
    forms: list[forms.ModelForm], field_name: str, error: str
):
    """
    Adds validation errors if there are any duplicate values for a field in a list of forms
    """
    values = set()
    for form in forms:
        if field_name in form.cleaned_data:
            if getattr(form.instance, field_name) in values:
                if not form.has_error(field_name):
                    form.add_error(field_name, ValidationError(error))

            values.add(getattr(form.instance, field_name))
