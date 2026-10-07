import uuid

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Avg, Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.accounts.api import body, error, membership_or_error
from apps.accounts.security import encrypt_secret, generate_token
from apps.operations.models import ServiceRequest, WorkOrder

from .models import (
    BulkOperation,
    ContractField,
    ContractVersion,
    Dashboard,
    RealtimeEvent,
    ViewRecipe,
    WebhookEndpoint,
)


def validate_and_save(item):
    item.full_clean()
    item.save()


def serialize_field(item):
    return {
        "id": str(item.id),
        "field_key": item.field_key,
        "label": item.label,
        "field_type": item.field_type,
        "required": item.required,
        "default_value": item.default_value,
        "options": item.options_json,
        "help_text": item.help_text,
        "presentation": item.presentation,
        "sort_order": item.sort_order,
        "validation": item.validation_json,
    }


def serialize_contract(item, include_schema=True):
    result = {
        "id": str(item.id),
        "contract_key": item.contract_key,
        "name": item.name,
        "entity_type": item.entity_type,
        "version_number": item.version_number,
        "status": item.status,
        "change_notes": item.change_notes,
        "plain_change_notes": item.plain_change_notes,
        "published_at": item.published_at.isoformat() if item.published_at else None,
        "retired_at": item.retired_at.isoformat() if item.retired_at else None,
    }
    if include_schema:
        result.update(
            {
                "schema": item.schema_json,
                "validation": item.validation_json,
                "workflow": item.workflow_json,
                "permissions": item.permission_json,
                "ui_metadata": item.ui_metadata_json,
                "fields": [serialize_field(field) for field in item.fields.all()],
            }
        )
    return result


@require_http_methods(["GET", "POST"])
def contracts(request, slug):
    membership, response = membership_or_error(
        request, slug, "contract.list" if request.method == "GET" else "contract.create"
    )
    if response:
        return response
    if request.method == "GET":
        rows = (
            ContractVersion.objects.prefetch_related("fields")
            .filter(organization=membership.organization)
            .order_by("contract_key", "-version_number")[:100]
        )
        return JsonResponse({"contracts": [serialize_contract(item) for item in rows]})
    payload = body(request)
    key = str(payload.get("contract_key", "")).strip()
    previous = (
        ContractVersion.objects.filter(
            organization=membership.organization, contract_key=key
        )
        .order_by("-version_number")
        .first()
    )
    item = ContractVersion(
        organization=membership.organization,
        contract_key=key,
        name=str(payload.get("name", ""))[:180],
        entity_type=str(payload.get("entity_type", ""))[:80],
        version_number=(previous.version_number + 1) if previous else 1,
        schema_json=payload.get("schema", {}),
        validation_json=payload.get("validation", {}),
        workflow_json=payload.get("workflow", {}),
        permission_json=payload.get("permissions", {}),
        ui_metadata_json=payload.get("ui_metadata", {}),
        change_notes=str(payload.get("change_notes", "")),
        predecessor=previous,
    )
    try:
        with transaction.atomic():
            validate_and_save(item)
            for index, definition in enumerate(payload.get("fields", [])):
                field = ContractField(
                    contract_version=item,
                    field_key=definition.get("field_key", ""),
                    label=definition.get("label", ""),
                    field_type=definition.get("field_type", "text"),
                    required=bool(definition.get("required")),
                    default_value=definition.get("default_value"),
                    options_json=definition.get("options", []),
                    help_text=definition.get("help_text", ""),
                    presentation="wysiwyg"
                    if definition.get("field_type") == "rich_text"
                    else definition.get("presentation", "input"),
                    sort_order=index,
                    validation_json=definition.get("validation", {}),
                )
                validate_and_save(field)
    except ValidationError as exc:
        return error(" ".join(exc.messages))
    return JsonResponse({"contract": serialize_contract(item)}, status=201)


@require_http_methods(["POST"])
def publish_contract(request, slug, contract_id):
    membership, response = membership_or_error(request, slug, "contract.publish")
    if response:
        return response
    item = (
        ContractVersion.objects.prefetch_related("fields")
        .filter(organization=membership.organization, id=contract_id, status="draft")
        .first()
    )
    if item is None:
        return error("Draft contract not found", 404, "NOT_FOUND")
    if not item.fields.exists():
        return error("A contract must contain at least one field before publication")
    item.status = "published"
    item.published_by = request.user
    item.published_at = timezone.now()
    item.save(
        update_fields=[
            "status",
            "published_by",
            "published_at",
            "change_notes",
            "plain_change_notes",
        ]
    )
    return JsonResponse({"contract": serialize_contract(item)})


