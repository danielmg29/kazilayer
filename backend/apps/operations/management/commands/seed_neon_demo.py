import uuid
from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import (
    AccessibilityPreference,
    AppUser,
    Membership,
    Organization,
    RolePolicy,
)
from apps.convergence.models import BulkOperation, RealtimeEvent
from apps.operations.models import (
    Assignment,
    AuditEvent,
    Comment,
    Notification,
    SearchDocument,
    ServiceRequest,
    SlaClockEvent,
    SlaPolicy,
    Technician,
    UserFeedback,
    WorkOrder,
)
from apps.operations.scheduling import add_business_minutes

ROLE_ACTIONS = {
    "owner": [
        "sla.list",
        "sla.manage",
        "sla.apply",
        "dispatch.view",
        "dispatch.assign",
    ],
    "dispatcher": ["sla.list", "sla.apply", "dispatch.view", "dispatch.assign"],
    "technician": ["sla.list", "dispatch.view"],
    "auditor": ["sla.list", "dispatch.view"],
}


class Command(BaseCommand):
    help = "Idempotently create the expanded PostgreSQL/Neon-ready portfolio dataset."

    def handle(self, *args, **options):
        call_command("seed_kazilayer")
        call_command("seed_operations")
        call_command("seed_convergence")
        now = timezone.now().replace(second=0, microsecond=0)
        users = {user.email: user for user in AppUser.objects.all()}
        for user in users.values():
            AccessibilityPreference.objects.update_or_create(
                user=user,
                defaults={
                    "reduced_motion": "auditor" in user.email,
                    "density": "compact"
                    if "dispatcher" in user.email
                    else "comfortable",
                    "contrast_mode": "high" if "technician" in user.email else "system",
                    "input_mode": "keyboard_first"
                    if "dispatcher" in user.email
                    else "auto",
                    "large_text": "customer" in user.email,
                },
            )
        for organization in Organization.objects.filter(status="active"):
            organization.enabled_modules = list(
                dict.fromkeys(
                    [*organization.enabled_modules, "sla", "dispatch", "accessibility"]
                )
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
                        [*role.resource_scope, "sla", "technician", "assignment"]
                    )
                )
                role.save(
                    update_fields=["allowed_actions", "resource_scope", "updated_at"]
                )

            calendar = {
                "timezone": organization.timezone,
                "workdays": [0, 1, 2, 3, 4],
                "start": "08:00",
                "end": "17:00",
                "holidays": [],
            }
            policies = {}
            for priority, response, completion in (
                ("low", 240, 1440),
                ("normal", 120, 960),
                ("high", 45, 360),
                ("critical", 15, 120),
            ):
                policies[priority], _ = SlaPolicy.objects.update_or_create(
                    organization=organization,
                    priority_key=priority,
                    version=1,
                    defaults={
                        "name": f"{priority.title()} response policy",
                        "response_minutes": response,
                        "completion_minutes": completion,
                        "business_calendar_json": calendar,
                        "pause_state_keys": ["blocked"],
                        "effective_from": now - timedelta(days=365),
                    },
                )

            technicians = []
            for email in (
                "technician@demo.kazilayer.test",
                "dispatcher@demo.kazilayer.test",
            ):
                member = Membership.objects.get(
                    organization=organization, user=users[email]
                )
                profile, _ = Technician.objects.update_or_create(
                    organization=organization,
                    membership=member,
                    defaults={
                        "display_name": users[email].display_name,
                        "skills_json": ["HVAC", "Electrical"]
                        if "technician" in email
                        else ["Inspection"],
                        "availability_json": calendar,
                        "is_active": True,
                    },
                )
                technicians.append(profile)

            timeline_start = now - timedelta(days=182)
            timeline_orders = []
            locations = (
                "Westlands commercial tower",
                "Kilimani medical centre",
                "Industrial Area warehouse",
                "Karen retail campus",
                "Upper Hill office block",
                "Ruiru distribution hub",
                "Thika Road service centre",
                "Mombasa Road cold store",
            )
            work_types = (
                "Preventive HVAC inspection",
                "Electrical panel assessment",
                "Cold-room temperature variance",
                "Water pressure investigation",
                "Generator load-bank test",
                "Fire-alarm device inspection",
                "Access-control reader repair",
                "Lighting circuit maintenance",
            )
            for index in range(1, 105):
                occurred_at = timeline_start + timedelta(
                    days=(index - 1) * 1.75,
                    hours=7 + (index % 9),
                )
                priority = ("normal", "high", "critical", "low")[index % 4]
                final_status = (
                    "completed"
                    if index <= 84
                    else ("in_progress" if index <= 94 else "new")
                )
                request, _ = ServiceRequest.objects.update_or_create(
                    organization=organization,
                    idempotency_key=f"six-month-request-{index:03d}",
                    defaults={
                        "created_by": users["customer@demo.kazilayer.test"],
                        "location_text": locations[index % len(locations)],
                        "urgency": priority,
                        "description": f"{work_types[index % len(work_types)]} reported during week {(index - 1) // 4 + 1} of the six-month operating simulation.",
                        "source": ("customer_portal", "staff", "integration", "import")[
                            index % 4
                        ],
                        "status": "converted" if final_status != "new" else "triaged",
                    },
                )
                order, _ = WorkOrder.objects.update_or_create(
                    organization=organization,
                    service_request=request,
                    title=f"{work_types[index % len(work_types)]} · {index:03d}",
                    defaults={
                        "instructions": f"<h2>Week {(index - 1) // 4 + 1} work package</h2><p>Verify the asset, complete the safety checklist, record readings and attach evidence before close-out.</p>",
                        "priority": priority,
                        "status": final_status,
                        "sla_policy": policies[priority],
                        "response_due_at": add_business_minutes(
                            occurred_at, policies[priority].response_minutes, calendar
                        ),
                        "completion_due_at": add_business_minutes(
                            occurred_at, policies[priority].completion_minutes, calendar
                        ),
                        "sla_status": "completed"
                        if final_status == "completed"
                        else ("at_risk" if index % 5 == 0 else "on_track"),
                        "completion_summary": "<p>Inspection complete, readings verified and site contact briefed.</p>"
                        if final_status == "completed"
                        else "",
                    },
                )
                ServiceRequest.objects.filter(id=request.id).update(
                    created_at=occurred_at
                )
                WorkOrder.objects.filter(id=order.id).update(
                    created_at=occurred_at,
                    updated_at=occurred_at + timedelta(hours=3),
                )
                SlaClockEvent.objects.get_or_create(
                    work_order=order,
                    event_type="started",
                    policy_version=1,
                    defaults={
                        "reason": "Six-month operating simulation",
                        "occurred_at": occurred_at,
                    },
                )
                start = occurred_at + timedelta(hours=2)
                assignment_status = (
                    "completed" if final_status == "completed" else "scheduled"
                )
                Assignment.objects.update_or_create(
                    id=uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"kazilayer:{organization.slug}:six-month-assignment:{index}",
                    ),
                    defaults={
                        "organization": organization,
                        "work_order": order,
                        "technician": technicians[index % len(technicians)],
                        "start_at": start,
                        "end_at": start + timedelta(minutes=60 + (index % 3) * 30),
                        "status": assignment_status,
                        "assigned_by": users["dispatcher@demo.kazilayer.test"],
                        "reason": "Six-month capacity plan",
                        "version": 1,
                    },
                )
                Comment.objects.update_or_create(
                    id=uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"kazilayer:{organization.slug}:six-month-comment:{index}",
                    ),
                    defaults={
                        "organization": organization,
                        "resource_type": "work_order",
                        "resource_id": order.id,
                        "author_user": users["dispatcher@demo.kazilayer.test"],
                        "body": f"<p>Week {(index - 1) // 4 + 1}: dispatcher reviewed priority, access window and technician capacity.</p>",
                        "visibility": "internal",
                    },
                )
                SearchDocument.objects.update_or_create(
                    organization=organization,
                    resource_type="work_order",
                    resource_id=order.id,
                    defaults={
                        "title": order.title,
                        "body_text": f"{request.location_text} {order.plain_instructions}",
                        "search_vector": f"{order.title} {request.location_text}",
                        "rank_boost": 1.5 if priority in {"high", "critical"} else 1,
                    },
                )
                AuditEvent.objects.get_or_create(
                    id=uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"kazilayer:{organization.slug}:six-month-audit:{index}",
                    ),
                    defaults={
                        "organization": organization,
                        "actor_user": users["dispatcher@demo.kazilayer.test"],
                        "event_type": "work_order.timeline_seeded",
                        "resource_type": "work_order",
                        "resource_id": order.id,
                        "after_summary": {"status": final_status, "priority": priority},
                        "reason": "Six-month portfolio simulation",
                    },
                )
                Notification.objects.update_or_create(
                    dedupe_key=f"{organization.slug}:six-month-work-order:{index}",
                    defaults={
                        "organization": organization,
                        "recipient_user": users["dispatcher@demo.kazilayer.test"],
                        "event_id": f"six-month-{organization.slug}-{index}",
                        "channel": "in_app",
                        "status": "read" if index <= 84 else "sent",
                        "payload_json": {
                            "title": order.title,
                            "status": final_status,
                            "priority": priority,
                        },
                        "sent_at": occurred_at,
                    },
                )
                RealtimeEvent.objects.update_or_create(
                    event_id=f"six-month-{organization.slug}-{index}",
                    defaults={
                        "organization": organization,
                        "stream_key": f"tenant:{organization.slug}",
                        "sequence": 1000 + index,
                        "event_type": "work_order.updated",
                        "resource_type": "work_order",
                        "resource_id": order.id,
                        "version": order.version,
                        "payload_json": {"status": final_status, "priority": priority},
                    },
                )
                if index % 8 == 0:
                    UserFeedback.objects.update_or_create(
                        id=uuid.uuid5(
                            uuid.NAMESPACE_URL,
                            f"kazilayer:{organization.slug}:six-month-feedback:{index}",
                        ),
                        defaults={
                            "organization": organization,
                            "user": users["dispatcher@demo.kazilayer.test"],
                            "route": f"/{organization.slug}/dispatch",
                            "role_key": "dispatcher",
                            "viewport_width": 1440,
                            "viewport_height": 900,
                            "category": ("usability", "performance", "content")[
                                index % 3
                            ],
                            "message": f"Week {(index - 1) // 4 + 1} dispatch review: capacity lanes remained clear and actionable.",
                            "consent_context_capture": True,
                            "triage_status": "closed" if index <= 80 else "reviewing",
                        },
                    )
                timeline_orders.append(order)

            for month in range(1, 7):
                selected = timeline_orders[(month - 1) * 16 : (month - 1) * 16 + 12]
                BulkOperation.objects.update_or_create(
                    id=uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"kazilayer:{organization.slug}:monthly-export:{month}",
                    ),
                    defaults={
                        "organization": organization,
                        "requested_by": users["owner@demo.kazilayer.test"],
                        "resource_type": "work_order",
                        "action_key": "export",
                        "selection_mode": "explicit_ids",
                        "selected_ids_json": [str(item.id) for item in selected],
                        "action_params_json": {
                            "format": "csv",
                            "period": f"month-{month}",
                        },
                        "preview_count": len(selected),
                        "status": "completed",
                        "total_count": len(selected),
                        "processed_count": len(selected),
                        "success_count": len(selected),
                        "failure_count": 0,
                        "started_at": timeline_start + timedelta(days=month * 30),
                        "completed_at": timeline_start
                        + timedelta(days=month * 30, minutes=2),
                    },
                )
        self.stdout.write(
            self.style.SUCCESS(
                "Expanded Neon-ready seed complete: base fixtures + 104 six-month work packages, assignments, collaboration, audit, notifications, realtime events and six monthly bulk exports per tenant."
            )
        )
