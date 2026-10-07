MODULE_FIELDS = {
    "overview": {"status", "owner", "updated_at"},
    "members": {"display_name", "email", "role", "status", "joined_at"},
    "roles": {"name", "resource_scope", "priority", "is_active", "updated_at"},
    "saved-views": {"name", "module_key", "density", "is_default", "updated_at"},
    "requests": {"reference", "title", "status", "priority", "site", "created_at"},
    "work-orders": {
        "reference",
        "title",
        "status",
        "technician",
        "scheduled_at",
        "sla_state",
    },
    "dispatch": {"technician", "capacity", "scheduled_at", "status"},
}


def validate_saved_view_definition(module_key, filters, sorts, columns, dashboards):
    allowed = MODULE_FIELDS.get(module_key)
    if allowed is None:
        raise ValueError("Unknown module key")
    for entry in filters:
        if not isinstance(entry, dict) or entry.get("field") not in allowed:
            raise ValueError("A filter references a field outside the current contract")
    for entry in sorts:
        if (
            not isinstance(entry, dict)
            or entry.get("field") not in allowed
            or entry.get("direction") not in {"asc", "desc"}
        ):
            raise ValueError("A sort definition is invalid")
    if any(field not in allowed for field in columns):
        raise ValueError("A visible column is outside the current contract")
    if not all(isinstance(item, str) and len(item) <= 80 for item in dashboards):
        raise ValueError("Dashboard selections must be bounded keys")