@require_http_methods(["GET", "POST"])
def dynamic_form(request, slug, contract_key):
    membership, response = membership_or_error(request, slug, "dynamic_form.use")
    if response:
        return response
    item = (
        ContractVersion.objects.prefetch_related("fields")
        .filter(
            organization=membership.organization,
            contract_key=contract_key,
            status="published",
        )
        .order_by("-version_number")
        .first()
    )
    if item is None:
        return error("Published contract not found", 404, "NOT_FOUND")
    fields = [serialize_field(field) for field in item.fields.all()]
    editable = [field["field_key"] for field in fields]
    if request.method == "GET":
        return JsonResponse(
            {
                "form": {
                    "contract_version_id": str(item.id),
                    "mode": request.GET.get("mode", "create"),
                    "field_values": {
                        field["field_key"]: field["default_value"] for field in fields
                    },
                    "initial_values": {},
                    "field_errors": {},
                    "visible_fields": editable,
                    "editable_fields": editable,
                    "dirty_fields": [],
                    "expected_record_version": None,
                    "submit_action_key": f"{item.entity_type}.create",
                    "idempotency_key": str(uuid.uuid4()),
                    "fields": fields,
                }
            }
        )
    payload = body(request)
    values = payload.get("field_values", {})
    errors = {}
    for field in fields:
        current = values.get(field["field_key"])
        if field["required"] and current in (None, "", []):
            errors[field["field_key"]] = "This field is required."
    status = 400 if errors else 200
    return JsonResponse(
        {
            "form": {
                "contract_version_id": str(item.id),
                "mode": payload.get("mode", "create"),
                "field_values": values,
                "initial_values": payload.get("initial_values", {}),
                "field_errors": errors,
                "form_error": "Validation failed" if errors else "",
                "visible_fields": editable,
                "editable_fields": editable,
                "dirty_fields": list(values),
                "expected_record_version": payload.get("expected_record_version"),
                "submit_action_key": f"{item.entity_type}.create",
                "idempotency_key": payload.get("idempotency_key"),
            }
        },
        status=status,
    )


@require_http_methods(["GET", "POST"])
def view_recipes(request, slug):
    membership, response = membership_or_error(
        request,
        slug,
        "view_recipe.list" if request.method == "GET" else "view_recipe.create",
    )
    if response:
        return response
    if request.method == "POST":
        payload = body(request)
        contract = ContractVersion.objects.filter(
            organization=membership.organization,
            id=payload.get("contract_version_id"),
            status="published",
        ).first()
        if contract is None:
            return error("A published tenant contract is required")
        item = ViewRecipe(
            organization=membership.organization,
            contract_version=contract,
            recipe_key=payload.get("recipe_key", ""),
            recipe_type=payload.get("recipe_type", "summary_card"),
            title_template=payload.get("title_template", ""),
            slot_mapping_json=payload.get("slot_mapping", {}),
            field_order_json=payload.get("field_order", []),
            action_keys_json=payload.get("action_keys", []),
            responsive_rules_json=payload.get("responsive_rules", {}),
            density=payload.get("density", "comfortable"),
        )
        validate_and_save(item)
        return JsonResponse({"recipe_id": str(item.id)}, status=201)
    rows = (
        ViewRecipe.objects.select_related("contract_version")
        .filter(organization=membership.organization, is_active=True)
        .order_by("recipe_key", "recipe_type")
    )
    return JsonResponse(
        {
            "recipes": [
                {
                    "id": str(item.id),
                    "contract_version_id": str(item.contract_version_id),
                    "contract_key": item.contract_version.contract_key,
                    "recipe_key": item.recipe_key,
                    "recipe_type": item.recipe_type,
                    "title_template": item.title_template,
                    "slot_mapping": item.slot_mapping_json,
                    "field_order": item.field_order_json,
                    "action_keys": item.action_keys_json,
                    "responsive_rules": item.responsive_rules_json,
                    "density": item.density,
                    "is_active": item.is_active,
                }
                for item in rows
            ]
        }
    )


