import hashlib
import uuid
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.accounts.api import body, error, membership_or_error

from .models import (
    Assignment,
    AuditEvent,
    Comment,
    ExportJob,
    FileAsset,
    ImportJob,
    Notification,
    NotificationPreference,
    SearchDocument,
    ServiceRequest,
    SlaClockEvent,
    SlaPolicy,
    Technician,
    UserFeedback,
    WorkOrder,
    WorkTransition,
)
from .scheduling import add_business_minutes


def value(item, field):
    raw = getattr(item, field)
    if isinstance(raw, uuid.UUID):
        return str(raw)
    if hasattr(raw, "isoformat"):
        return raw.isoformat()
    return raw


def projection(item, fields):
    return {field: value(item, field) for field in ("id", *fields)}


def record_audit(organization, actor, event_type, item, after, reason=""):
    AuditEvent.objects.create(
        organization=organization,
        actor_user=actor,
        event_type=event_type,
        resource_type=item._meta.model_name,
        resource_id=item.id,
        after_summary=after,
        reason=reason,
    )


def validated_save(item):
    item.full_clean()
    item.save()


@require_http_methods(["GET", "POST"])
def feedback(request, slug):
    membership, response = membership_or_error(
        request, slug, "feedback.list" if request.method == "GET" else "feedback.create"
    )
    if response:
        return response
    if request.method == "POST":
        payload = body(request)
        item = UserFeedback(
            organization=membership.organization,
            user=request.user,
            route=str(payload.get("route", ""))[:500],
            role_key=membership.role_policy.key,
            viewport_width=payload.get("viewport_width"),
            viewport_height=payload.get("viewport_height"),
            category=payload.get("category", "other"),
            message=str(payload.get("message", "")),
            consent_context_capture=bool(payload.get("consent_context_capture")),
        )
        validated_save(item)
        return JsonResponse(
            {
                "feedback": projection(
                    item,
                    ("route", "category", "message", "triage_status", "created_at"),
                )
            },
            status=201,
        )
    rows = UserFeedback.objects.filter(organization=membership.organization).order_by(
        "-created_at"
    )[:100]
    return JsonResponse(
        {
            "feedback": [
                projection(
                    item,
                    ("route", "category", "message", "triage_status", "created_at"),
                )
                for item in rows
            ]
        }
    )


@require_http_methods(["GET", "POST"])
def service_requests(request, slug):
    membership, response = membership_or_error(
        request, slug, "request.list" if request.method == "GET" else "request.create"
    )
    if response:
        return response
    rows = ServiceRequest.objects.filter(organization=membership.organization)
    if membership.role_policy.key == "customer":
        rows = rows.filter(created_by=request.user)
    if request.method == "GET":
        fields = (
            "location_text",
            "urgency",
            "description",
            "preferred_start_at",
            "preferred_end_at",
            "source",
            "status",
            "version",
            "created_at",
        )
        return JsonResponse(
            {
                "requests": [
                    projection(item, fields)
                    for item in rows.order_by("-created_at")[:100]
                ]
            }
        )
    payload = body(request)
    item = ServiceRequest(
        organization=membership.organization,
        created_by=request.user,
        location_text=str(payload.get("location_text", ""))[:255],
        location_point=payload.get("location_point"),
        urgency=payload.get("urgency", "normal"),
        description=str(payload.get("description", "")),
        preferred_start_at=payload.get("preferred_start_at") or None,
        preferred_end_at=payload.get("preferred_end_at") or None,
        source="customer_portal"
        if membership.role_policy.key == "customer"
        else "staff",
        idempotency_key=str(payload.get("idempotency_key") or uuid.uuid4()),
    )
    try:
        validated_save(item)
    except ValidationError as exc:
        return error(" ".join(exc.messages))
    record_audit(
        membership.organization,
        request.user,
        "request.created",
        item,
        {"status": item.status, "urgency": item.urgency},
    )
    return JsonResponse(
        {
            "request": projection(
                item, ("status", "urgency", "description", "created_at")
            )
        },
        status=201,
    )


