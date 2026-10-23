"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { apiRequest, loadMe } from "@/lib/accounts/api";
import type { MeResponse } from "@/lib/accounts/types";

type AccessibilityPreference = { reduced_motion: boolean; density: string; contrast_mode: string; input_mode: string; large_text: boolean };

const navigation = [
  { key: "overview", label: "Overview", mark: "OV", action: "organization.view" },
  { key: "members", label: "People", mark: "PE", action: "membership.list" },
  { key: "roles", label: "Role policy", mark: "RP", action: "role_policy.list" },
  { key: "saved-views", label: "Saved views", mark: "SV", action: "saved_view.list" },
  { key: "requests", label: "Requests", mark: "RQ", action: "request.list" },
  { key: "work-orders", label: "Work orders", mark: "WO", action: "work_order.list" },
  { key: "comments", label: "Comments", mark: "CM", action: "comment.list" },
  { key: "files", label: "Evidence", mark: "EV", action: "file.list" },
  { key: "search", label: "Search", mark: "SE", action: "search.query" },
  { key: "data-jobs", label: "Data jobs", mark: "DJ", action: "data_job.list" },
  { key: "audit", label: "Audit", mark: "AU", action: "audit.list" },
  { key: "notifications", label: "Notifications", mark: "NT", action: "notification.list" },
  { key: "feedback", label: "Feedback", mark: "FB", action: "feedback.create" },
  { key: "contracts", label: "Contracts", mark: "CT", action: "contract.list" },
  { key: "dynamic-forms", label: "Dynamic forms", mark: "DF", action: "dynamic_form.use" },
  { key: "adaptive-views", label: "View recipes", mark: "VR", action: "view_recipe.list" },
  { key: "dashboards", label: "Dashboards", mark: "DB", action: "dashboard.list" },
  { key: "integrations", label: "Integrations", mark: "IN", action: "webhook.list" },
  { key: "realtime", label: "Realtime", mark: "RT", action: "realtime.subscribe" },
  { key: "bulk-operations", label: "Bulk operations", mark: "BK", action: "bulk.list" },
  { key: "sla", label: "SLA policies", mark: "SL", action: "sla.list" },
  { key: "dispatch", label: "Dispatch", mark: "DP", action: "dispatch.view" },
  { key: "accessibility", label: "Accessibility", mark: "AX", action: null },
  { key: "settings", label: "Settings", mark: "ST", action: "organization.update" },
] as const;

