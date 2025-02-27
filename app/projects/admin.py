from django.contrib import admin

from app.projects.models import Project
from app.utils.admin import (
    HideReadOnlyOnCreationAdmin,
    SetCreatedByOnCreationAdmin,
)


class ProjectAdmin(HideReadOnlyOnCreationAdmin, SetCreatedByOnCreationAdmin):
    ordering = ["-created_at"]
    readonly_fields = ["uuid", "created_by"]
    fields = [
        "uuid",
        "created_by",
        "name",
        "domain",
        "retention_period_days",
        "owned_by",
    ]
    list_display = [
        "name",
        "domain",
        "owned_by",
        "created_at",
        "uuid",
    ]
    list_filter = ["retention_period_days", "owned_by"]
    search_fields = ["name", "uuid"]


admin.site.register(Project, ProjectAdmin)