@require_http_methods(["GET", "POST"])
def comments(request, slug):
    membership, response = membership_or_error(
        request, slug, "comment.list" if request.method == "GET" else "comment.create"
    )
    if response:
        return response
    rows = Comment.objects.filter(organization=membership.organization).select_related(
        "author_user"
    )
    if membership.role_policy.key == "customer":
        rows = rows.filter(
            Q(visibility="customer_visible") | Q(author_user=request.user)
        )
    if request.method == "GET":
        return JsonResponse(
            {
                "comments": [
                    {
                        **projection(
                            item,
                            (
                                "resource_type",
                                "resource_id",
                                "body",
                                "plain_text",
                                "visibility",
                                "created_at",
                                "version",
                            ),
                        ),
                        "author": item.author_user.display_name,
                    }
                    for item in rows.order_by("-created_at")[:100]
                ]
            }
        )
    payload = body(request)
    try:
        resource_id = uuid.UUID(str(payload.get("resource_id")))
    except ValueError:
        return error("A valid target resource is required")
    item = Comment(
        organization=membership.organization,
        author_user=request.user,
        resource_type=str(payload.get("resource_type", "work_order"))[:80],
        resource_id=resource_id,
        body=str(payload.get("body", "")),
        visibility=payload.get("visibility", "internal"),
    )
    if membership.role_policy.key == "customer":
        item.visibility = "customer_visible"
    validated_save(item)
    return JsonResponse(
        {
            "comment": projection(
                item, ("body", "plain_text", "visibility", "created_at")
            )
        },
        status=201,
    )


@require_http_methods(["GET", "POST"])
def files(request, slug):
    membership, response = membership_or_error(
        request, slug, "file.list" if request.method == "GET" else "file.create"
    )
    if response:
        return response
    rows = FileAsset.objects.filter(organization=membership.organization)
    if membership.role_policy.key == "customer":
        rows = rows.filter(
            Q(visibility="customer_visible") | Q(uploaded_by=request.user)
        )
    if request.method == "GET":
        fields = (
            "resource_type",
            "resource_id",
            "original_name",
            "mime_type",
            "size_bytes",
            "upload_status",
            "scan_status",
            "visibility",
            "created_at",
            "ready_at",
        )
        return JsonResponse(
            {
                "files": [
                    projection(item, fields)
                    for item in rows.order_by("-created_at")[:100]
                ]
            }
        )
    upload = request.FILES.get("file")
    if upload is None or upload.size > 15 * 1024 * 1024:
        return error("A file up to 15 MB is required")
    digest = hashlib.sha256()
    for chunk in upload.chunks():
        digest.update(chunk)
    upload.seek(0)
    resource_id = request.POST.get("resource_id") or uuid.uuid4()
    item = FileAsset(
        organization=membership.organization,
        uploaded_by=request.user,
        resource_type=request.POST.get("resource_type", "general")[:80],
        resource_id=resource_id,
        original_name=upload.name[:255],
        object_key=f"{membership.organization_id}/{uuid.uuid4()}",
        file=upload,
        mime_type=upload.content_type or "application/octet-stream",
        size_bytes=upload.size,
        sha256=digest.hexdigest(),
        upload_status="ready",
        scan_status="pending",
        visibility=request.POST.get("visibility", "internal"),
        ready_at=timezone.now(),
    )
    if membership.role_policy.key == "customer":
        item.visibility = "customer_visible"
    validated_save(item)
    return JsonResponse(
        {
            "file": projection(
                item,
                (
                    "original_name",
                    "mime_type",
                    "size_bytes",
                    "upload_status",
                    "scan_status",
                ),
            )
        },
        status=201,
    )


