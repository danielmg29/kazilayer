import json

import pytest
from django.test import Client
from django.utils import timezone

from apps.accounts.models import AppUser, Membership, Organization, RolePolicy
from apps.operations.models import Comment, ServiceRequest, UserFeedback, WorkOrder


@pytest.fixture
def operation_tenant(db):
    organization = Organization.objects.create(name="Operations", slug="operations")
    staff = AppUser.objects.create_user(
        "staff@example.test", "StrongPassword!2026", display_name="Staff"
    )
    customer = AppUser.objects.create_user(
        "customer@example.test", "StrongPassword!2026", display_name="Customer"
    )
    staff_role = RolePolicy.objects.create(
        organization=organization,
        key="staff",
        name="Staff",
        allowed_actions=[
            "comment.create",
            "comment.list",
            "request.create",
            "request.list",
            "work_order.list",
            "work_order.create",
            "work_order.transition",
        ],
    )
    customer_role = RolePolicy.objects.create(
        organization=organization,
        key="customer",
        name="Customer",
        allowed_actions=["request.create", "request.list"],
    )
    Membership.objects.create(
        organization=organization,
        user=staff,
        role_policy=staff_role,
        status="active",
        joined_at=timezone.now(),
    )
    Membership.objects.create(
        organization=organization,
        user=customer,
        role_policy=customer_role,
        status="active",
        joined_at=timezone.now(),
    )
    return organization, staff, customer


@pytest.mark.django_db
def test_rich_text_is_sanitized_and_plain_text_is_derived(operation_tenant):
    organization, staff, _ = operation_tenant
    comment = Comment.objects.create(
        organization=organization,
        author_user=staff,
        resource_type="work_order",
        resource_id=WorkOrder._meta.pk.get_default(),
        body="<p>Hello <strong>team</strong><script>alert(1)</script></p>",
        visibility="internal",
    )
    assert "<script" not in comment.body
    assert "Hello teamalert(1)" == comment.plain_text


@pytest.mark.django_db
def test_customer_request_list_is_scoped_to_author(operation_tenant):
    organization, staff, customer = operation_tenant
    ServiceRequest.objects.create(
        organization=organization,
        created_by=staff,
        urgency="normal",
        description="Staff only",
        idempotency_key="staff",
    )
    own = ServiceRequest.objects.create(
        organization=organization,
        created_by=customer,
        urgency="normal",
        description="Customer own",
        idempotency_key="customer",
    )
    client = Client()
    client.force_login(customer)
    response = client.get(
        f"/api/v1/organizations/{organization.slug}/operations/requests/"
    )
    assert response.status_code == 200
    assert [row["id"] for row in response.json()["requests"]] == [str(own.id)]


@pytest.mark.django_db
def test_completion_transition_requires_evidence(operation_tenant):
    organization, staff, _ = operation_tenant
    work_order = WorkOrder.objects.create(
        organization=organization, title="Inspect", status="in_progress"
    )
    client = Client()
    client.force_login(staff)
    response = client.post(
        f"/api/v1/organizations/{organization.slug}/operations/work-orders/{work_order.id}/transition/",
        json.dumps({"to_state": "completed", "evidence_required_met": False}),
        content_type="application/json",
    )
    assert response.status_code == 409
    work_order.refresh_from_db()
    assert work_order.status == "in_progress"


@pytest.mark.django_db
def test_role_without_action_cannot_open_work_orders(operation_tenant):
    organization, _, customer = operation_tenant
    client = Client()
    client.force_login(customer)
    response = client.get(
        f"/api/v1/organizations/{organization.slug}/operations/work-orders/"
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_feedback_creator_can_read_only_their_own_submissions(operation_tenant):
    organization, staff, customer = operation_tenant
    membership = customer.memberships.select_related("role_policy").get(
        organization=organization
    )
    membership.role_policy.allowed_actions = ["feedback.create"]
    membership.role_policy.save(update_fields=["allowed_actions", "updated_at"])
    own = UserFeedback.objects.create(
        organization=organization,
        user=customer,
        route="/customer",
        category="usability",
        message="My feedback",
    )
    UserFeedback.objects.create(
        organization=organization,
        user=staff,
        route="/staff",
        category="bug",
        message="Staff feedback",
    )
    client = Client()
    client.force_login(customer)
    response = client.get(
        f"/api/v1/organizations/{organization.slug}/operations/feedback/"
    )
    assert response.status_code == 200
    assert [row["id"] for row in response.json()["feedback"]] == [str(own.id)]
