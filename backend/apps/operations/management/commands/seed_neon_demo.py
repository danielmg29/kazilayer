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
from apps.operations.models import (
    Assignment,
    ServiceRequest,
    SlaClockEvent,
    SlaPolicy,
    Technician,
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

            for index in range(1, 13):
                priority = ("normal", "high", "critical", "low")[index % 4]
                request, _ = ServiceRequest.objects.update_or_create(
                    organization=organization,
                    idempotency_key=f"neon-demo-request-{index:02d}",
                    defaults={
                        "created_by": users["customer@demo.kazilayer.test"],
                        "location_text": f"Service zone {index:02d}",
                        "urgency": priority,
                        "description": f"Portfolio service request {index:02d} requiring coordinated field response.",
                        "source": "customer_portal",
                        "status": "triaged",
                    },
                )
                order, _ = WorkOrder.objects.update_or_create(
                    organization=organization,
                    service_request=request,
                    title=f"Portfolio work package {index:02d}",
                    defaults={
                        "instructions": f"<h2>Work package {index:02d}</h2><p>Verify the asset, complete the checklist, and attach evidence.</p>",
                        "priority": priority,
                        "status": "new",
                        "sla_policy": policies[priority],
                        "response_due_at": add_business_minutes(
                            now, policies[priority].response_minutes, calendar
                        ),
                        "completion_due_at": add_business_minutes(
                            now, policies[priority].completion_minutes, calendar
                        ),
                        "sla_status": "at_risk" if index % 5 == 0 else "on_track",
                    },
                )
                SlaClockEvent.objects.get_or_create(
                    work_order=order,
                    event_type="started",
                    policy_version=1,
                    defaults={"reason": "Expanded portfolio seed"},
                )
                if index <= 6:
                    start = now + timedelta(hours=index * 2)
                    Assignment.objects.update_or_create(
                        id=uuid.uuid5(
                            uuid.NAMESPACE_URL,
                            f"kazilayer:{organization.slug}:assignment:{index}",
                        ),
                        defaults={
                            "organization": organization,
                            "work_order": order,
                            "technician": technicians[index % len(technicians)],
                            "start_at": start,
                            "end_at": start + timedelta(minutes=90),
                            "status": "scheduled",
                            "assigned_by": users["dispatcher@demo.kazilayer.test"],
                            "reason": "Seeded capacity plan",
                            "version": 1,
                        },
                    )
        self.stdout.write(
            self.style.SUCCESS(
                "Expanded Neon-ready seed complete: base fixtures + 12 work packages, 4 SLA policies, 2 technicians, 6 assignments per tenant, and accessibility preferences."
            )
        )