@require_http_methods(["GET"])
def search(request, slug):
    membership, response = membership_or_error(request, slug, "search.query")
    if response:
        return response
    query = request.GET.get("q", "").strip()[:200]
    types = [
        value
        for value in request.GET.getlist("type")
        if value in membership.role_policy.resource_scope
    ]
    rows = SearchDocument.objects.filter(organization=membership.organization)
    if query:
        rows = rows.filter(Q(title__icontains=query) | Q(body_text__icontains=query))
    if types:
        rows = rows.filter(resource_type__in=types)
    rows = rows.order_by("-rank_boost", "title")[:50]
    return JsonResponse(
        {
            "query": query,
            "results": [
                projection(
                    item,
                    (
                        "resource_type",
                        "resource_id",
                        "title",
                        "body_text",
                        "rank_boost",
                        "updated_at",
                    ),
                )
                for item in rows
            ],
        }
    )


@require_http_methods(["GET", "POST"])
def data_jobs(request, slug):
    membership, response = membership_or_error(
        request, slug, "data_job.list" if request.method == "GET" else "data_job.create"
    )
    if response:
        return response
    if request.method == "POST":
        payload = body(request)
        if payload.get("kind") != "export":
            return error(
                "Uploads create import jobs through the file pipeline; this endpoint currently creates exports."
            )
        item = ExportJob(
            organization=membership.organization,
            requested_by=request.user,
            resource_type=str(payload.get("resource_type", "service_request"))[:80],
            filters_json=payload.get("filters", {}),
            columns_json=payload.get("columns", []),
            manifest_json={
                "requested_at": timezone.now().isoformat(),
                "filters": payload.get("filters", {}),
                "columns": payload.get("columns", []),
            },
        )
        validated_save(item)
        return JsonResponse(
            {
                "export": projection(
                    item, ("resource_type", "status", "manifest_json", "created_at")
                )
            },
            status=201,
        )
    imports = ImportJob.objects.filter(organization=membership.organization).order_by(
        "-created_at"
    )[:50]
    exports = ExportJob.objects.filter(organization=membership.organization).order_by(
        "-created_at"
    )[:50]
    return JsonResponse(
        {
            "imports": [
                projection(
                    item,
                    (
                        "resource_type",
                        "status",
                        "total_rows",
                        "valid_rows",
                        "invalid_rows",
                        "created_at",
                        "completed_at",
                    ),
                )
                for item in imports
            ],
            "exports": [
                projection(
                    item, ("resource_type", "status", "manifest_json", "created_at")
                )
                for item in exports
            ],
        }
    )


@require_http_methods(["GET"])
def audit(request, slug):
    membership, response = membership_or_error(request, slug, "audit.list")
    if response:
        return response
    rows = (
        AuditEvent.objects.filter(organization=membership.organization)
        .select_related("actor_user")
        .order_by("-created_at")[:100]
    )
    return JsonResponse(
        {
            "events": [
                {
                    **projection(
                        item,
                        (
                            "event_type",
                            "resource_type",
                            "resource_id",
                            "before_summary",
                            "after_summary",
                            "reason",
                            "created_at",
                        ),
                    ),
                    "actor": item.actor_user.display_name
                    if item.actor_user
                    else "System",
                }
                for item in rows
            ]
        }
    )


