import type { MeResponse } from "./types";

function csrfToken() {
  return document.cookie.split("; ").find((item) => item.startsWith("csrftoken="))?.split("=")[1] ?? "";
}

export async function ensureCsrf() {
  await fetch("/api/v1/csrf/", { credentials: "include" });
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = init.method?.toUpperCase() ?? "GET";
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) await ensureCsrf();
  const response = await fetch(path, {
    ...init,
    credentials: "include",
    headers: {
      ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(!["GET", "HEAD", "OPTIONS"].includes(method) ? { "X-CSRFToken": csrfToken() } : {}),
      ...init.headers,
    },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload?.error?.message ?? "The request could not be completed");
  if (typeof window !== "undefined" && path === "/api/v1/profile/" && !["GET", "HEAD"].includes(method)) {
    window.dispatchEvent(new Event("kazilayer:profile-updated"));
  }
  return payload as T;
}

export function loadMe() {
  return apiRequest<MeResponse>("/api/v1/me/");
}
