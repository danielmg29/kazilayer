from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import (
    AppUser,
    Membership,
    Organization,
    RolePolicy,
    SavedView,
)

DEMO_PASSWORD = "KaziLayerDemo!2026"

ROLE_DEFINITIONS = {
    "owner": {
        "name": "Organisation owner",
        "description": "Full tenant administration, identity, policy, settings and operational access.",
        "resources": [
            "organization",
            "membership",
            "role_policy",
            "saved_view",
            "request",
            "work_order",
            "dispatch",
        ],
        "actions": [
            "organization.view",
            "organization.update",
            "membership.list",
            "membership.invite",
            "membership.update",
            "role_policy.list",
            "role_policy.create",
            "role_policy.update",
            "saved_view.list",
            "saved_view.create",
            "saved_view.update",
            "saved_view.delete",
            "request.list",
            "work_order.list",
            "dispatch.view",
        ],
        "priority": 10,
    },
    "dispatcher": {
        "name": "Dispatcher",
        "description": "Coordinates requests, work orders, technicians and saved operational views.",
        "resources": [
            "organization",
            "membership",
            "saved_view",
            "request",
            "work_order",
            "dispatch",
        ],
        "actions": [
            "organization.view",
            "membership.list",
            "role_policy.list",
            "saved_view.list",
            "saved_view.create",
            "saved_view.update",
            "saved_view.delete",
            "request.list",
            "work_order.list",
            "dispatch.view",
        ],
        "priority": 20,
    },
    "technician": {
        "name": "Technician",
        "description": "Views assigned work and maintains personal operational views.",
        "resources": ["organization", "saved_view", "work_order"],
        "actions": [
            "organization.view",
            "saved_view.list",
            "saved_view.create",
            "saved_view.update",
            "saved_view.delete",
            "work_order.list",
        ],
        "priority": 30,
    },
    "customer": {
        "name": "Customer contact",
        "description": "Views permitted customer requests and personal saved views.",
        "resources": ["organization", "saved_view", "request"],
        "actions": [
            "organization.view",
            "saved_view.list",
            "saved_view.create",
            "saved_view.update",
            "saved_view.delete",
            "request.list",
        ],
        "priority": 40,
    },
    "auditor": {
        "name": "Auditor",
        "description": "Read-only tenant, identity and operational review access.",
        "resources": [
            "organization",
            "membership",
            "role_policy",
            "saved_view",
            "request",
            "work_order",
        ],
        "actions": [
            "organization.view",
            "membership.list",
            "role_policy.list",
            "saved_view.list",
            "request.list",
            "work_order.list",
        ],
        "priority": 50,
    },
}

USERS = [
    ("owner@demo.kazilayer.test", "Tuki Gichovi", "owner"),
    ("dispatcher@demo.kazilayer.test", "Amina Kamau", "dispatcher"),
    ("technician@demo.kazilayer.test", "Brian Mwangi", "technician"),
    ("customer@demo.kazilayer.test", "Linet Wanjiku", "customer"),
    ("auditor@demo.kazilayer.test", "Omar Hassan", "auditor"),
]


class Command(BaseCommand):
    help = (
        "Seed deterministic KL-F-01, KL-F-02, KL-F-03 and KL-F-11 demonstration data."
    )

    def handle(self, *args, **options):
        now = timezone.now()
        organizations = [
            Organization.objects.update_or_create(
                slug="meridian-field-services",
                defaults={
                    "name": "Meridian Field Services",
                    "status": "active",
                    "timezone": "Africa/Nairobi",
                    "locale": "en-KE",
                    "enabled_modules": [
                        "overview",
                        "members",
                        "roles",
                        "saved-views",
                        "requests",
                        "work-orders",
                        "dispatch",
                        "settings",
                    ],
                    "settings_json": {
                        "week_starts_on": "monday",
                        "date_format": "DD MMM YYYY",
                    },
                },
            )[0],
            Organization.objects.update_or_create(
                slug="rift-valley-facilities",
                defaults={
                    "name": "Rift Valley Facilities",
                    "status": "active",
                    "timezone": "Africa/Nairobi",
                    "locale": "en-KE",
                    "enabled_modules": [
                        "overview",
                        "members",
                        "roles",
                        "saved-views",
                        "requests",
                        "work-orders",
                        "settings",
                    ],
                    "settings_json": {
                        "week_starts_on": "monday",
                        "date_format": "DD/MM/YYYY",
                    },
                },
            )[0],
        ]
        for organization in organizations:
            roles = {}
            for key, definition in ROLE_DEFINITIONS.items():
                roles[key] = RolePolicy.objects.update_or_create(
                    organization=organization,
                    key=key,
                    defaults={
                        "name": definition["name"],
                        "description": definition["description"],
                        "resource_scope": definition["resources"],
                        "allowed_actions": definition["actions"],
                        "conditions_json": {"tenant_scoped": True},
                        "priority": definition["priority"],
                        "is_active": True,
                    },
                )[0]
            for email, display_name, role_key in USERS:
                user, created = AppUser.objects.get_or_create(
                    email=email,
                    defaults={
                        "display_name": display_name,
                        "email_verified_at": now,
                        "is_active": True,
                    },
                )
                if created:
                    user.set_password(DEMO_PASSWORD)
                    user.save(update_fields=["password"])
                Membership.objects.update_or_create(
                    organization=organization,
                    user=user,
                    defaults={
                        "role_policy": roles[role_key],
                        "status": "active",
                        "joined_at": now,
                    },
                )
            owner = AppUser.objects.get(email="owner@demo.kazilayer.test")
            dispatcher = AppUser.objects.get(email="dispatcher@demo.kazilayer.test")
            SavedView.objects.update_or_create(
                organization=organization,
                user=dispatcher,
                module_key="work-orders",
                name="SLA risk queue",
                defaults={
                    "filters_json": [
                        {
                            "field": "sla_state",
                            "operator": "in",
                            "value": ["at_risk", "breached"],
                        }
                    ],
                    "sorts_json": [{"field": "scheduled_at", "direction": "asc"}],
                    "visible_columns": [
                        "reference",
                        "title",
                        "status",
                        "technician",
                        "scheduled_at",
                        "sla_state",
                    ],
                    "density": "compact",
                    "dashboard_selection": [],
                    "is_default": True,
                },
            )
            SavedView.objects.update_or_create(
                organization=organization,
                user=owner,
                module_key="members",
                name="Active team",
                defaults={
                    "filters_json": [
                        {"field": "status", "operator": "eq", "value": "active"}
                    ],
                    "sorts_json": [{"field": "display_name", "direction": "asc"}],
                    "visible_columns": [
                        "display_name",
                        "email",
                        "role",
                        "status",
                        "joined_at",
                    ],
                    "density": "comfortable",
                    "dashboard_selection": [],
                    "is_default": True,
                },
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(organizations)} organizations, {len(USERS)} accounts, {len(organizations) * len(ROLE_DEFINITIONS)} role policies and {len(organizations) * 2} saved views."
            )
        )
        self.stdout.write(f"Demo password for every seeded account: {DEMO_PASSWORD}")
