from django.contrib import admin

from app.projects.models import Project
from app.utils.admin import (
    HideReadOnlyOnCreationAdmin,
    SetCreatedByOnCreationAdmin,
)


class ProjectAdmin(HideReadOnlyOnCreationAdmin, SetCreatedByOnCreationAdmin):
    model = Project
    ordering = ["-created_at"]
    readonly_fields = ["uuid", "created_by"]
    fields = [
        "uuid",
        "name",
        "domain",
        "retention_period_days",
        "owned_by",
        "created_by",
    ]
    list_display = [
        "name",
        "domain",
        "owned_by",
        "uuid",
    ]
    list_filter = ["retention_period_days", "owned_by"]
    search_fields = ["name", "uuid"]


admin.site.register(Project, ProjectAdmin)
