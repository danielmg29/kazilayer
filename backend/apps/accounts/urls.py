from django.urls import path

from . import api

urlpatterns = [
    path("csrf/", api.csrf),
    path("auth/login/", api.login_view),
    path("auth/logout/", api.logout_view),
    path("auth/password-reset/", api.password_reset_request),
    path("auth/password-reset/confirm/", api.password_reset_confirm),
    path("auth/mfa/setup/", api.mfa_setup),
    path("auth/mfa/confirm/", api.mfa_confirm),
    path("auth/sessions/", api.sessions),
    path("auth/sessions/<uuid:session_id>/", api.revoke_session),
    path("me/", api.me),
    path("profile/", api.profile),
    path("accessibility-preferences/", api.accessibility_preferences),
    path("organizations/<slug:slug>/", api.organization_detail),
    path("organizations/<slug:slug>/memberships/", api.memberships),
    path("organizations/<slug:slug>/role-policies/", api.role_policies),
    path("organizations/<slug:slug>/saved-views/", api.saved_views),
    path(
        "organizations/<slug:slug>/saved-views/<uuid:view_id>/", api.saved_view_detail
    ),
]
