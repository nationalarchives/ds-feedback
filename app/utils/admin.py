from django.contrib import admin
from django.contrib.auth.models import User


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
