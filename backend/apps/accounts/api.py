import json
from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from core.contract.registry import validate_saved_view_definition

from .models import (
    AccessibilityPreference,
    AccountSession,
    AppUser,
    Membership,
    MfaFactor,
    PasswordResetToken,
    RolePolicy,
    SavedView,
)
from .policies import require_action, resolve_membership
from .security import (
    decrypt_secret,
    encrypt_secret,
    generate_token,
    generate_totp_secret,
    hash_token,
    provisioning_uri,
    verify_totp,
)


def body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body)
    except json.JSONDecodeError as exc:
        raise ValueError("Request body must be valid JSON") from exc


def error(message, status=400, code="INVALID_REQUEST"):
    return JsonResponse({"error": {"code": code, "message": message}}, status=status)


def image_url(request, field):
    return request.build_absolute_uri(field.url) if field else None


def serialize_user(request, user):
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "avatar_url": image_url(request, user.avatar_image),
        "avatar_alt_text": user.avatar_alt_text,
        "email_verified_at": user.email_verified_at.isoformat()
        if user.email_verified_at
        else None,
    }


def serialize_org(request, organization):
    return {
        "id": str(organization.id),
        "name": organization.name,
        "slug": organization.slug,
        "status": organization.status,
        "timezone": organization.timezone,
        "locale": organization.locale,
        "settings": organization.settings_json,
        "enabled_modules": organization.enabled_modules,
        "logo_url": image_url(request, organization.logo_image),
        "logo_alt_text": organization.logo_alt_text,
    }


def membership_or_error(request, slug, action=None):
    membership = resolve_membership(request.user, slug)
    if membership is None:
        return None, error("Organization not found", 404, "NOT_FOUND")
    try:
        if action:
            require_action(membership, action)
    except PermissionError as exc:
        return None, error(str(exc), 403, "FORBIDDEN")
    return membership, None


@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({"csrf": "ready"})


@require_http_methods(["POST"])
def login_view(request):
    try:
        payload = body(request)
    except ValueError as exc:
        return error(str(exc))
    user = authenticate(
        request,
        username=str(payload.get("email", "")).lower(),
        password=payload.get("password"),
    )
    if user is None:
        return error("Email or password is incorrect", 401, "INVALID_CREDENTIALS")
    enabled_factor = user.mfa_factors.filter(enabled_at__isnull=False).first()
    if enabled_factor and not verify_totp(
        decrypt_secret(enabled_factor.secret_encrypted), payload.get("mfa_code", "")
    ):
        return error("A valid authenticator code is required", 401, "MFA_REQUIRED")
    login(request, user)
    request.session.save()
    AccountSession.objects.update_or_create(
        session_key=request.session.session_key,
        defaults={
            "user": user,
            "token_hash": hash_token(request.session.session_key),
            "device_label": str(payload.get("device_label", "Web browser"))[:160],
            "last_seen_at": timezone.now(),
            "expires_at": timezone.now()
            + timedelta(seconds=request.session.get_expiry_age()),
            "revoked_at": None,
        },
    )
    return JsonResponse({"user": serialize_user(request, user)})


@require_http_methods(["POST"])
def logout_view(request):
    if request.user.is_authenticated and request.session.session_key:
        AccountSession.objects.filter(session_key=request.session.session_key).update(
            revoked_at=timezone.now()
        )
    logout(request)
    return JsonResponse({"ok": True})


@require_http_methods(["GET"])
def me(request):
    if not request.user.is_authenticated:
        return error("Authentication required", 401, "UNAUTHENTICATED")
    memberships = Membership.objects.select_related(
        "organization", "role_policy"
    ).filter(user=request.user, status="active", organization__status="active")
    return JsonResponse(
        {
            "user": serialize_user(request, request.user),
            "memberships": [
                {
                    "organization": serialize_org(request, item.organization),
                    "role": {
                        "key": item.role_policy.key,
                        "name": item.role_policy.name,
                    },
                    "allowed_actions": item.role_policy.allowed_actions,
                }
                for item in memberships
            ],
        }
    )


