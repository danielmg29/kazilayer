import ipaddress
import uuid
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models

from apps.accounts.models import Organization
from apps.operations.fields import RichTextField, rich_text_to_plain, sanitize_rich_text
from apps.operations.models import FileAsset


class TenantModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class ContractVersion(TenantModel):
    contract_key = models.SlugField(max_length=100)
    name = models.CharField(max_length=180)
    entity_type = models.CharField(max_length=80)
    version_number = models.PositiveIntegerField()
    status = models.CharField(
        max_length=16,
        default="draft",
        choices=[(x, x.title()) for x in ("draft", "published", "retired")],
    )
    schema_json = models.JSONField(default=dict)
    validation_json = models.JSONField(default=dict)
    workflow_json = models.JSONField(default=dict, blank=True)
    permission_json = models.JSONField(default=dict, blank=True)
    ui_metadata_json = models.JSONField(default=dict, blank=True)
    change_notes = RichTextField(blank=True)
    plain_change_notes = models.TextField(blank=True, editable=False)
    predecessor = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    published_at = models.DateTimeField(null=True, blank=True)
    retired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "contract_key", "version_number"],
                name="convergence_contract_version_uniq",
            )
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            previous = ContractVersion.objects.filter(pk=self.pk).first()
            if previous and previous.status in {"published", "retired"}:
                immutable = (
                    "contract_key",
                    "entity_type",
                    "version_number",
                    "schema_json",
                    "validation_json",
                    "workflow_json",
                    "permission_json",
                )
                if any(
                    getattr(previous, field) != getattr(self, field)
                    for field in immutable
                ):
                    raise ValidationError(
                        "Published contract content is immutable; create a successor version."
                    )
        self.change_notes = sanitize_rich_text(self.change_notes)
        self.plain_change_notes = rich_text_to_plain(self.change_notes)
        super().save(*args, **kwargs)


class ContractField(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contract_version = models.ForeignKey(
        ContractVersion, on_delete=models.CASCADE, related_name="fields"
    )
    field_key = models.SlugField(max_length=100)
    label = models.CharField(max_length=180)
    field_type = models.CharField(max_length=32)
    required = models.BooleanField(default=False)
    default_value = models.JSONField(null=True, blank=True)
    options_json = models.JSONField(default=list, blank=True)
    help_text = models.TextField(blank=True)
    presentation = models.CharField(max_length=40, default="input")
    sort_order = models.PositiveIntegerField(default=0)
    validation_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["sort_order", "field_key"]
        constraints = [
            models.UniqueConstraint(
                fields=["contract_version", "field_key"],
                name="convergence_contract_field_uniq",
            )
        ]

    def save(self, *args, **kwargs):
        if self.contract_version.status != "draft":
            raise ValidationError("Fields on published contracts are immutable.")
        super().save(*args, **kwargs)


class ViewRecipe(TenantModel):
    contract_version = models.ForeignKey(
        ContractVersion, on_delete=models.PROTECT, related_name="view_recipes"
    )
    recipe_key = models.SlugField(max_length=100)
    recipe_type = models.CharField(
        max_length=32,
        choices=[
            (x, x.replace("_", " ").title())
            for x in (
                "summary_card",
                "detail_panel",
                "table",
                "timeline",
                "compact_mobile",
            )
        ],
    )
    title_template = models.CharField(max_length=255, blank=True)
    slot_mapping_json = models.JSONField(default=dict)
    field_order_json = models.JSONField(default=list, blank=True)
    action_keys_json = models.JSONField(default=list, blank=True)
    responsive_rules_json = models.JSONField(default=dict, blank=True)
    density = models.CharField(max_length=20, default="comfortable")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "recipe_key", "recipe_type"],
                name="convergence_view_recipe_uniq",
            )
        ]


class MetricDefinition(TenantModel):
    key = models.SlugField(max_length=100)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    aggregation = models.CharField(max_length=40)
    measure_field_key = models.CharField(max_length=100, blank=True)
    filters_json = models.JSONField(default=dict, blank=True)
    dimensions_json = models.JSONField(default=list, blank=True)
    unit = models.CharField(max_length=40, blank=True)
    format_json = models.JSONField(default=dict, blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "key", "version"],
                name="convergence_metric_version_uniq",
            )
        ]


