import hashlib
import uuid

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import AppUser, Organization, RolePolicy
from apps.accounts.security import encrypt_secret
from apps.convergence.models import (
    BulkOperation,
    ContractField,
    ContractVersion,
    Dashboard,
    DashboardWidget,
    MetricDefinition,
    RealtimeEvent,
    ViewRecipe,
    WebhookDelivery,
    WebhookEndpoint,
)
from apps.operations.models import WorkOrder

MODULES = [
    "contracts",
    "dynamic-forms",
    "adaptive-views",
    "dashboards",
    "integrations",
    "realtime",
    "bulk-operations",
]
ROLE_ACTIONS = {
    "owner": [
        "contract.list",
        "contract.create",
        "contract.publish",
        "dynamic_form.use",
        "view_recipe.list",
        "view_recipe.create",
        "dashboard.list",
        "dashboard.create",
        "webhook.list",
        "webhook.create",
        "webhook.rotate",
        "realtime.subscribe",
        "bulk.list",
        "bulk.preview",
        "bulk.execute",
    ],
    "dispatcher": [
        "contract.list",
        "dynamic_form.use",
        "view_recipe.list",
        "dashboard.list",
        "dashboard.create",
        "realtime.subscribe",
        "bulk.list",
        "bulk.preview",
        "bulk.execute",
    ],
    "technician": [
        "dynamic_form.use",
        "view_recipe.list",
        "dashboard.list",
        "realtime.subscribe",
    ],
    "customer": ["dynamic_form.use", "view_recipe.list", "realtime.subscribe"],
    "auditor": [
        "contract.list",
        "view_recipe.list",
        "dashboard.list",
        "webhook.list",
        "realtime.subscribe",
        "bulk.list",
    ],
}


def stable_id(organization, label):
    return uuid.uuid5(
        uuid.NAMESPACE_URL, f"kazilayer:{organization.slug}:convergence:{label}"
    )