@require_http_methods(["PATCH", "POST"])
def profile(request):
    if not request.user.is_authenticated:
        return error("Authentication required", 401, "UNAUTHENTICATED")
    user = request.user
    payload = (
        request.POST
        if request.content_type and request.content_type.startswith("multipart/")
        else body(request)
    )
    if "display_name" in payload:
        user.display_name = str(payload["display_name"]).strip()[:160]
    if "avatar_alt_text" in payload:
        user.avatar_alt_text = str(payload["avatar_alt_text"]).strip()[:180]
    avatar = request.FILES.get("avatar_image")
    if avatar:
        if avatar.size > 5 * 1024 * 1024:
            return error("Avatar images must be 5 MB or smaller")
        user.avatar_image = avatar
    user.full_clean(exclude=["password", "last_login"])
    user.save()
    return JsonResponse({"user": serialize_user(request, user)})


@require_http_methods(["POST"])
def password_reset_request(request):
    payload = body(request)
    user = AppUser.objects.filter(
        email=str(payload.get("email", "")).lower(), is_active=True
    ).first()
    if user:
        raw_token = generate_token()
        PasswordResetToken.objects.create(
            user=user,
            token_hash=hash_token(raw_token),
            expires_at=timezone.now() + timedelta(minutes=30),
        )
        send_mail(
            "Reset your KaziLayer password",
            f"Your one-time reset token is: {raw_token}",
            None,
            [user.email],
        )
    return JsonResponse(
        {
            "ok": True,
            "message": "If the account exists, reset instructions have been sent.",
        }
    )


