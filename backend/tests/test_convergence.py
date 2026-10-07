import uuid

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import Client
from django.utils import timezone

from apps.accounts.models import AppUser, Membership, Organization, RolePolicy
from apps.convergence.models import (
    BulkOperation,
    ContractField,
    ContractVersion,
    RealtimeEvent,
    WebhookEndpoint,
)


@pytest.fixture
def convergence_tenant(db):
    organization = Organization.objects.create(name="Convergence", slug="convergence")
    user = AppUser.objects.create_user(
        "owner@convergence.test", "StrongPassword!2026", display_name="Owner"
    )
    role = RolePolicy.objects.create(
        organization=organization,
        key="owner",
        name="Owner",
        allowed_actions=[
            "contract.list",
            "contract.create",
            "contract.publish",
            "dynamic_form.use",
            "webhook.create",
            "realtime.subscribe",
            "bulk.preview",
        ],
    )
    Membership.objects.create(
        organization=organization,
        user=user,
        role_policy=role,
        status="active",
        joined_at=timezone.now(),
    )
    return organization, user


@pytest.mark.django_db
def test_contract_change_notes_are_rich_text_and_published_schema_is_immutable(
    convergence_tenant,
):
    organization, user = convergence_tenant
    contract = ContractVersion.objects.create(
        organization=organization,
        contract_key="work",
        name="Work",
        entity_type="work_order",
        version_number=1,
        change_notes="<p><strong>Safe</strong><script>bad()</script></p>",
    )
    ContractField.objects.create(
        contract_version=contract,
        field_key="instructions",
        label="Instructions",
        field_type="rich_text",
        presentation="wysiwyg",
    )
    assert "<script" not in contract.change_notes
    assert contract.plain_change_notes == "Safebad()"
    contract.status = "published"
    contract.published_by = user
    contract.published_at = timezone.now()
    contract.save()
    contract.schema_json = {"changed": True}
    with pytest.raises(ValidationError):
        contract.save()


@pytest.mark.django_db
def test_dynamic_form_projects_rich_text_as_wysiwyg(convergence_tenant):
    organization, user = convergence_tenant
    contract = ContractVersion.objects.create(
        organization=organization,
        contract_key="work",
        name="Work",
        entity_type="work_order",
        version_number=1,
    )
    ContractField.objects.create(
        contract_version=contract,
        field_key="instructions",
        label="Instructions",
        field_type="rich_text",
        required=True,
        presentation="wysiwyg",
    )
    contract.status = "published"
    contract.published_by = user
    contract.published_at = timezone.now()
    contract.save()
    client = Client()
    client.force_login(user)
    response = client.get(
        f"/api/v1/organizations/{organization.slug}/convergence/dynamic-forms/work/"
    )
    assert response.status_code == 200
    field = response.json()["form"]["fields"][0]
    assert field["field_type"] == "rich_text"
    assert field["presentation"] == "wysiwyg"


@pytest.mark.django_db
def test_webhook_rejects_private_destination(convergence_tenant):
    organization, _user = convergence_tenant
    endpoint = WebhookEndpoint(
        organization=organization,
        name="Unsafe",
        url="https://127.0.0.1/events",
        event_keys=["work.updated"],
        secret_ciphertext="encrypted",
    )
    with pytest.raises(ValidationError):
        endpoint.full_clean()


@pytest.mark.django_db(transaction=True)
def test_realtime_sequence_is_unique_per_tenant_stream(convergence_tenant):
    organization, _ = convergence_tenant
    values = {
        "organization": organization,
        "stream_key": "tenant:convergence",
        "sequence": 1,
        "event_type": "work.updated",
        "resource_type": "work_order",
        "payload_json": {},
    }
    RealtimeEvent.objects.create(event_id="event-1", **values)
    with pytest.raises(IntegrityError):
        RealtimeEvent.objects.create(event_id="event-2", **values)


@pytest.mark.django_db
def test_bulk_explicit_selection_is_bounded(convergence_tenant):
    organization, user = convergence_tenant
    item = BulkOperation(
        organization=organization,
        requested_by=user,
        resource_type="work_order",
        action_key="export",
        selection_mode="explicit_ids",
        selected_ids_json=[str(uuid.uuid4()) for _ in range(501)],
    )
    with pytest.raises(ValidationError):
        item.full_clean()
