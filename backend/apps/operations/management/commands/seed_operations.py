import uuid

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import AppUser, Organization, RolePolicy
from apps.operations.models import (
    AuditEvent,
    Comment,
    ExportJob,
    FileAsset,
    ImportJob,
    Notification,
    NotificationPreference,
    NotificationTemplate,
    SearchDocument,
    ServiceRequest,
    UserFeedback,
    WorkOrder,
    WorkTransition,
)

ROLE_ACTIONS = {
    "owner": [
        "feedback.list",
        "feedback.create",
        "request.list",
        "request.create",
        "comment.list",
        "comment.create",
        "file.list",
        "file.create",
        "search.query",
        "data_job.list",
        "data_job.create",
        "audit.list",
        "work_order.list",
        "work_order.create",
        "work_order.transition",
        "notification.list",
        "notification.preference",
    ],
    "dispatcher": [
        "feedback.create",
        "request.list",
        "request.create",
        "comment.list",
        "comment.create",
        "file.list",
        "file.create",
        "search.query",
        "data_job.list",
        "data_job.create",
        "audit.list",
        "work_order.list",
        "work_order.create",
        "work_order.transition",
        "notification.list",
        "notification.preference",
    ],
    "technician": [
        "feedback.create",
        "comment.list",
        "comment.create",
        "file.list",
        "file.create",
        "search.query",
        "work_order.list",
        "work_order.transition",
        "notification.list",
        "notification.preference",
    ],
    "customer": [
        "feedback.create",
        "request.list",
        "request.create",
        "comment.list",
        "comment.create",
        "file.list",
        "file.create",
        "notification.list",
        "notification.preference",
    ],
    "auditor": [
        "request.list",
        "comment.list",
        "file.list",
        "search.query",
        "data_job.list",
        "audit.list",
        "work_order.list",
        "notification.list",
        "notification.preference",
    ],
}

MODULES = [
    "feedback",
    "requests",
    "comments",
    "files",
    "search",
    "data-jobs",
    "audit",
    "work-orders",
    "notifications",
]


def stable_id(organization, label):
    return uuid.uuid5(uuid.NAMESPACE_URL, f"kazilayer:{organization.slug}:{label}")