@require_http_methods(["GET", "POST"])
def work_orders(request, slug):
    membership, response = membership_or_error(
        request,
        slug,
        "work_order.list" if request.method == "GET" else "work_order.create",
    )
    if response:
        return response
    rows = WorkOrder.objects.filter(organization=membership.organization)
    fields = (
        "title",
        "instructions",
        "plain_instructions",
        "priority",
        "status",
        "scheduled_start_at",
        "scheduled_end_at",
        "completion_summary",
        "version",
        "created_at",
        "updated_at",
    )
    if request.method == "GET":
        return JsonResponse(
            {
                "work_orders": [
                    projection(item, fields)
                    for item in rows.order_by("-created_at")[:100]
                ]
            }
        )
    payload = body(request)
    item = WorkOrder(
        organization=membership.organization,
        title=str(payload.get("title", ""))[:255],
        instructions=str(payload.get("instructions", "")),
        priority=payload.get("priority", "normal"),
        scheduled_start_at=payload.get("scheduled_start_at") or None,
        scheduled_end_at=payload.get("scheduled_end_at") or None,
    )
    validated_save(item)
    WorkTransition.objects.create(
        work_order=item,
        to_state="new",
        actor_user=request.user,
        evidence_required_met=True,
    )
    record_audit(
        membership.organization,
        request.user,
        "work_order.created",
        item,
        {"status": item.status, "title": item.title},
    )
    return JsonResponse({"work_order": projection(item, fields)}, status=201)


@require_http_methods(["POST"])
def transition_work_order(request, slug, work_order_id):
    membership, response = membership_or_error(request, slug, "work_order.transition")
    if response:
        return response
    item = WorkOrder.objects.filter(
        organization=membership.organization, id=work_order_id
    ).first()
    if item is None:
        return error("Work order not found", 404, "NOT_FOUND")
    payload = body(request)
    target = str(payload.get("to_state", ""))
    allowed = {
        "new": {"scheduled", "cancelled"},
        "scheduled": {"in_progress", "cancelled"},
        "in_progress": {"completed", "blocked"},
        "blocked": {"in_progress", "cancelled"},
    }
    if target not in allowed.get(item.status, set()):
        return error(
            f"Transition from {item.status} to {target} is not allowed",
            409,
            "TRANSITION_REJECTED",
        )
    evidence_met = bool(payload.get("evidence_required_met"))
    if target == "completed" and not evidence_met:
        return error("Completion evidence is required", 409, "EVIDENCE_REQUIRED")
    before = item.status
    with transaction.atomic():
        item.status = target
        item.version += 1
        if target == "completed":
            item.completion_summary = str(payload.get("completion_summary", ""))
        validated_save(item)
        WorkTransition.objects.create(
            work_order=item,
            from_state=before,
            to_state=target,
            actor_user=request.user,
            reason=str(payload.get("reason", "")),
            evidence_required_met=evidence_met,
        )
        record_audit(
            membership.organization,
            request.user,
            "work_order.transitioned",
            item,
            {"status": target},
            str(payload.get("reason", "")),
        )
    return JsonResponse(
        {"work_order": projection(item, ("status", "version", "completion_summary"))}
    )


@require_http_methods(["GET"])
def notifications(request, slug):
    membership, response = membership_or_error(request, slug, "notification.list")
    if response:
        return response
    rows = Notification.objects.filter(
        organization=membership.organization, recipient_user=request.user
    ).order_by("-created_at")[:100]
    return JsonResponse(
        {
            "notifications": [
                projection(
                    item,
                    (
                        "event_id",
                        "channel",
                        "status",
                        "payload_json",
                        "sent_at",
                        "read_at",
                        "created_at",
                    ),
                )
                for item in rows
            ]
        }
    )


@require_http_methods(["GET", "POST"])
def notification_preferences(request, slug):
    _membership, response = membership_or_error(
        request, slug, "notification.preference"
    )
    if response:
        return response
    if request.method == "POST":
        payload = body(request)
        item, _ = NotificationPreference.objects.update_or_create(
            user=request.user,
            event_key=str(payload.get("event_key", "work_order.updated"))[:120],
            defaults={
                "in_app": bool(payload.get("in_app", True)),
                "email": bool(payload.get("email", False)),
                "quiet_hours_json": payload.get("quiet_hours"),
            },
        )
        return JsonResponse(
            {
                "preference": projection(
                    item, ("event_key", "in_app", "email", "quiet_hours_json")
                )
            }
        )
    rows = NotificationPreference.objects.filter(user=request.user).order_by(
        "event_key"
    )
    return JsonResponse(
        {
            "preferences": [
                projection(item, ("event_key", "in_app", "email", "quiet_hours_json"))
                for item in rows
            ]
        }
    )


