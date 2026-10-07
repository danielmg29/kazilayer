import { NextRequest, NextResponse } from "next/server";
import type { MeResponse } from "@/lib/accounts/types";

const sectionActions: Record<string, string | null> = {
  members: "membership.list",
  roles: "role_policy.list",
  "saved-views": "saved_view.list",
  settings: "organization.update",
  profile: null,
  feedback: "feedback.create",
  requests: "request.list",
  comments: "comment.list",
  files: "file.list",
  search: "search.query",
  "data-jobs": "data_job.list",
  audit: "audit.list",
  "work-orders": "work_order.list",
  notifications: "notification.list",
  contracts: "contract.list",
  "dynamic-forms": "dynamic_form.use",
  "adaptive-views": "view_recipe.list",
  dashboards: "dashboard.list",
  integrations: "webhook.list",
  realtime: "realtime.subscribe",
  "bulk-operations": "bulk.list",
  sla: "sla.list",
  dispatch: "dispatch.view",
  accessibility: null,
};

const publicRoots = new Set(["api", "_next", "login", "password-reset", "design-system", "logo", "fonts"]);

export async function proxy(request: NextRequest) {
  const segments = request.nextUrl.pathname.split("/").filter(Boolean);
  if (segments.length === 0 || segments.length > 2 || publicRoots.has(segments[0]) || request.nextUrl.pathname.includes(".")) {
    return NextResponse.next();
  }

  const [tenantSlug, section] = segments;
  const apiUrl = process.env.KAZILAYER_API_URL ?? "http://127.0.0.1:8000";
  let identity: MeResponse;

  try {
    const response = await fetch(`${apiUrl}/api/v1/me/`, {
      cache: "no-store",
      headers: { cookie: request.headers.get("cookie") ?? "" },
    });
    if (!response.ok) return NextResponse.redirect(new URL("/login", request.url));
    identity = await response.json() as MeResponse;
  } catch {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  const membership = identity.memberships.find((item) => item.organization.slug === tenantSlug);
  if (!membership) {
    const fallback = identity.memberships[0]?.organization.slug;
    return NextResponse.redirect(new URL(fallback ? `/${fallback}` : "/login", request.url));
  }

  const requiredAction = section ? sectionActions[section] : "organization.view";
  if (section && !(section in sectionActions)) return NextResponse.next();
  if (requiredAction && !membership.allowed_actions.includes(requiredAction)) {
    const denied = new URL(`/${tenantSlug}`, request.url);
    denied.searchParams.set("access", "denied");
    return NextResponse.redirect(denied);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
