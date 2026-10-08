"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/accounts/api";
import { ErrorState, LoadingState } from "@/components/kernel/projection";
import { RichTextEditor } from "@/components/ui/rich-text-editor";

export type OperationsSection = "feedback" | "requests" | "comments" | "files" | "search" | "data-jobs" | "audit" | "work-orders" | "notifications";
type Row = Record<string, unknown> & { id?: string };

const meta: Record<OperationsSection, { code: string; title: string; detail: string; key: string }> = {
  feedback: { code: "KL-F-22", title: "User feedback", detail: "Consent-aware product feedback with allow-listed context and triage.", key: "feedback" },
  requests: { code: "KL-F-07", title: "Request intake", detail: "Idempotent tenant requests with urgency, location and preferred service windows.", key: "requests" },
  comments: { code: "KL-F-13", title: "Comments and mentions", detail: "Sanitised rich collaboration with customer-safe visibility boundaries.", key: "comments" },
  files: { code: "KL-F-14", title: "File evidence", detail: "Authorised evidence metadata, integrity hashes, scan state and object storage keys.", key: "files" },
  search: { code: "KL-F-16", title: "Authorised search", detail: "Tenant and policy scoped search projections evaluated before result exposure.", key: "results" },
  "data-jobs": { code: "KL-F-19", title: "Imports and exports", detail: "Bounded asynchronous data jobs with validation counts and frozen manifests.", key: "exports" },
  audit: { code: "KL-F-20", title: "Audit ledger", detail: "Append-only, redacted mutation evidence for authorised reviewers.", key: "events" },
  "work-orders": { code: "KL-F-08", title: "Work lifecycle", detail: "Backend-guarded transitions, evidence requirements and structured work instructions.", key: "work_orders" },
  notifications: { code: "KL-F-17", title: "Notifications", detail: "Deduplicated in-app delivery governed by per-user preferences.", key: "notifications" },
};