@require_http_methods(["GET", "POST"])
def sla_policies(request, slug):
    membership, response = membership_or_error(
        request, slug, "sla.list" if request.method == "GET" else "sla.manage"
    )
    if response:
        return response
    if request.method == "POST":
        payload = body(request)
        latest = (
            SlaPolicy.objects.filter(
                organization=membership.organization,
                priority_key=payload.get("priority_key", "normal"),
            )
            .order_by("-version")
            .first()
        )
        item = SlaPolicy(
            organization=membership.organization,
            name=str(payload.get("name", ""))[:160],
            priority_key=payload.get("priority_key", "normal"),
            response_minutes=int(payload.get("response_minutes", 60)),
            completion_minutes=int(payload.get("completion_minutes", 480)),
            business_calendar_json=payload.get("business_calendar", {}),
            pause_state_keys=payload.get("pause_state_keys", []),
            effective_from=payload.get("effective_from") or timezone.now(),
            version=(latest.version + 1) if latest else 1,
        )
        validated_save(item)
        return JsonResponse(
            {
                "policy": projection(
                    item,
                    (
                        "name",
                        "priority_key",
                        "response_minutes",
                        "completion_minutes",
                        "business_calendar_json",
                        "pause_state_keys",
                        "effective_from",
                        "version",
                    ),
                )
            },
            status=201,
        )
    rows = SlaPolicy.objects.filter(organization=membership.organization).order_by(
        "priority_key", "-version"
    )[:100]
    return JsonResponse(
        {
            "policies": [
                projection(
                    item,
                    (
                        "name",
                        "priority_key",
                        "response_minutes",
                        "completion_minutes",
                        "business_calendar_json",
                        "pause_state_keys",
                        "effective_from",
                        "effective_to",
                        "version",
                    ),
                )
                for item in rows
            ]
        }
    )


@require_http_methods(["POST"])
def apply_sla(request, slug, work_order_id):
    membership, response = membership_or_error(request, slug, "sla.apply")
    if response:
        return response
    with transaction.atomic():
        item = (
            WorkOrder.objects.select_for_update()
            .filter(id=work_order_id, organization=membership.organization)
            .first()
        )
        if item is None:
            return error("Work order not found", 404, "NOT_FOUND")
        policy = (
            SlaPolicy.objects.filter(
                organization=membership.organization,
                priority_key=item.priority,
                effective_from__lte=item.created_at,
            )
            .order_by("-version")
            .first()
        )
        if policy is None:
            return error(
                "No effective SLA policy exists for this priority",
                409,
                "SLA_POLICY_MISSING",
            )
        item.sla_policy = policy
        item.response_due_at = add_business_minutes(
            item.created_at, policy.response_minutes, policy.business_calendar_json
        )
        item.completion_due_at = add_business_minutes(
            item.created_at, policy.completion_minutes, policy.business_calendar_json
        )
        item.sla_status = "on_track"
        item.version += 1
        item.save()
        SlaClockEvent.objects.create(
            work_order=item,
            event_type="started",
            policy_version=policy.version,
            reason="Policy applied deterministically",
        )
    return JsonResponse(
        {
            "work_order": projection(
                item,
                (
                    "sla_policy_id",
                    "response_due_at",
                    "completion_due_at",
                    "sla_status",
                    "version",
                ),
            )
        }
    )


