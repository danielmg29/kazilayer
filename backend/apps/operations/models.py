import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.accounts.models import Organization

from .fields import RichTextField, rich_text_to_plain, sanitize_rich_text


class TenantModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class FileAsset(TenantModel):
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    resource_type = models.CharField(max_length=80)
    resource_id = models.UUIDField()
    original_name = models.CharField(max_length=255)
    object_key = models.CharField(max_length=500, unique=True)
    file = models.FileField(upload_to="evidence/%Y/%m/", blank=True)
    mime_type = models.CharField(max_length=120)
    size_bytes = models.BigIntegerField(validators=[MinValueValidator(0)])
    sha256 = models.CharField(max_length=64)
    upload_status = models.CharField(
        max_length=20,
        default="ready",
        choices=[
            (x, x.title())
            for x in ("pending", "uploaded", "processing", "ready", "failed")
        ],
    )
    scan_status = models.CharField(
        max_length=20,
        default="pending",
        choices=[(x, x.title()) for x in ("pending", "clean", "rejected", "failed")],
    )
    preview_object_key = models.CharField(max_length=500, blank=True)
    visibility = models.CharField(
        max_length=24,
        default="internal",
        choices=[
            (x, x.replace("_", " ").title())
            for x in ("internal", "customer_visible", "restricted")
        ],
    )
    ready_at = models.DateTimeField(null=True, blank=True)


class UserFeedback(TenantModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    route = models.CharField(max_length=500)
    role_key = models.CharField(max_length=80, blank=True)
    viewport_width = models.PositiveIntegerField(null=True, blank=True)
    viewport_height = models.PositiveIntegerField(null=True, blank=True)
    category = models.CharField(
        max_length=20,
        choices=[
            (x, x.title())
            for x in ("bug", "usability", "content", "performance", "other")
        ],
    )
    message = models.TextField()
    screenshot_file = models.ForeignKey(
        FileAsset,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="feedback_screenshots",
    )
    consent_context_capture = models.BooleanField(default=False)
    triage_status = models.CharField(
        max_length=20,
        default="new",
        choices=[(x, x.title()) for x in ("new", "reviewing", "planned", "closed")],
    )


class ServiceRequest(TenantModel):
    contract_version_id = models.UUIDField(null=True, blank=True)
    customer_id = models.UUIDField(null=True, blank=True)
    customer_contact_id = models.UUIDField(null=True, blank=True)
    site_id = models.UUIDField(null=True, blank=True)
    location_text = models.CharField(max_length=255, blank=True)
    location_point = models.JSONField(null=True, blank=True)
    urgency = models.CharField(
        max_length=20,
        choices=[(x, x.title()) for x in ("low", "normal", "high", "critical")],
    )
    description = models.TextField()
    preferred_start_at = models.DateTimeField(null=True, blank=True)
    preferred_end_at = models.DateTimeField(null=True, blank=True)
    source = models.CharField(
        max_length=24,
        default="staff",
        choices=[
            (x, x.replace("_", " ").title())
            for x in ("staff", "customer_portal", "import", "integration")
        ],
    )
    status = models.CharField(
        max_length=24,
        default="submitted",
        choices=[
            (x, x.title())
            for x in (
                "draft",
                "submitted",
                "triaged",
                "approved",
                "rejected",
                "converted",
            )
        ],
    )
    idempotency_key = models.CharField(max_length=120)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "idempotency_key"],
                name="operations_request_idempotency_uniq",
            )
        ]

    def clean(self):
        super().clean()
        if (
            self.preferred_start_at
            and self.preferred_end_at
            and self.preferred_end_at <= self.preferred_start_at
        ):
            from django.core.exceptions import ValidationError

            raise ValidationError(
                {"preferred_end_at": "Preferred end must be after preferred start."}
            )


class Comment(TenantModel):
    resource_type = models.CharField(max_length=80)
    resource_id = models.UUIDField()
    author_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    body = RichTextField()
    plain_text = models.TextField(editable=False)
    visibility = models.CharField(
        max_length=24,
        default="internal",
        choices=[
            (x, x.replace("_", " ").title())
            for x in ("internal", "customer_visible", "restricted_role")
        ],
    )
    parent_comment = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )
    edited_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)

    def save(self, *args, **kwargs):
        self.body = sanitize_rich_text(self.body)
        self.plain_text = rich_text_to_plain(self.body)
        super().save(*args, **kwargs)


class Mention(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="mentions"
    )
    mentioned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["comment", "mentioned_user"],
                name="operations_mention_comment_user_uniq",
            )
        ]


class SearchDocument(TenantModel):
    resource_type = models.CharField(max_length=80)
    resource_id = models.UUIDField()
    title = models.CharField(max_length=255)
    body_text = models.TextField(blank=True)
    search_vector = models.TextField(blank=True)
    rank_boost = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "resource_type", "resource_id"],
                name="operations_search_resource_uniq",
            )
        ]


