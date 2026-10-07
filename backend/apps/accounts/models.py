import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q

from .managers import AppUserManager


def user_avatar_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"users/{instance.id}/avatar.{extension}"


def organization_logo_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"organizations/{instance.id}/logo.{extension}"


image_validator = FileExtensionValidator(["jpg", "jpeg", "png", "webp"])


class AppUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=160)
    avatar_image = models.ImageField(
        upload_to=user_avatar_path, validators=[image_validator], blank=True
    )
    avatar_alt_text = models.CharField(max_length=180, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]
    objects = AppUserManager()

    def save(self, *args, **kwargs):
        self.email = self.__class__.objects.normalize_email(self.email).lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class Organization(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=100, unique=True)
    status = models.CharField(max_length=16, choices=Status, default=Status.ACTIVE)
    timezone = models.CharField(max_length=64, default="Africa/Nairobi")
    locale = models.CharField(max_length=16, default="en-KE")
    settings_json = models.JSONField(default=dict, blank=True)
    enabled_modules = models.JSONField(default=list, blank=True)
    logo_image = models.ImageField(
        upload_to=organization_logo_path, validators=[image_validator], blank=True
    )
    logo_alt_text = models.CharField(max_length=180, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class RolePolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="role_policies"
    )
    name = models.CharField(max_length=120)
    key = models.SlugField(max_length=80)
    description = models.TextField(blank=True)
    resource_scope = models.JSONField(default=list)
    allowed_actions = models.JSONField(default=list)
    conditions_json = models.JSONField(default=dict, blank=True)
    priority = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "key"], name="accounts_role_org_key_uniq"
            )
        ]
        ordering = ["priority", "name"]

    def __str__(self):
        return f"{self.organization.slug}:{self.key}"


class Membership(models.Model):
    class Status(models.TextChoices):
        INVITED = "invited", "Invited"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        REMOVED = "removed", "Removed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        AppUser, on_delete=models.CASCADE, related_name="memberships"
    )
    role_policy = models.ForeignKey(
        RolePolicy, on_delete=models.PROTECT, related_name="memberships"
    )
    status = models.CharField(max_length=16, choices=Status, default=Status.INVITED)
    invited_by = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_membership_invites",
    )
    invited_at = models.DateTimeField(null=True, blank=True)
    joined_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                name="accounts_membership_org_user_uniq",
            )
        ]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["user", "status"]),
        ]


class AccountSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        AppUser, on_delete=models.CASCADE, related_name="account_sessions"
    )
    session_key = models.CharField(max_length=64, unique=True)
    token_hash = models.CharField(max_length=128)
    device_label = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)


class PasswordResetToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        AppUser, on_delete=models.CASCADE, related_name="password_reset_tokens"
    )
    token_hash = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class MfaFactor(models.Model):
    class FactorType(models.TextChoices):
        TOTP = "totp", "Authenticator app"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        AppUser, on_delete=models.CASCADE, related_name="mfa_factors"
    )
    factor_type = models.CharField(
        max_length=16, choices=FactorType, default=FactorType.TOTP
    )
    secret_encrypted = models.TextField()
    enabled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SavedView(models.Model):
    class Density(models.TextChoices):
        COMFORTABLE = "comfortable", "Comfortable"
        COMPACT = "compact", "Compact"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="saved_views"
    )
    user = models.ForeignKey(
        AppUser, on_delete=models.CASCADE, related_name="saved_views"
    )
    module_key = models.SlugField(max_length=80)
    name = models.CharField(max_length=120)
    filters_json = models.JSONField(default=list, blank=True)
    sorts_json = models.JSONField(default=list, blank=True)
    visible_columns = models.JSONField(default=list, blank=True)
    density = models.CharField(
        max_length=16, choices=Density, default=Density.COMFORTABLE
    )
    dashboard_selection = models.JSONField(default=list, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user", "module_key", "name"],
                name="accounts_saved_view_name_uniq",
            ),
            models.UniqueConstraint(
                fields=["organization", "user", "module_key"],
                condition=Q(is_default=True),
                name="accounts_saved_view_default_uniq",
            ),
        ]
        ordering = ["module_key", "name"]