@require_http_methods(["GET", "POST"])
def dispatch_board(request, slug):
    membership, response = membership_or_error(
        request, slug, "dispatch.view" if request.method == "GET" else "dispatch.assign"
    )
    if response:
        return response
    if request.method == "POST":
        payload = body(request)
        try:
            start_at = datetime.fromisoformat(str(payload.get("start_at", "")))
            end_at = datetime.fromisoformat(str(payload.get("end_at", "")))
        except ValueError:
            return error("Valid timezone-aware start and end times are required")
        if timezone.is_naive(start_at) or timezone.is_naive(end_at):
            return error("Assignment times must include a timezone offset")
        with transaction.atomic():
            existing = None
            if payload.get("assignment_id"):
                existing = (
                    Assignment.objects.select_for_update()
                    .filter(
                        id=payload["assignment_id"],
                        organization=membership.organization,
                    )
                    .first()
                )
                if existing is None:
                    return error("Assignment not found", 404, "NOT_FOUND")
                if int(payload.get("expected_version", 0)) != existing.version:
                    return error(
                        "Assignment changed since the board was loaded",
                        409,
                        "VERSION_CONFLICT",
                    )
            technician = (
                Technician.objects.select_for_update()
                .filter(
                    id=payload.get("technician_id"),
                    organization=membership.organization,
                    is_active=True,
                )
                .first()
            )
            work_order = (
                WorkOrder.objects.select_for_update()
                .filter(
                    id=payload.get("work_order_id"),
                    organization=membership.organization,
                )
                .first()
            )
            if technician is None or work_order is None:
                return error("Technician or work order not found", 404, "NOT_FOUND")
            conflict = Assignment.objects.filter(
                technician=technician,
                status__in=["scheduled", "accepted", "active"],
                start_at__lt=end_at,
                end_at__gt=start_at,
            )
            if existing:
                conflict = conflict.exclude(id=existing.id)
            conflict = conflict.exists()
            if conflict:
                return error(
                    "The technician already has an overlapping assignment",
                    409,
                    "SCHEDULE_CONFLICT",
                )
            item = existing or Assignment(
                organization=membership.organization,
                work_order=work_order,
                assigned_by=request.user,
            )
            item.work_order = work_order
            item.technician = technician
            item.start_at = start_at
            item.end_at = end_at
            item.reason = str(payload.get("reason", ""))
            if existing:
                item.version += 1
            validated_save(item)
            work_order.scheduled_start_at, work_order.scheduled_end_at = (
                start_at,
                end_at,
            )
            work_order.status, work_order.version = "scheduled", work_order.version + 1
            work_order.save()
        return JsonResponse({"assignment": serialize_assignment(item)}, status=201)
    technicians = list(
        Technician.objects.filter(
            organization=membership.organization, is_active=True
        ).select_related("membership__user")[:100]
    )
    assignments = list(
        Assignment.objects.filter(organization=membership.organization)
        .select_related("technician", "work_order")
        .order_by("start_at")[:200]
    )
    unscheduled = WorkOrder.objects.filter(
        organization=membership.organization, assignments__isnull=True
    ).order_by("-created_at")[:100]
    return JsonResponse(
        {
            "technicians": [
                {
                    **projection(
                        item,
                        (
                            "display_name",
                            "skills_json",
                            "availability_json",
                            "is_active",
                        ),
                    ),
                    "assignments": [
                        serialize_assignment(row)
                        for row in assignments
                        if row.technician_id == item.id
                    ],
                }
                for item in technicians
            ],
            "unscheduled": [
                projection(
                    item,
                    (
                        "title",
                        "priority",
                        "status",
                        "sla_status",
                        "response_due_at",
                        "completion_due_at",
                        "version",
                    ),
                )
                for item in unscheduled
            ],
            "capacity_snapshot": {
                "technician_count": len(technicians),
                "assignment_count": len(assignments),
                "bounded": True,
            },
        }
    )


def serialize_assignment(item):
    return {
        **projection(
            item,
            (
                "work_order_id",
                "technician_id",
                "start_at",
                "end_at",
                "status",
                "reason",
                "version",
            ),
        ),
        "title": item.work_order.title,
        "technician_name": item.technician.display_name,
    }