class ImportJob(TenantModel):
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    resource_type = models.CharField(max_length=80)
    source_file = models.ForeignKey(
        FileAsset, on_delete=models.PROTECT, related_name="import_sources"
    )
    contract_version_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        default="queued",
        choices=[
            (x, x.title())
            for x in ("queued", "validating", "importing", "completed", "failed")
        ],
    )
    total_rows = models.PositiveIntegerField(null=True, blank=True)
    valid_rows = models.PositiveIntegerField(null=True, blank=True)
    invalid_rows = models.PositiveIntegerField(null=True, blank=True)
    error_report_file = models.ForeignKey(
        FileAsset,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="import_error_reports",
    )
    completed_at = models.DateTimeField(null=True, blank=True)


class ExportJob(TenantModel):
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    resource_type = models.CharField(max_length=80)
    filters_json = models.JSONField(default=dict, blank=True)
    columns_json = models.JSONField(default=list)
    output_file = models.ForeignKey(
        FileAsset,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="export_outputs",
    )
    manifest_json = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20,
        default="queued",
        choices=[
            (x, x.title()) for x in ("queued", "generating", "completed", "failed")
        ],
    )


class AuditEvent(TenantModel):
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    request_id = models.CharField(max_length=120, blank=True)
    event_type = models.CharField(max_length=120)
    resource_type = models.CharField(max_length=80)
    resource_id = models.UUIDField()
    before_summary = models.JSONField(null=True, blank=True)
    after_summary = models.JSONField(null=True, blank=True)
    reason = models.TextField(blank=True)
    contract_version_id = models.UUIDField(null=True, blank=True)
    source_ip_hash = models.CharField(max_length=128, blank=True)

    def save(self, *args, **kwargs):
        if self.pk and AuditEvent.objects.filter(pk=self.pk).exists():
            raise ValueError("Audit events are append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Audit events are append-only.")


class WorkOrder(TenantModel):
    service_request = models.ForeignKey(
        ServiceRequest, null=True, blank=True, on_delete=models.SET_NULL
    )
    contract_version_id = models.UUIDField(null=True, blank=True)
    title = models.CharField(max_length=255)
    instructions = RichTextField(blank=True)
    plain_instructions = models.TextField(blank=True, editable=False)
    priority = models.CharField(
        max_length=20,
        default="normal",
        choices=[(x, x.title()) for x in ("low", "normal", "high", "critical")],
    )
    status = models.CharField(max_length=40, default="new")
    site_id = models.UUIDField(null=True, blank=True)
    customer_id = models.UUIDField(null=True, blank=True)
    scheduled_start_at = models.DateTimeField(null=True, blank=True)
    scheduled_end_at = models.DateTimeField(null=True, blank=True)
    completion_summary = RichTextField(blank=True)
    plain_completion_summary = models.TextField(blank=True, editable=False)
    version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.instructions = sanitize_rich_text(self.instructions)
        self.completion_summary = sanitize_rich_text(self.completion_summary)
        self.plain_instructions = rich_text_to_plain(self.instructions)
        self.plain_completion_summary = rich_text_to_plain(self.completion_summary)
        super().save(*args, **kwargs)


class WorkTransition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_order = models.ForeignKey(
        WorkOrder, on_delete=models.CASCADE, related_name="transitions"
    )
    from_state = models.CharField(max_length=40, blank=True)
    to_state = models.CharField(max_length=40)
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    reason = models.TextField(blank=True)
    evidence_required_met = models.BooleanField(default=False)
    occurred_at = models.DateTimeField(auto_now_add=True)


class NotificationPreference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    event_key = models.CharField(max_length=120)
    in_app = models.BooleanField(default=True)
    email = models.BooleanField(default=False)
    quiet_hours_json = models.JSONField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "event_key"],
                name="operations_notification_preference_uniq",
            )
        ]


class NotificationTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_key = models.CharField(max_length=120)
    channel = models.CharField(
        max_length=16, choices=[("in_app", "In app"), ("email", "Email")]
    )
    subject_template = models.CharField(max_length=255, blank=True)
    body = RichTextField()
    plain_text_body = models.TextField(editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event_key", "channel"],
                name="operations_notification_template_uniq",
            )
        ]

    def save(self, *args, **kwargs):
        self.body = sanitize_rich_text(self.body)
        self.plain_text_body = rich_text_to_plain(self.body)
        super().save(*args, **kwargs)


class Notification(TenantModel):
    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    event_id = models.CharField(max_length=120)
    dedupe_key = models.CharField(max_length=255, unique=True)
    channel = models.CharField(
        max_length=16, choices=[("in_app", "In app"), ("email", "Email")]
    )
    status = models.CharField(
        max_length=16,
        default="queued",
        choices=[(x, x.title()) for x in ("queued", "sent", "failed", "read")],
    )
    payload_json = models.JSONField(default=dict)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
