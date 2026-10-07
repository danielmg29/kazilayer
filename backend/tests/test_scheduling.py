from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import (
    AccessibilityPreference,
    AppUser,
    Membership,
    Organization,
    RolePolicy,
)
from apps.operations.models import Assignment, SlaPolicy, Technician, WorkOrder
from apps.operations.scheduling import add_business_minutes


@pytest.mark.django_db
def test_business_minutes_skip_weekend():
    start = timezone.datetime(2026, 10, 9, 16, 0, tzinfo=timezone.UTC)  # Friday
    result = add_business_minutes(
        start,
        120,
        {
            "timezone": "UTC",
            "workdays": [0, 1, 2, 3, 4],
            "start": "08:00",
            "end": "17:00",
        },
    )
    assert result == timezone.datetime(2026, 10, 12, 9, 0, tzinfo=timezone.UTC)


@pytest.mark.django_db
def test_assignment_rejects_cross_tenant_technician():
    user = AppUser.objects.create_user(
        email="schedule@test.local", password="test-pass", display_name="Schedule User"
    )
    org_a = Organization.objects.create(name="A", slug="schedule-a")
    org_b = Organization.objects.create(name="B", slug="schedule-b")
    role = RolePolicy.objects.create(
        organization=org_a, name="Tech", key="tech", allowed_actions=[]
    )
    membership = Membership.objects.create(
        organization=org_a, user=user, role_policy=role, status="active"
    )
    technician = Technician.objects.create(
        organization=org_a, membership=membership, display_name="Tech"
    )
    order = WorkOrder.objects.create(
        organization=org_b, title="Other tenant", priority="normal"
    )
    assignment = Assignment(
        organization=org_b,
        technician=technician,
        work_order=order,
        start_at=timezone.now(),
        end_at=timezone.now() + timedelta(hours=1),
        assigned_by=user,
    )
    with pytest.raises(ValidationError):
        assignment.full_clean()


@pytest.mark.django_db
def test_sla_policy_and_accessibility_are_versioned_and_user_owned():
    user = AppUser.objects.create_user(
        email="preference@test.local",
        password="test-pass",
        display_name="Preference User",
    )
    org = Organization.objects.create(name="Preference Org", slug="preference-org")
    policy = SlaPolicy.objects.create(
        organization=org,
        name="High",
        priority_key="high",
        response_minutes=30,
        completion_minutes=240,
        business_calendar_json={},
        effective_from=timezone.now(),
        version=2,
    )
    preference = AccessibilityPreference.objects.create(
        user=user, reduced_motion=True, density="compact"
    )
    assert policy.version == 2
    assert preference.user_id == user.id and preference.reduced_motion