class Command(BaseCommand):
    help = "Seed KL-F-22, 07, 13, 14, 16, 19, 20, 08 and 17 demonstration data."

    def handle(self, *args, **options):
        now = timezone.now()
        owner = AppUser.objects.get(email="owner@demo.kazilayer.test")
        dispatcher = AppUser.objects.get(email="dispatcher@demo.kazilayer.test")
        technician = AppUser.objects.get(email="technician@demo.kazilayer.test")
        customer = AppUser.objects.get(email="customer@demo.kazilayer.test")

        NotificationTemplate.objects.update_or_create(
            event_key="work_order.updated",
            channel="in_app",
            defaults={
                "body": "<p>Work order <strong>{{reference}}</strong> moved to {{status}}.</p>"
            },
        )

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
                            "feedback",
                            "comment",
                            "file",
                            "search",
                            "data_job",
                            "audit",
                            "notification",
                        ]
                    )
                )
                role.save(
                    update_fields=["allowed_actions", "resource_scope", "updated_at"]
                )

            service_request, _ = ServiceRequest.objects.update_or_create(
                organization=organization,
                idempotency_key="seed-cold-room-variance",
                defaults={
                    "created_by": customer,
                    "location_text": "Sarit Centre - Cold room B",
                    "urgency": "high",
                    "description": "Cold room temperature is above the contracted range.",
                    "source": "customer_portal",
                    "status": "triaged",
                },
            )
            work_order, created = WorkOrder.objects.update_or_create(
                organization=organization,
                title="Stabilise cold room temperature",
                defaults={
                    "service_request": service_request,
                    "instructions": "<h2>Safety check</h2><ul><li>Confirm isolation controls.</li><li>Record inlet and outlet temperature.</li></ul>",
                    "priority": "high",
                    "status": "scheduled",
                    "scheduled_start_at": now,
                },
            )
            if created:
                WorkTransition.objects.create(
                    work_order=work_order,
                    to_state="new",
                    actor_user=dispatcher,
                    evidence_required_met=True,
                )
                WorkTransition.objects.create(
                    work_order=work_order,
                    from_state="new",
                    to_state="scheduled",
                    actor_user=dispatcher,
                    reason="Matched to refrigeration technician",
                    evidence_required_met=True,
                )

            FileAsset.objects.update_or_create(
                object_key=f"{organization.id}/seed/cold-room-reading.csv",
                defaults={
                    "organization": organization,
                    "uploaded_by": technician,
                    "resource_type": "work_order",
                    "resource_id": work_order.id,
                    "original_name": "cold-room-reading.csv",
                    "mime_type": "text/csv",
                    "size_bytes": 2480,
                    "sha256": "0" * 64,
                    "upload_status": "ready",
                    "scan_status": "clean",
                    "visibility": "customer_visible",
                    "ready_at": now,
                },
            )
            source_file = FileAsset.objects.get(
                object_key=f"{organization.id}/seed/cold-room-reading.csv"
            )
            UserFeedback.objects.update_or_create(
                id=stable_id(organization, "feedback"),
                defaults={
                    "organization": organization,
                    "user": dispatcher,
                    "route": f"/{organization.slug}/work-orders",
                    "role_key": "dispatcher",
                    "viewport_width": 1440,
                    "viewport_height": 900,
                    "category": "usability",
                    "message": "Keep the transition controls visible while reviewing evidence.",
                    "consent_context_capture": True,
                    "triage_status": "reviewing",
                },
            )
            Comment.objects.update_or_create(
                id=stable_id(organization, "comment"),
                defaults={
                    "organization": organization,
                    "resource_type": "work_order",
                    "resource_id": work_order.id,
                    "author_user": dispatcher,
                    "body": "<p><strong>Technician:</strong> please attach the final temperature reading before completion.</p>",
                    "visibility": "internal",
                },
            )
            SearchDocument.objects.update_or_create(
                organization=organization,
                resource_type="work_order",
                resource_id=work_order.id,
                defaults={
                    "title": work_order.title,
                    "body_text": work_order.plain_instructions,
                    "search_vector": f"{work_order.title} {work_order.plain_instructions}",
                    "rank_boost": 1.25,
                },
            )
            ImportJob.objects.update_or_create(
                id=stable_id(organization, "import"),
                defaults={
                    "organization": organization,
                    "requested_by": owner,
                    "resource_type": "service_request",
                    "source_file": source_file,
                    "status": "completed",
                    "total_rows": 12,
                    "valid_rows": 11,
                    "invalid_rows": 1,
                    "completed_at": now,
                },
            )
            ExportJob.objects.update_or_create(
                id=stable_id(organization, "export"),
                defaults={
                    "organization": organization,
                    "requested_by": owner,
                    "resource_type": "work_order",
                    "filters_json": {"status": ["scheduled", "in_progress"]},
                    "columns_json": [
                        "title",
                        "priority",
                        "status",
                        "scheduled_start_at",
                    ],
                    "manifest_json": {
                        "generated_at": now.isoformat(),
                        "row_count": 1,
                        "contract": "v1",
                    },
                    "status": "completed",
                },
            )
            AuditEvent.objects.get_or_create(
                id=stable_id(organization, "audit"),
                defaults={
                    "organization": organization,
                    "actor_user": dispatcher,
                    "event_type": "work_order.scheduled",
                    "resource_type": "work_order",
                    "resource_id": work_order.id,
                    "before_summary": {"status": "new"},
                    "after_summary": {"status": "scheduled"},
                    "reason": "Matched to refrigeration technician",
                },
            )
            for user in (owner, dispatcher, technician, customer):
                NotificationPreference.objects.update_or_create(
                    user=user,
                    event_key="work_order.updated",
                    defaults={
                        "in_app": True,
                        "email": user in (owner, customer),
                        "quiet_hours_json": {
                            "start": "22:00",
                            "end": "06:00",
                            "timezone": "Africa/Nairobi",
                        },
                    },
                )
                Notification.objects.update_or_create(
                    dedupe_key=f"seed:{organization.slug}:work-order:{work_order.id}:{user.id}:in_app",
                    defaults={
                        "organization": organization,
                        "recipient_user": user,
                        "event_id": f"work-order:{work_order.id}:scheduled",
                        "channel": "in_app",
                        "status": "sent",
                        "payload_json": {
                            "title": work_order.title,
                            "status": work_order.status,
                            "href": f"/{organization.slug}/work-orders",
                        },
                        "sent_at": now,
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded nine operational feature slices for every active tenant."
            )
        )