@require_http_methods(["POST"])
def password_reset_confirm(request):
    payload = body(request)
    record = (
        PasswordResetToken.objects.select_related("user")
        .filter(
            token_hash=hash_token(str(payload.get("token", ""))),
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .first()
    )
    if record is None:
        return error("Reset token is invalid or expired", 400, "TOKEN_INVALID")
    password = str(payload.get("password", ""))
    try:
        validate_password(password, record.user)
    except ValidationError as exc:
        return error(" ".join(exc.messages), 400, "PASSWORD_INVALID")
    record.user.set_password(password)
    record.user.full_clean(exclude=["password", "last_login"])
    with transaction.atomic():
        record.user.save(update_fields=["password", "updated_at"])
        record.used_at = timezone.now()
        record.save(update_fields=["used_at"])
        AccountSession.objects.filter(user=record.user, revoked_at__isnull=True).update(
            revoked_at=timezone.now()
        )
    return JsonResponse({"ok": True})


@require_http_methods(["POST"])
def mfa_setup(request):
    if not request.user.is_authenticated:
        return error("Authentication required", 401, "UNAUTHENTICATED")
    secret = generate_totp_secret()
    factor, _ = MfaFactor.objects.update_or_create(
        user=request.user,
        factor_type="totp",
        defaults={"secret_encrypted": encrypt_secret(secret), "enabled_at": None},
    )
    return JsonResponse(
        {
            "factor_id": str(factor.id),
            "secret": secret,
            "provisioning_uri": provisioning_uri(secret, request.user.email),
        }
    )


@require_http_methods(["POST"])
def mfa_confirm(request):
    if not request.user.is_authenticated:
        return error("Authentication required", 401, "UNAUTHENTICATED")
    factor = request.user.mfa_factors.filter(
        factor_type="totp", enabled_at__isnull=True
    ).first()
    if factor is None or not verify_totp(
        decrypt_secret(factor.secret_encrypted), body(request).get("code", "")
    ):
        return error("Authenticator code is invalid", 400, "MFA_CODE_INVALID")
    factor.enabled_at = timezone.now()
    factor.save(update_fields=["enabled_at"])
    return JsonResponse({"ok": True})


@require_http_methods(["GET"])
def sessions(request):
    if not request.user.is_authenticated:
        return error("Authentication required", 401, "UNAUTHENTICATED")
    rows = request.user.account_sessions.order_by("-last_seen_at")[:20]
    return JsonResponse(
        {
            "sessions": [
                {
                    "id": str(item.id),
                    "device_label": item.device_label,
                    "created_at": item.created_at.isoformat(),
                    "last_seen_at": item.last_seen_at.isoformat()
                    if item.last_seen_at
                    else None,
                    "expires_at": item.expires_at.isoformat(),
                    "revoked_at": item.revoked_at.isoformat()
                    if item.revoked_at
                    else None,
                    "current": item.session_key == request.session.session_key,
                }
                for item in rows
            ]
        }
    )


@require_http_methods(["DELETE"])
def revoke_session(request, session_id):
    if not request.user.is_authenticated:
        return error("Authentication required", 401, "UNAUTHENTICATED")
    record = request.user.account_sessions.filter(
        id=session_id, revoked_at__isnull=True
    ).first()
    if record is None:
        return error("Session not found", 404, "NOT_FOUND")
    record.revoked_at = timezone.now()
    record.save(update_fields=["revoked_at"])
    from django.contrib.sessions.models import Session as DjangoSession

    DjangoSession.objects.filter(session_key=record.session_key).delete()
    return JsonResponse({"ok": True})


@require_http_methods(["GET", "PATCH"])
def organization_detail(request, slug):
    membership, response = membership_or_error(
        request,
        slug,
        "organization.view" if request.method == "GET" else "organization.update",
    )
    if response:
        return response
    organization = membership.organization
    if request.method == "PATCH":
        payload = (
            request.POST
            if request.content_type and request.content_type.startswith("multipart/")
            else body(request)
        )
        for field in ("name", "timezone", "locale", "logo_alt_text"):
            if field in payload:
                setattr(organization, field, str(payload[field]).strip())
        logo = request.FILES.get("logo_image")
        if logo:
            if logo.size > 5 * 1024 * 1024:
                return error("Organization logos must be 5 MB or smaller")
            organization.logo_image = logo
        organization.full_clean()
        organization.save()
    return JsonResponse(
        {
            "organization": serialize_org(request, organization),
            "allowed_actions": membership.role_policy.allowed_actions,
        }
    )


@require_http_methods(["GET", "POST"])
def memberships(request, slug):
    membership, response = membership_or_error(
        request,
        slug,
        "membership.list" if request.method == "GET" else "membership.invite",
    )
    if response:
        return response
    if request.method == "POST":
        payload = body(request)
        user = AppUser.objects.filter(
            email=str(payload.get("email", "")).lower()
        ).first()
        role = RolePolicy.objects.filter(
            organization=membership.organization,
            id=payload.get("role_policy_id"),
            is_active=True,
        ).first()
        if user is None or role is None:
            return error("A valid existing user and tenant role are required")
        item, _ = Membership.objects.update_or_create(
            organization=membership.organization,
            user=user,
            defaults={
                "role_policy": role,
                "status": "invited",
                "invited_by": request.user,
                "invited_at": timezone.now(),
            },
        )
        return JsonResponse(
            {"membership_id": str(item.id), "status": item.status}, status=201
        )
    rows = (
        Membership.objects.select_related("user", "role_policy")
        .filter(organization=membership.organization)
        .exclude(status="removed")
    )
    return JsonResponse(
        {
            "memberships": [
                {
                    "id": str(item.id),
                    "user": serialize_user(request, item.user),
                    "role": {
                        "id": str(item.role_policy_id),
                        "key": item.role_policy.key,
                        "name": item.role_policy.name,
                    },
                    "status": item.status,
                    "joined_at": item.joined_at.isoformat() if item.joined_at else None,
                }
                for item in rows
            ]
        }
    )


@require_http_methods(["GET", "POST"])
def role_policies(request, slug):
    membership, response = membership_or_error(
        request,
        slug,
        "role_policy.list" if request.method == "GET" else "role_policy.create",
    )
    if response:
        return response
    if request.method == "POST":
        payload = body(request)
        policy = RolePolicy.objects.create(
            organization=membership.organization,
            name=str(payload.get("name", "")).strip()[:120],
            key=str(payload.get("key", "")).strip()[:80],
            description=str(payload.get("description", "")),
            resource_scope=payload.get("resource_scope", []),
            allowed_actions=payload.get("allowed_actions", []),
            conditions_json=payload.get("conditions", {}),
            priority=int(payload.get("priority", 100)),
            is_active=True,
        )
        return JsonResponse(
            {"role_policy_id": str(policy.id), "version": policy.version}, status=201
        )
    rows = RolePolicy.objects.filter(organization=membership.organization)
    return JsonResponse(
        {
            "role_policies": [
                {
                    "id": str(item.id),
                    "key": item.key,
                    "name": item.name,
                    "description": item.description,
                    "resource_scope": item.resource_scope,
                    "allowed_actions": item.allowed_actions,
                    "priority": item.priority,
                    "is_active": item.is_active,
                    "version": item.version,
                }
                for item in rows
            ]
        }
    )


@require_http_methods(["GET", "POST"])
def saved_views(request, slug):
    membership, response = membership_or_error(
        request,
        slug,
        "saved_view.list" if request.method == "GET" else "saved_view.create",
    )
    if response:
        return response
    if request.method == "POST":
        payload = body(request)
        filters = payload.get("filters", [])
        sorts = payload.get("sorts", [])
        columns = payload.get("visible_columns", [])
        dashboards = payload.get("dashboard_selection", [])
        try:
            validate_saved_view_definition(
                payload.get("module_key", ""), filters, sorts, columns, dashboards
            )
        except ValueError as exc:
            return error(str(exc))
        with transaction.atomic():
            if payload.get("is_default"):
                SavedView.objects.filter(
                    organization=membership.organization,
                    user=request.user,
                    module_key=payload["module_key"],
                    is_default=True,
                ).update(is_default=False)
            view = SavedView.objects.create(
                organization=membership.organization,
                user=request.user,
                module_key=payload["module_key"],
                name=str(payload.get("name", "")).strip()[:120],
                filters_json=filters,
                sorts_json=sorts,
                visible_columns=columns,
                density=payload.get("density", "comfortable"),
                dashboard_selection=dashboards,
                is_default=bool(payload.get("is_default")),
            )
        return JsonResponse({"saved_view": serialize_saved_view(view)}, status=201)
    rows = SavedView.objects.filter(
        organization=membership.organization, user=request.user
    )
    return JsonResponse({"saved_views": [serialize_saved_view(item) for item in rows]})


@require_http_methods(["PATCH", "DELETE"])
def saved_view_detail(request, slug, view_id):
    membership, response = membership_or_error(
        request,
        slug,
        "saved_view.delete" if request.method == "DELETE" else "saved_view.update",
    )
    if response:
        return response
    item = SavedView.objects.filter(
        id=view_id, organization=membership.organization, user=request.user
    ).first()
    if item is None:
        return error("Saved view not found", 404, "NOT_FOUND")
    if request.method == "DELETE":
        item.delete()
        return JsonResponse({"ok": True})
    payload = body(request)
    module_key = payload.get("module_key", item.module_key)
    filters = payload.get("filters", item.filters_json)
    sorts = payload.get("sorts", item.sorts_json)
    columns = payload.get("visible_columns", item.visible_columns)
    dashboards = payload.get("dashboard_selection", item.dashboard_selection)
    try:
        validate_saved_view_definition(module_key, filters, sorts, columns, dashboards)
    except ValueError as exc:
        return error(str(exc))
    with transaction.atomic():
        if payload.get("is_default"):
            SavedView.objects.filter(
                organization=membership.organization,
                user=request.user,
                module_key=module_key,
                is_default=True,
            ).exclude(id=item.id).update(is_default=False)
        item.module_key = module_key
        item.name = str(payload.get("name", item.name)).strip()[:120]
        item.filters_json, item.sorts_json, item.visible_columns = (
            filters,
            sorts,
            columns,
        )
        item.dashboard_selection = dashboards
        item.density = payload.get("density", item.density)
        item.is_default = bool(payload.get("is_default", item.is_default))
        item.full_clean()
        item.save()
    return JsonResponse({"saved_view": serialize_saved_view(item)})


@require_http_methods(["GET", "PATCH"])
def accessibility_preferences(request):
    if not request.user.is_authenticated:
        return error("Authentication required", 401, "UNAUTHENTICATED")
    item, _ = AccessibilityPreference.objects.get_or_create(user=request.user)
    if request.method == "PATCH":
        payload = body(request)
        for field in (
            "reduced_motion",
            "density",
            "contrast_mode",
            "input_mode",
            "large_text",
        ):
            if field in payload:
                setattr(item, field, payload[field])
        item.full_clean()
        item.save()
    return JsonResponse(
        {
            "preference": {
                "reduced_motion": item.reduced_motion,
                "density": item.density,
                "contrast_mode": item.contrast_mode,
                "input_mode": item.input_mode,
                "large_text": item.large_text,
                "updated_at": item.updated_at.isoformat(),
            }
        }
    )


def serialize_saved_view(item):
    return {
        "id": str(item.id),
        "module_key": item.module_key,
        "name": item.name,
        "filters": item.filters_json,
        "sorts": item.sorts_json,
        "visible_columns": item.visible_columns,
        "density": item.density,
        "dashboard_selection": item.dashboard_selection,
        "is_default": item.is_default,
        "updated_at": item.updated_at.isoformat(),
    }
