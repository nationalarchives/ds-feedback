from django.contrib import admin

from app.utils.admin import SetCreatedByOnCreationAdmin

from .models import ProjectAPIAccess


class ProjectAPIAccessAdmin(SetCreatedByOnCreationAdmin, admin.ModelAdmin):
    model = ProjectAPIAccess
    list_display = ("project", "grantee", "created_at")
    list_filter = ("project", "role")
    search_fields = ("project__name", "user__username")
    readonly_fields = [
        "created_at",
        "created_by",
        "modified_at",
        "lifespan_days",
        "expires_at",
    ]

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj=obj))
        if obj is None:
            fields.remove("lifespan_days")
        return fields


admin.site.register(ProjectAPIAccess, ProjectAPIAccessAdmin)
