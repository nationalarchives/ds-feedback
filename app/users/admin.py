from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import User


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_superuser",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "email",
        "first_name",
        "last_name",
        "is_superuser",
        "is_staff",
        "is_active",
    )
    fieldsets = (
        (None, {"fields": ("email", "password", "first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_staff",
                    "is_active",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "is_superuser",
                    "is_staff",
                    "is_active",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)


admin.site.register(User, CustomUserAdmin)
