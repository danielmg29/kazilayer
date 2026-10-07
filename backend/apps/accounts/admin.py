from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    AccountSession,
    AppUser,
    Membership,
    MfaFactor,
    Organization,
    PasswordResetToken,
    RolePolicy,
    SavedView,
)


@admin.register(AppUser)
class AppUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "display_name", "is_active", "is_staff")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("display_name", "avatar_image", "avatar_alt_text")}),
        (
            "Status",
            {
                "fields": (
                    "is_active",
                    "is_staff",
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
                    "display_name",
                    "password1",
                    "password2",
                    "is_staff",
                ),
            },
        ),
    )


admin.site.register(
    [
        Organization,
        RolePolicy,
        Membership,
        AccountSession,
        PasswordResetToken,
        MfaFactor,
        SavedView,
    ]
)
