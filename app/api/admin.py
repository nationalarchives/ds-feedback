from django.contrib import admin
from .models import ProjectAPIAccess
from app.utils.admin import SetCreatedByOnCreationAdmin


class ProjectAPIAccessAdmin(SetCreatedByOnCreationAdmin, admin.ModelAdmin):
    model = ProjectAPIAccess
    list_display = ("project", "grantee", "created_at")
    list_filter = ("project", "role")
    search_fields = ("project__name", "user__username")
    readonly_fields = ("created_at","created_by", "modified_at", "expires_at")


admin.site.register(ProjectAPIAccess, ProjectAPIAccessAdmin)