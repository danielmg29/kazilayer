"use client";

import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/accounts/api";
import type { AccountSession } from "@/lib/accounts/types";
import { PaginatedCollection } from "@/components/ui/paginated-collection";

export function SessionPanel() {
  const [sessions, setSessions] = useState<AccountSession[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const result = await apiRequest<{ sessions: AccountSession[] }>("/api/v1/auth/sessions/");
      setSessions(result.sessions);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Sessions could not be loaded.");
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function revoke(id: string) {
    await apiRequest<{ ok: boolean }>(`/api/v1/auth/sessions/${id}/`, { method: "DELETE" });
    await load();
  }

  return (
    <section className="panel mt-5">
      <p className="eyebrow">KL-F-02 · Sessions</p>
      <div className="mt-2 flex items-end justify-between gap-4">
        <div><h2 className="section-title">Signed-in devices</h2><p className="mt-2 text-sm text-muted">Review or revoke the bounded server sessions attached to your identity.</p></div>
        <span className="variant-chip">{sessions.filter((item) => !item.revoked_at).length} active</span>
      </div>
      {error ? <p className="mt-5 text-xs text-danger-ink" role="alert">{error}</p> : null}
      <PaginatedCollection items={sessions} itemLabel="sessions" className="mt-5">
        {(visibleSessions) => <div className="grid gap-px border border-line bg-line">
        {visibleSessions.map((session) => (
          <article className="flex flex-col gap-3 bg-panel p-4 sm:flex-row sm:items-center" key={session.id}>
            <div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold">{session.device_label || "Web browser"}</p><p className="mt-1 font-mono text-[10px] uppercase text-muted">Last seen {session.last_seen_at ? new Date(session.last_seen_at).toLocaleString() : "unknown"}</p></div>
            {session.current ? <span className="status-badge bg-success-soft text-success-ink">Current</span> : session.revoked_at ? <span className="status-badge">Revoked</span> : <button className="button-secondary" type="button" onClick={() => revoke(session.id)}>Revoke</button>}
          </article>
        ))}
      </div>}
      </PaginatedCollection>
    </section>
  );
}