def metric_value(metric, organization):
    if metric.key == "open_requests":
        return (
            ServiceRequest.objects.filter(organization=organization)
            .exclude(status__in=["rejected", "converted"])
            .count()
        )
    if metric.key == "active_work":
        return WorkOrder.objects.filter(
            organization=organization,
            status__in=["scheduled", "in_progress", "blocked"],
        ).count()
    if metric.aggregation == "count":
        return 0
    if metric.aggregation == "avg" and metric.measure_field_key == "version":
        return (
            WorkOrder.objects.filter(organization=organization).aggregate(
                value=Avg("version")
            )["value"]
            or 0
        )
    return 0


@require_http_methods(["GET", "POST"])
def dashboards(request, slug):
    membership, response = membership_or_error(
        request,
        slug,
        "dashboard.list" if request.method == "GET" else "dashboard.create",
    )
    if response:
        return response
    if request.method == "POST":
        payload = body(request)
        item = Dashboard(
            organization=membership.organization,
            owner_user=request.user
            if payload.get("visibility", "private") == "private"
            else None,
            name=str(payload.get("name", ""))[:180],
            visibility=payload.get("visibility", "private"),
        )
        validate_and_save(item)
        return JsonResponse({"dashboard_id": str(item.id)}, status=201)
    rows = (
        Dashboard.objects.prefetch_related("widgets__metric_definition")
        .filter(organization=membership.organization)
        .filter(Q(visibility="organization") | Q(owner_user=request.user))
    )
    data = []
    for dashboard in rows:
        widgets = [
            {
                "id": str(widget.id),
                "widget_type": widget.widget_type,
                "layout": widget.layout_json,
                "display_options": widget.display_options_json,
                "metric": {
                    "key": widget.metric_definition.key,
                    "name": widget.metric_definition.name,
                    "description": widget.metric_definition.description,
                    "unit": widget.metric_definition.unit,
                    "value": metric_value(
                        widget.metric_definition, membership.organization
                    ),
                    "version": widget.metric_definition.version,
                }
                if widget.metric_definition
                else None,
            }
            for widget in dashboard.widgets.all()
        ]
        data.append(
            {
                "id": str(dashboard.id),
                "name": dashboard.name,
                "visibility": dashboard.visibility,
                "widgets": widgets,
                "created_at": dashboard.created_at.isoformat(),
            }
        )
    return JsonResponse({"dashboards": data})


@require_http_methods(["GET", "POST"])
def webhooks(request, slug):
    membership, response = membership_or_error(
        request, slug, "webhook.list" if request.method == "GET" else "webhook.create"
    )
    if response:
        return response
    if request.method == "POST":
        payload = body(request)
        raw_secret = generate_token(32)
        item = WebhookEndpoint(
            organization=membership.organization,
            name=str(payload.get("name", ""))[:180],
            url=str(payload.get("url", "")),
            event_keys=payload.get("event_keys", []),
            secret_ciphertext=encrypt_secret(raw_secret),
            is_active=True,
        )
        try:
            validate_and_save(item)
        except ValidationError as exc:
            return error(" ".join(exc.messages))
        return JsonResponse(
            {
                "endpoint": {
                    "id": str(item.id),
                    "name": item.name,
                    "url": item.url,
                    "event_keys": item.event_keys,
                    "secret_version": item.secret_version,
                    "is_active": item.is_active,
                },
                "signing_secret": raw_secret,
            },
            status=201,
        )
    rows = WebhookEndpoint.objects.filter(
        organization=membership.organization
    ).order_by("name")
    return JsonResponse(
        {
            "endpoints": [
                {
                    "id": str(item.id),
                    "name": item.name,
                    "url": item.url,
                    "event_keys": item.event_keys,
                    "secret_version": item.secret_version,
                    "is_active": item.is_active,
                    "created_at": item.created_at.isoformat(),
                    "deliveries": [
                        {
                            "id": str(delivery.id),
                            "event_id": delivery.event_id,
                            "delivery_key": delivery.delivery_key,
                            "attempt": delivery.attempt,
                            "response_status": delivery.response_status,
                            "response_excerpt": delivery.response_excerpt,
                            "next_retry_at": delivery.next_retry_at.isoformat()
                            if delivery.next_retry_at
                            else None,
                            "delivered_at": delivery.delivered_at.isoformat()
                            if delivery.delivered_at
                            else None,
                        }
                        for delivery in item.deliveries.order_by("-attempt")[:20]
                    ],
                }
                for item in rows
            ]
        }
    )