class Dashboard(TenantModel):
    name = models.CharField(max_length=180)
    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )
    visibility = models.CharField(
        max_length=20,
        default="private",
        choices=[(x, x.title()) for x in ("private", "role", "organization")],
    )


class DashboardWidget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dashboard = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name="widgets"
    )
    metric_definition = models.ForeignKey(
        MetricDefinition, null=True, blank=True, on_delete=models.PROTECT
    )
    widget_type = models.CharField(
        max_length=24,
        choices=[
            (x, x.title())
            for x in ("metric", "trend", "distribution", "table", "alert")
        ],
    )
    layout_json = models.JSONField(default=dict)
    display_options_json = models.JSONField(default=dict, blank=True)


def validate_webhook_url(value):
    URLValidator(schemes=["https"])(value)
    host = urlparse(value).hostname or ""
    if host.lower() == "localhost" or host.endswith(".local"):
        raise ValidationError("Local webhook destinations are not allowed.")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return
    if not address.is_global:
        raise ValidationError(
            "Private or reserved webhook destinations are not allowed."
        )


class WebhookEndpoint(TenantModel):
    name = models.CharField(max_length=180)
    url = models.URLField(validators=[validate_webhook_url])
    event_keys = models.JSONField(default=list)
    secret_ciphertext = models.TextField()
    secret_version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)


class WebhookDelivery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    endpoint = models.ForeignKey(
        WebhookEndpoint, on_delete=models.CASCADE, related_name="deliveries"
    )
    event_id = models.CharField(max_length=120)
    delivery_key = models.CharField(max_length=180, unique=True)
    attempt = models.PositiveIntegerField(default=1)
    request_body_hash = models.CharField(max_length=64)
    response_status = models.PositiveIntegerField(null=True, blank=True)
    response_excerpt = models.TextField(blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)


class RealtimeEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    stream_key = models.CharField(max_length=180)
    sequence = models.BigIntegerField()
    event_id = models.CharField(max_length=120, unique=True)
    event_type = models.CharField(max_length=120)
    resource_type = models.CharField(max_length=80)
    resource_id = models.UUIDField(null=True, blank=True)
    version = models.PositiveIntegerField(null=True, blank=True)
    payload_json = models.JSONField(default=dict)
    emitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "stream_key", "sequence"],
                name="convergence_realtime_sequence_uniq",
            )
        ]


class BulkOperation(TenantModel):
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    resource_type = models.CharField(max_length=80)
    action_key = models.CharField(max_length=80)
    selection_mode = models.CharField(
        max_length=20,
        choices=[
            ("explicit_ids", "Explicit IDs"),
            ("query_snapshot", "Query snapshot"),
        ],
    )
    selected_ids_json = models.JSONField(default=list, blank=True)
    query_snapshot_json = models.JSONField(default=dict, blank=True)
    action_params_json = models.JSONField(default=dict, blank=True)
    preview_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        default="draft",
        choices=[
            (x, x.title())
            for x in (
                "draft",
                "confirmed",
                "queued",
                "running",
                "completed",
                "partial",
                "failed",
            )
        ],
    )
    total_count = models.PositiveIntegerField(null=True, blank=True)
    processed_count = models.PositiveIntegerField(null=True, blank=True)
    success_count = models.PositiveIntegerField(null=True, blank=True)
    failure_count = models.PositiveIntegerField(null=True, blank=True)
    error_report_file = models.ForeignKey(
        FileAsset, null=True, blank=True, on_delete=models.SET_NULL
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        super().clean()
        ids = self.selected_ids_json or []
        if self.selection_mode == "explicit_ids" and (not ids or len(ids) > 500):
            raise ValidationError(
                {
                    "selected_ids_json": "Explicit selections must contain between 1 and 500 IDs."
                }
            )
        if self.selection_mode == "query_snapshot" and not self.query_snapshot_json:
            raise ValidationError(
                {"query_snapshot_json": "A frozen query snapshot is required."}
            )
