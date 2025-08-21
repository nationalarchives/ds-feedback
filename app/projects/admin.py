from django.contrib import admin

from app.projects.models import Project, ProjectMembership
from app.utils.admin import (
    HideReadOnlyOnCreationAdmin,
    SetCreatedByOnCreationAdmin,
)


class ProjectMembershipAdmin(admin.ModelAdmin):
    model = Project
    fields = [
        "project",
        "user",
        "role",
    ]
    list_display = [
        "project",
        "user",
        "role",
    ]


class ProjectAdmin(HideReadOnlyOnCreationAdmin, SetCreatedByOnCreationAdmin):
    model = Project
    ordering = ["-created_at"]
    readonly_fields = ["uuid", "created_by"]
    fields = [
        "uuid",
        "name",
        "domain",
        "retention_period_days",
        "created_by",
    ]
    list_display = [
        "name",
        "domain",
        "uuid",
    ]
    list_filter = ["retention_period_days"]
    search_fields = ["name", "uuid"]


admin.site.register(Project, ProjectAdmin)
admin.site.register(ProjectMembership, ProjectMembershipAdmin)
