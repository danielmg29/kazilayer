from .models import Membership


def resolve_membership(user, organization_slug):
    if not user.is_authenticated:
        return None
    return (
        Membership.objects.select_related("organization", "role_policy")
        .filter(
            user=user,
            organization__slug=organization_slug,
            organization__status="active",
            status="active",
            role_policy__is_active=True,
        )
        .first()
    )


def has_action(membership, action):
    if membership is None:
        return False
    return action in membership.role_policy.allowed_actions


def require_action(membership, action):
    if not has_action(membership, action):
        raise PermissionError(f"The active membership does not allow {action}")