@require_http_methods(["POST"])
def rotate_webhook(request, slug, endpoint_id):
    membership, response = membership_or_error(request, slug, "webhook.rotate")
    if response:
        return response
    item = WebhookEndpoint.objects.filter(
        organization=membership.organization, id=endpoint_id
    ).first()
    if item is None:
        return error("Webhook endpoint not found", 404, "NOT_FOUND")
    raw_secret = generate_token(32)
    item.secret_ciphertext = encrypt_secret(raw_secret)
    item.secret_version += 1
    item.save(update_fields=["secret_ciphertext", "secret_version"])
    return JsonResponse(
        {
            "endpoint_id": str(item.id),
            "secret_version": item.secret_version,
            "signing_secret": raw_secret,
        }
    )


@require_http_methods(["GET"])
def realtime(request, slug):
    membership, response = membership_or_error(request, slug, "realtime.subscribe")
    if response:
        return response
    stream = request.GET.get("stream", f"tenant:{slug}")[:180]
    after = max(0, int(request.GET.get("after", "0")))
    rows = list(
        RealtimeEvent.objects.filter(
            organization=membership.organization, stream_key=stream, sequence__gt=after
        ).order_by("sequence")[:100]
    )
    gap = bool(rows and after and rows[0].sequence != after + 1)
    return JsonResponse(
        {
            "stream_key": stream,
            "connection_state": "live",
            "last_sequence": rows[-1].sequence if rows else after,
            "gap_detected": gap,
            "events": [
                {
                    "event_id": item.event_id,
                    "sequence": item.sequence,
                    "event_type": item.event_type,
                    "resource_type": item.resource_type,
                    "resource_id": str(item.resource_id) if item.resource_id else None,
                    "version": item.version,
                    "payload": item.payload_json,
                    "emitted_at": item.emitted_at.isoformat(),
                }
                for item in rows
            ],
            "refetch_required": gap,
        }
    )


@require_http_methods(["GET", "POST"])
def bulk_operations(request, slug):
    membership, response = membership_or_error(
        request, slug, "bulk.list" if request.method == "GET" else "bulk.preview"
    )
    if response:
        return response
    if request.method == "POST":
        payload = body(request)
        ids = payload.get("selected_ids", [])
        preview_count = (
            len(ids)
            if payload.get("selection_mode", "explicit_ids") == "explicit_ids"
            else min(int(payload.get("estimated_count", 0)), 5000)
        )
        item = BulkOperation(
            organization=membership.organization,
            requested_by=request.user,
            resource_type=str(payload.get("resource_type", "work_order"))[:80],
            action_key=str(payload.get("action_key", "export"))[:80],
            selection_mode=payload.get("selection_mode", "explicit_ids"),
            selected_ids_json=ids,
            query_snapshot_json=payload.get("query_snapshot", {}),
            action_params_json=payload.get("action_params", {}),
            preview_count=preview_count,
        )
        try:
            validate_and_save(item)
        except ValidationError as exc:
            return error(" ".join(exc.messages))
        return JsonResponse({"operation": serialize_bulk(item)}, status=201)
    rows = BulkOperation.objects.filter(organization=membership.organization).order_by(
        "-created_at"
    )[:100]
    return JsonResponse({"operations": [serialize_bulk(item) for item in rows]})


def serialize_bulk(item):
    return {
        "id": str(item.id),
        "resource_type": item.resource_type,
        "action_key": item.action_key,
        "selection_mode": item.selection_mode,
        "selected_ids": item.selected_ids_json,
        "query_snapshot": item.query_snapshot_json,
        "action_params": item.action_params_json,
        "preview_count": item.preview_count,
        "status": item.status,
        "total_count": item.total_count,
        "processed_count": item.processed_count,
        "success_count": item.success_count,
        "failure_count": item.failure_count,
        "started_at": item.started_at.isoformat() if item.started_at else None,
        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
        "created_at": item.created_at.isoformat(),
    }


@require_http_methods(["POST"])
def confirm_bulk_operation(request, slug, operation_id):
    membership, response = membership_or_error(request, slug, "bulk.execute")
    if response:
        return response
    item = BulkOperation.objects.filter(
        organization=membership.organization,
        id=operation_id,
        requested_by=request.user,
        status="draft",
    ).first()
    if item is None:
        return error("Draft bulk operation not found", 404, "NOT_FOUND")
    item.status = "queued"
    item.total_count = item.preview_count
    item.save(update_fields=["status", "total_count"])
    return JsonResponse({"operation": serialize_bulk(item)})