export function OperationsWorkspace({ tenantSlug, section }: { tenantSlug: string; section: OperationsSection }) {
  const [payload, setPayload] = useState<Record<string, unknown>>();
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const definition = meta[section];
  const endpoint = `/api/v1/organizations/${tenantSlug}/operations/${section}/`;

  async function load(query = "") {
    try {
      setError("");
      if (section === "feedback") {
        setPayload({});
      } else if (section === "notifications") {
        const [notifications, preferences] = await Promise.all([
          apiRequest<Record<string, unknown>>(endpoint),
          apiRequest<Record<string, unknown>>(`/api/v1/organizations/${tenantSlug}/operations/notification-preferences/`),
        ]);
        setPayload({ ...notifications, ...preferences });
      } else {
        setPayload(await apiRequest<Record<string, unknown>>(`${endpoint}${query}`));
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The feature could not be loaded.");
    }
  }

  // Route identity is the intended refresh boundary.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { const timer = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(timer); }, [tenantSlug, section]);

  async function submitJson(values: Record<string, unknown>, path = endpoint) {
    try {
      await apiRequest(path, { method: "POST", body: JSON.stringify(values) });
      setNotice("Saved to the tenant workspace.");
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The change could not be saved.");
    }
  }

  if (error && !payload) return <ErrorState title={`${definition.title} unavailable`} detail={error} />;
  if (!payload) return <div className="panel"><LoadingState /></div>;
  const rows = (payload[definition.key] as Row[] | undefined) ?? [];

  return (
    <div className="space-y-6">
      <header className="border-b border-line pb-6"><p className="eyebrow">{definition.code}</p><h1 className="mt-2 font-heading text-4xl font-semibold tracking-[-.05em]">{definition.title}</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-muted">{definition.detail}</p></header>
      {notice ? <p className="border-l-2 border-accent bg-success-soft p-3 text-xs text-success-ink" role="status">{notice}</p> : null}
      {error ? <ErrorState title="Action not completed" detail={error} /> : null}
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
        <RecordList rows={rows} empty={`No ${definition.title.toLowerCase()} records yet.`} />
        <FeatureForm section={section} submit={submitJson} search={(query) => load(`?q=${encodeURIComponent(query)}`)} tenantSlug={tenantSlug} />
      </div>
      {section === "notifications" ? <PreferenceList rows={(payload.preferences as Row[] | undefined) ?? []} /> : null}
      {section === "data-jobs" ? <ImportList rows={(payload.imports as Row[] | undefined) ?? []} /> : null}
    </div>
  );
}

function RecordList({ rows, empty }: { rows: Row[]; empty: string }) {
  if (!rows.length) return <div className="panel text-sm text-muted">{empty}</div>;
  return <div className="grid content-start gap-px border border-line bg-line">{rows.map((row, index) => {
    const title = String(row.title ?? row.description ?? row.message ?? row.original_name ?? row.event_type ?? row.event_id ?? row.resource_type ?? `Record ${index + 1}`);
    const status = row.status ?? row.triage_status ?? row.upload_status ?? row.category;
    const detail = String(row.plain_text ?? row.plain_instructions ?? row.body_text ?? row.location_text ?? row.reason ?? "");
    return <article className="bg-panel p-4" key={row.id ?? index}><div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="spec-kicker">{String(row.resource_type ?? row.channel ?? "Tenant record")}</p><h2 className="mt-2 truncate text-sm font-bold">{title}</h2></div>{status ? <span className="status-badge bg-primary-soft text-primary">{String(status)}</span> : null}</div>{detail ? <p className="mt-3 line-clamp-3 text-xs leading-5 text-muted">{detail}</p> : null}<p className="mt-4 font-mono text-[9px] uppercase text-faint">{String(row.created_at ?? row.updated_at ?? "")}</p></article>;
  })}</div>;
}

function FeatureForm({ section, submit, search, tenantSlug }: { section: OperationsSection; submit: (values: Record<string, unknown>, path?: string) => Promise<void>; search: (query: string) => Promise<void>; tenantSlug: string }) {
  if (section === "audit") return <aside className="panel self-start"><p className="eyebrow">Immutable surface</p><p className="mt-3 text-sm leading-6 text-muted">Audit events are created by backend mutations and cannot be edited or deleted.</p></aside>;
  if (section === "feedback") return <Form title="Submit feedback" action={(fd) => submit({ route: location.pathname, viewport_width: innerWidth, viewport_height: innerHeight, category: fd.get("category"), message: fd.get("message"), consent_context_capture: fd.get("consent") === "on" })}><Select name="category" label="Category" options={["bug", "usability", "content", "performance", "other"]}/><Textarea name="message" label="Feedback"/><Check name="consent" label="Include viewport and route context"/></Form>;
  if (section === "requests") return <Form title="New service request" action={(fd) => submit({ location_text: fd.get("location"), urgency: fd.get("urgency"), description: fd.get("description"), preferred_start_at: fd.get("start"), preferred_end_at: fd.get("end") })}><Input name="location" label="Location"/><Select name="urgency" label="Urgency" options={["low", "normal", "high", "critical"]}/><Textarea name="description" label="Problem description"/><Input name="start" label="Preferred start" type="datetime-local"/><Input name="end" label="Preferred end" type="datetime-local"/></Form>;
  if (section === "comments") return <Form title="Add comment" action={(fd) => submit({ resource_type: fd.get("resource_type"), resource_id: fd.get("resource_id"), body: fd.get("body"), visibility: fd.get("visibility") })}><Input name="resource_type" label="Target type" defaultValue="work_order"/><Input name="resource_id" label="Target UUID"/><Select name="visibility" label="Visibility" options={["internal", "customer_visible", "restricted_role"]}/><RichTextEditor name="body" label="Comment"/></Form>;
  if (section === "files") return <FileForm tenantSlug={tenantSlug} />;
  if (section === "search") return <Form title="Search permitted records" submitLabel="Search" action={(fd) => search(String(fd.get("query")))}><Input name="query" label="Search query"/></Form>;
  if (section === "data-jobs") return <Form title="Create export" action={(fd) => submit({ kind: "export", resource_type: fd.get("resource_type"), columns: String(fd.get("columns")).split(",").map((value) => value.trim()).filter(Boolean), filters: {} })}><Select name="resource_type" label="Resource" options={["service_request", "work_order", "comment", "file_asset"]}/><Input name="columns" label="Columns, comma separated" defaultValue="title,status,created_at"/></Form>;
  if (section === "work-orders") return <Form title="Create work order" action={(fd) => submit({ title: fd.get("title"), instructions: fd.get("instructions"), priority: fd.get("priority"), scheduled_start_at: fd.get("start") })}><Input name="title" label="Work title"/><Select name="priority" label="Priority" options={["low", "normal", "high", "critical"]}/><RichTextEditor name="instructions" label="Work instructions"/><Input name="start" label="Scheduled start" type="datetime-local"/></Form>;
  return <Form title="Notification preference" action={(fd) => submit({ event_key: fd.get("event_key"), in_app: fd.get("in_app") === "on", email: fd.get("email") === "on" }, `/api/v1/organizations/${tenantSlug}/operations/notification-preferences/`)}><Input name="event_key" label="Event key" defaultValue="work_order.updated"/><Check name="in_app" label="In-app notifications" defaultChecked/><Check name="email" label="Email notifications"/></Form>;
}

function Form({ title, action, children, submitLabel = "Save" }: { title: string; action: (data: FormData) => void | Promise<void>; children: React.ReactNode; submitLabel?: string }) { return <form action={action} className="panel self-start"><p className="eyebrow">{title}</p><div className="mt-5 space-y-4">{children}<button className="button-primary w-full">{submitLabel}</button></div></form>; }
function Input({ name, label, type = "text", defaultValue }: { name: string; label: string; type?: string; defaultValue?: string }) { return <label className="field-label">{label}<input className="control" name={name} type={type} defaultValue={defaultValue} required /></label>; }
function Textarea({ name, label }: { name: string; label: string }) { return <label className="field-label">{label}<textarea className="control min-h-28" name={name} required /></label>; }
function Select({ name, label, options }: { name: string; label: string; options: string[] }) { return <label className="field-label">{label}<select className="control" name={name}>{options.map((option) => <option key={option}>{option}</option>)}</select></label>; }
function Check({ name, label, defaultChecked = false }: { name: string; label: string; defaultChecked?: boolean }) { return <label className="flex items-center gap-2 text-xs"><input name={name} type="checkbox" defaultChecked={defaultChecked}/>{label}</label>; }
function PreferenceList({ rows }: { rows: Row[] }) { return <section className="panel"><p className="eyebrow">Delivery preferences</p><div className="mt-4 flex flex-wrap gap-2">{rows.map((row, index) => <span className="variant-chip" key={row.id ?? index}>{String(row.event_key)} · in-app {row.in_app ? "on" : "off"} · email {row.email ? "on" : "off"}</span>)}</div></section>; }
function ImportList({ rows }: { rows: Row[] }) { return <section className="panel"><p className="eyebrow">Import jobs</p><div className="mt-4 flex flex-wrap gap-2">{rows.map((row, index) => <span className="variant-chip" key={row.id ?? index}>{String(row.resource_type)} · {String(row.status)} · {String(row.valid_rows ?? 0)} valid / {String(row.invalid_rows ?? 0)} invalid</span>)}</div></section>; }

function FileForm({ tenantSlug }: { tenantSlug: string }) {
  const [message, setMessage] = useState("");
  async function upload(fd: FormData) {
    try {
      await apiRequest(`/api/v1/organizations/${tenantSlug}/operations/files/`, { method: "POST", body: fd });
      setMessage("Evidence uploaded. Refresh to see the new metadata record.");
    } catch (cause) { setMessage(cause instanceof Error ? cause.message : "Upload failed."); }
  }
  return <Form title="Upload evidence" action={upload} submitLabel="Upload"><Input name="resource_type" label="Target type" defaultValue="work_order"/><Input name="resource_id" label="Target UUID"/><label className="field-label">Evidence file<input className="control" name="file" type="file" required /></label><Select name="visibility" label="Visibility" options={["internal", "customer_visible", "restricted"]}/>{message ? <p className="text-xs text-muted">{message}</p> : null}</Form>;
}
