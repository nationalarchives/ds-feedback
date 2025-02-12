from django.contrib import admin
from app.projects.models import Project
from flask import current_app


class ProjectAdmin(admin.ModelAdmin):
    ordering = ["-created_at"]
    readonly_fields = ["created_by", "uuid"]
    fields = ["uuid", "created_by", "name", "domain", "retention_period", "owned_by"]
    list_display = ["name", "owned_by", "created_at", "retention_period", "uuid"]
    list_filter = ["retention_period", "owned_by"]
    search_fields = ["name", "uuid"]

    # Only show the created_by field on existing projects
    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj=obj))
        if obj is None:
            fields.remove("uuid")
            fields.remove("created_by")
        return fields

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


admin.site.register(Project, ProjectAdmin)
