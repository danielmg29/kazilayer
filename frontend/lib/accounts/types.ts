export type Organization = { id: string; name: string; slug: string; status: string; timezone: string; locale: string; settings: Record<string, unknown>; enabled_modules: string[]; logo_url: string | null; logo_alt_text: string };
export type User = { id: string; email: string; display_name: string; avatar_url: string | null; avatar_alt_text: string; email_verified_at: string | null };
export type MembershipProjection = { organization: Organization; role: { key: string; name: string }; allowed_actions: string[] };
export type MeResponse = { user: User; memberships: MembershipProjection[] };
export type Member = { id: string; user: User; role: { id: string; key: string; name: string }; status: string; joined_at: string | null };
export type RolePolicy = { id: string; key: string; name: string; description: string; resource_scope: string[]; allowed_actions: string[]; priority: number; is_active: boolean; version: number };
export type SavedView = { id: string; module_key: string; name: string; filters: unknown[]; sorts: unknown[]; visible_columns: string[]; density: string; dashboard_selection: string[]; is_default: boolean; updated_at: string };
export type AccountSession = { id: string; device_label: string; created_at: string; last_seen_at: string | null; expires_at: string; revoked_at: string | null; current: boolean };