export function AppShell({ children, tenantSlug = "meridian-field-services" }: { children: ReactNode; tenantSlug?: string }) {
  const pathname = usePathname();
  const router = useRouter();
  const [identity, setIdentity] = useState<MeResponse | null>(null);
  const [accessibility, setAccessibility] = useState<AccessibilityPreference | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const [signOutError, setSignOutError] = useState("");
  const membership = useMemo(
    () => identity?.memberships.find((item) => item.organization.slug === tenantSlug),
    [identity, tenantSlug],
  );

  useEffect(() => {
    const refreshIdentity = () => loadMe().then(setIdentity).catch(() => router.replace("/login"));
    const refreshAccessibility = () => apiRequest<{ preference: AccessibilityPreference }>("/api/v1/accessibility-preferences/").then((result) => setAccessibility(result.preference)).catch(() => undefined);
    void refreshIdentity();
    void refreshAccessibility();
    window.addEventListener("kazilayer:profile-updated", refreshIdentity);
    window.addEventListener("kazilayer:accessibility-updated", refreshAccessibility);
    return () => { window.removeEventListener("kazilayer:profile-updated", refreshIdentity); window.removeEventListener("kazilayer:accessibility-updated", refreshAccessibility); };
  }, [router]);

  const base = `/${membership?.organization.slug ?? tenantSlug}`;
  const enabled = new Set(membership?.organization.enabled_modules ?? []);
  const allowed = new Set(membership?.allowed_actions ?? []);
  const initials = identity?.user.display_name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase() ?? "KL";
  const tenantInitials = membership?.organization.name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase() ?? "--";

  async function signOut() {
    try {
      setSigningOut(true);
      setSignOutError("");
      await apiRequest<{ ok: boolean }>("/api/v1/auth/logout/", { method: "POST", body: "{}" });
      router.replace("/login");
      router.refresh();
    } catch (cause) {
      setSignOutError(cause instanceof Error ? cause.message : "Sign out failed. Please try again.");
      setSigningOut(false);
    }
  }

  return (
    <div className="app-shell min-h-screen bg-canvas text-ink" data-sidebar-collapsed={collapsed} data-density={accessibility?.density} data-contrast={accessibility?.contrast_mode} data-input-mode={accessibility?.input_mode} data-large-text={accessibility?.large_text} data-reduced-motion={accessibility?.reduced_motion}>
      <aside className="sidebar">
        <div className="sidebar-brand">
          <Link href={base} aria-label="KaziLayer overview" className="sidebar-logo-link">
            {collapsed ? (
              <Image src="/logo/logo-mark.svg" alt="KaziLayer" width={44} height={44} priority className="sidebar-logo-mark" />
            ) : (
              <Image src="/logo/logo-horizontal.svg" alt="KaziLayer — Work in one flow" width={196} height={49} priority className="sidebar-logo-full" />
            )}
          </Link>
          {!collapsed ? <button className="sidebar-toggle" type="button" onClick={() => setCollapsed(true)} aria-label="Collapse sidebar" title="Collapse sidebar">←</button> : null}
        </div>

        {collapsed ? (
          <button className="sidebar-toggle sidebar-toggle-collapsed" type="button" onClick={() => setCollapsed(false)} aria-label="Expand sidebar" title="Expand sidebar">→</button>
        ) : null}

        <div className="sidebar-tenant" title={collapsed ? membership?.organization.name : undefined}>
          {collapsed ? <span className="sidebar-tenant-mark">{tenantInitials}</span> : <><p className="spec-kicker">Active tenant</p><p className="mt-2 truncate font-heading text-sm font-semibold">{membership?.organization.name ?? "Resolving workspace"}</p><p className="mt-1 font-mono text-[9px] uppercase tracking-[.1em] text-muted">{membership?.role.name ?? "Resolving role…"}</p></>}
        </div>

        <nav className="sidebar-nav" aria-label="Primary navigation">
          {navigation
            .filter((item) => enabled.has(item.key) && (item.action === null || allowed.has(item.action)))
            .map((item, index) => {
              const href = item.key === "overview" ? base : `${base}/${item.key}`;
              return (
                <Link key={item.key} href={href} title={collapsed ? item.label : undefined} aria-label={collapsed ? item.label : undefined} className={pathname === href ? "nav-link nav-link-active" : "nav-link"}>
                  <span className="nav-index">{item.mark}</span>
                  {!collapsed ? <><span>{item.label}</span><span className="ml-auto font-mono text-[9px] opacity-40">0{index + 1}</span></> : null}
                </Link>
              );
            })}
        </nav>

        <div className="sidebar-utility">
          <Link title={collapsed ? "Profile" : undefined} aria-label={collapsed ? "Profile" : undefined} className={pathname === `${base}/profile` ? "nav-link nav-link-active" : "nav-link"} href={`${base}/profile`}><span className="nav-index">ID</span>{!collapsed ? <span>Profile</span> : null}</Link>
        </div>
      </aside>

      <div className="app-content">
        <header className="topbar">
          <Link href={base} className="md:hidden"><Image src="/logo/logo-mark.svg" alt="KaziLayer" width={36} height={36} /></Link>
          <div className="hidden items-center gap-2 text-xs text-muted md:flex"><span className="size-2 bg-accent" /><span>{membership?.organization.name ?? "Workspace"}</span><span className="text-faint">/</span><span className="capitalize">{pathname.split("/").filter(Boolean).at(-1)?.replaceAll("-", " ") ?? "Overview"}</span></div>
          <div className="ml-auto flex items-center gap-2">
            <span className="hidden border border-line bg-panel px-2 py-1 font-mono text-[9px] uppercase text-muted sm:block">{membership?.organization.timezone ?? "Africa/Nairobi"}</span>
            {signOutError ? <span className="hidden max-w-52 text-right text-[10px] text-danger-ink md:block" role="alert">{signOutError}</span> : null}
            <button className="button-secondary h-9 gap-2 px-3 text-xs" type="button" onClick={signOut} disabled={signingOut} aria-label={signingOut ? "Signing out" : "Sign out"}>
              <span aria-hidden="true">↪</span><span className="hidden sm:inline">{signingOut ? "Signing out…" : "Sign out"}</span>
            </button>
            <Link className="user-chip border-l border-line pl-3 no-underline" href={`${base}/profile`}>
              {identity?.user.avatar_url ? <Image src={identity.user.avatar_url} alt={identity.user.avatar_alt_text || "Profile"} width={36} height={36} className="size-9 object-cover" unoptimized /> : <span className="avatar">{initials}</span>}
              <span className="hidden sm:block"><b>{identity?.user.display_name ?? "Loading identity"}</b><small>{membership?.role.name ?? "Membership"}</small></span>
            </Link>
          </div>
        </header>
        <main className="mx-auto max-w-[1560px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">{children}</main>
        <footer className="mx-auto flex max-w-[1560px] flex-col gap-3 border-t border-line px-4 py-6 text-xs text-muted sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8"><span>KaziLayer · Work in one flow</span><span className="font-mono text-[10px] uppercase tracking-[.1em]">KL-F-01 · KL-F-02 · KL-F-03 · KL-F-11</span></footer>
      </div>
    </div>
  );
}