class Command(BaseCommand):
    help = "Seed KL-F-04, 05, 06, 15, 21, 18 and 12 demonstration data."

    def handle(self, *args, **options):
        owner = AppUser.objects.get(email="owner@demo.kazilayer.test")
        now = timezone.now()
        for organization in Organization.objects.filter(status="active"):
            organization.enabled_modules = list(
                dict.fromkeys([*organization.enabled_modules, *MODULES])
            )
            organization.save(update_fields=["enabled_modules", "updated_at"])
            for role in RolePolicy.objects.filter(organization=organization):
                role.allowed_actions = list(
                    dict.fromkeys(
                        [*role.allowed_actions, *ROLE_ACTIONS.get(role.key, [])]
                    )
                )
                role.resource_scope = list(
                    dict.fromkeys(
                        [
                            *role.resource_scope,
                            "contract",
                            "view_recipe",
                            "dashboard",
                            "webhook",
                            "realtime",
                            "bulk_operation",
                        ]
                    )
                )
                role.save(
                    update_fields=["allowed_actions", "resource_scope", "updated_at"]
                )

            contract, _ = ContractVersion.objects.get_or_create(
                organization=organization,
                contract_key="maintenance-work-order",
                version_number=1,
                defaults={
                    "name": "Maintenance work order",
                    "entity_type": "work_order",
                    "status": "draft",
                    "schema_json": {"type": "object"},
                    "validation_json": {"mode": "server_authoritative"},
                    "workflow_json": {
                        "states": [
                            "new",
                            "scheduled",
                            "in_progress",
                            "blocked",
                            "completed",
                        ]
                    },
                    "permission_json": {
                        "create": ["owner", "dispatcher"],
                        "review": ["owner", "dispatcher", "technician"],
                    },
                    "ui_metadata_json": {"layout": "operational"},
                    "change_notes": "<p>Initial contract with <strong>restricted rich-text</strong> work instructions.</p>",
                },
            )
            if contract.status == "draft":
                field_definitions = [
                    (
                        "title",
                        "Work title",
                        "text",
                        True,
                        "input",
                        {},
                        "Short operational title.",
                    ),
                    (
                        "instructions",
                        "Work instructions",
                        "rich_text",
                        False,
                        "wysiwyg",
                        {"allowed_blocks": ["paragraph", "heading", "list"]},
                        "Structured and sanitised instructions.",
                    ),
                    (
                        "priority",
                        "Priority",
                        "select",
                        True,
                        "select",
                        {"options": ["low", "normal", "high", "critical"]},
                        "Configured work priority.",
                    ),
                    (
                        "scheduled_start_at",
                        "Scheduled start",
                        "datetime",
                        False,
                        "datetime",
                        {},
                        "Planned start time.",
                    ),
                ]
                for index, (
                    key,
                    label,
                    field_type,
                    required,
                    presentation,
                    validation,
                    help_text,
                ) in enumerate(field_definitions):
                    ContractField.objects.update_or_create(
                        contract_version=contract,
                        field_key=key,
                        defaults={
                            "label": label,
                            "field_type": field_type,
                            "required": required,
                            "presentation": presentation,
                            "sort_order": index,
                            "validation_json": validation,
                            "options_json": validation.get("options", []),
                            "help_text": help_text,
                        },
                    )
                contract.status = "published"
                contract.published_by = owner
                contract.published_at = now
                contract.save(
                    update_fields=[
                        "status",
                        "published_by",
                        "published_at",
                        "change_notes",
                        "plain_change_notes",
                    ]
                )

            recipes = [
                (
                    "work-order",
                    "summary_card",
                    {"title": "title", "badge": "status", "meta": "scheduled_start_at"},
                    ["title", "priority", "status"],
                ),
                (
                    "work-order",
                    "detail_panel",
                    {"title": "title", "body": "instructions", "badge": "status"},
                    ["title", "instructions", "priority", "scheduled_start_at"],
                ),
                (
                    "work-order",
                    "compact_mobile",
                    {"title": "title", "badge": "status"},
                    ["title", "status"],
                ),
            ]
            for key, recipe_type, slots, order in recipes:
                ViewRecipe.objects.update_or_create(
                    organization=organization,
                    recipe_key=key,
                    recipe_type=recipe_type,
                    defaults={
                        "contract_version": contract,
                        "title_template": "{{title}}",
                        "slot_mapping_json": slots,
                        "field_order_json": order,
                        "action_keys_json": ["work_order.transition"],
                        "responsive_rules_json": {
                            "min_width": 0 if recipe_type == "compact_mobile" else 768
                        },
                        "density": "compact"
                        if recipe_type == "compact_mobile"
                        else "comfortable",
                        "is_active": True,
                    },
                )

            open_requests, _ = MetricDefinition.objects.update_or_create(
                organization=organization,
                key="open_requests",
                version=1,
                defaults={
                    "name": "Open requests",
                    "description": "Requests not yet rejected or converted.",
                    "aggregation": "count",
                    "filters_json": {"status_not_in": ["rejected", "converted"]},
                    "dimensions_json": ["urgency", "status"],
                    "unit": "count",
                    "format_json": {"decimals": 0},
                },
            )
            active_work, _ = MetricDefinition.objects.update_or_create(
                organization=organization,
                key="active_work",
                version=1,
                defaults={
                    "name": "Active work",
                    "description": "Scheduled, in-progress, or blocked work orders.",
                    "aggregation": "count",
                    "filters_json": {
                        "status_in": ["scheduled", "in_progress", "blocked"]
                    },
                    "dimensions_json": ["priority", "status"],
                    "unit": "count",
                    "format_json": {"decimals": 0},
                },
            )
            dashboard, _ = Dashboard.objects.update_or_create(
                id=stable_id(organization, "dashboard"),
                defaults={
                    "organization": organization,
                    "name": "Operations control",
                    "visibility": "organization",
                },
            )
            DashboardWidget.objects.update_or_create(
                id=stable_id(organization, "widget-open-requests"),
                defaults={
                    "dashboard": dashboard,
                    "metric_definition": open_requests,
                    "widget_type": "metric",
                    "layout_json": {"x": 0, "y": 0, "w": 3, "h": 2},
                    "display_options_json": {"tone": "primary"},
                },
            )
            DashboardWidget.objects.update_or_create(
                id=stable_id(organization, "widget-active-work"),
                defaults={
                    "dashboard": dashboard,
                    "metric_definition": active_work,
                    "widget_type": "trend",
                    "layout_json": {"x": 3, "y": 0, "w": 6, "h": 3},
                    "display_options_json": {"chart": "bar"},
                },
            )

            endpoint, _ = WebhookEndpoint.objects.update_or_create(
                id=stable_id(organization, "webhook"),
                defaults={
                    "organization": organization,
                    "name": "Service operations sandbox",
                    "url": "https://example.com/kazilayer/events",
                    "event_keys": ["work_order.updated", "request.created"],
                    "secret_ciphertext": encrypt_secret("seed-webhook-secret"),
                    "secret_version": 1,
                    "is_active": False,
                },
            )
            WebhookDelivery.objects.update_or_create(
                delivery_key=f"seed:{organization.slug}:delivery:1",
                defaults={
                    "endpoint": endpoint,
                    "event_id": f"seed:{organization.slug}:work-order",
                    "attempt": 1,
                    "request_body_hash": hashlib.sha256(b"seed-event").hexdigest(),
                    "response_status": 202,
                    "response_excerpt": "Accepted",
                    "delivered_at": now,
                },
            )

            work_order = WorkOrder.objects.filter(organization=organization).first()
            resource_id = work_order.id if work_order else None
            for sequence, event_type, payload in (
                (1, "work_order.created", {"invalidate": ["work_orders", "dashboard"]}),
                (
                    2,
                    "work_order.scheduled",
                    {"status": "scheduled", "invalidate": ["work_orders"]},
                ),
            ):
                RealtimeEvent.objects.update_or_create(
                    organization=organization,
                    stream_key=f"tenant:{organization.slug}",
                    sequence=sequence,
                    defaults={
                        "event_id": f"seed:{organization.slug}:realtime:{sequence}",
                        "event_type": event_type,
                        "resource_type": "work_order",
                        "resource_id": resource_id,
                        "version": sequence,
                        "payload_json": payload,
                    },
                )
            if resource_id:
                BulkOperation.objects.update_or_create(
                    id=stable_id(organization, "bulk"),
                    defaults={
                        "organization": organization,
                        "requested_by": owner,
                        "resource_type": "work_order",
                        "action_key": "export",
                        "selection_mode": "explicit_ids",
                        "selected_ids_json": [str(resource_id)],
                        "query_snapshot_json": {},
                        "action_params_json": {"format": "csv"},
                        "preview_count": 1,
                        "status": "completed",
                        "total_count": 1,
                        "processed_count": 1,
                        "success_count": 1,
                        "failure_count": 0,
                        "started_at": now,
                        "completed_at": now,
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded seven Adaptive Convergence feature slices for every active tenant."
            )
        )
