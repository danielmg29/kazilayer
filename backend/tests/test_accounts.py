import json

import pytest
from django.test import Client
from django.utils import timezone

from apps.accounts.models import (
    AppUser,
    Membership,
    Organization,
    RolePolicy,
    SavedView,
)


@pytest.fixture
def tenant_data(db):
    user = AppUser.objects.create_user(
        "owner@example.test",
        "StrongPassword!2026",
        display_name="Owner",
        email_verified_at=timezone.now(),
    )
    first = Organization.objects.create(
        name="First", slug="first", enabled_modules=["members", "saved-views"]
    )
    second = Organization.objects.create(name="Second", slug="second")
    role = RolePolicy.objects.create(
        organization=first,
        name="Owner",
        key="owner",
        resource_scope=["organization", "saved_view"],
        allowed_actions=["organization.view", "saved_view.list", "saved_view.create"],
    )
    Membership.objects.create(
        organization=first,
        user=user,
        role_policy=role,
        status="active",
        joined_at=timezone.now(),
    )
    return user, first, second


@pytest.mark.django_db
def test_login_and_me_return_membership_projection(tenant_data):
    user, first, _ = tenant_data
    client = Client(enforce_csrf_checks=True)
    csrf = client.get("/api/v1/csrf/").cookies["csrftoken"].value
    response = client.post(
        "/api/v1/auth/login/",
        json.dumps({"email": user.email, "password": "StrongPassword!2026"}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf,
        HTTP_ORIGIN="http://localhost:3000",
    )
    assert response.status_code == 200
    projection = client.get("/api/v1/me/").json()
    assert projection["memberships"][0]["organization"]["slug"] == first.slug
    assert "organization.view" in projection["memberships"][0]["allowed_actions"]


@pytest.mark.django_db
def test_cross_tenant_access_returns_no_data(tenant_data):
    user, _, second = tenant_data
    client = Client()
    client.force_login(user)
    response = client.get(f"/api/v1/organizations/{second.slug}/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_saved_view_rejects_unknown_contract_field(tenant_data):
    user, first, _ = tenant_data
    client = Client()
    client.force_login(user)
    response = client.post(
        f"/api/v1/organizations/{first.slug}/saved-views/",
        json.dumps(
            {
                "module_key": "members",
                "name": "Unsafe",
                "filters": [{"field": "password", "operator": "eq", "value": "x"}],
                "sorts": [],
                "visible_columns": [],
                "dashboard_selection": [],
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert not SavedView.objects.exists()
