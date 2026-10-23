"use client";

import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "@/lib/accounts/api";
import { PaginatedCollection } from "@/components/ui/paginated-collection";

type Row = Record<string, unknown>;
export type SchedulingSection = "dispatch" | "sla";

export function SchedulingWorkspace({ tenantSlug, section }: { tenantSlug: string; section: SchedulingSection }) {
  const [data, setData] = useState<Row | null>(null);
  const [error, setError] = useState("");
  const endpoint = `/api/v1/organizations/${tenantSlug}/operations/${section === "dispatch" ? "dispatch" : "sla-policies"}/`;
  const load = useCallback(() => apiRequest<Row>(endpoint).then(setData).catch((reason: Error) => setError(reason.message)), [endpoint]);
  useEffect(() => { void load(); }, [load]);

  async function submit(formData: FormData) {
    setError("");
    const payload = section === "dispatch"
      ? { assignment_id: formData.get("assignment_id") || undefined, expected_version: Number(formData.get("expected_version") || 0), work_order_id: formData.get("work_order_id"), technician_id: formData.get("technician_id"), start_at: new Date(String(formData.get("start_at"))).toISOString(), end_at: new Date(String(formData.get("end_at"))).toISOString(), reason: formData.get("reason") }
      : { name: formData.get("name"), priority_key: formData.get("priority_key"), response_minutes: Number(formData.get("response_minutes")), completion_minutes: Number(formData.get("completion_minutes")), version: 2, business_calendar: { timezone: "Africa/Nairobi", workdays: [0, 1, 2, 3, 4], start: "08:00", end: "17:00", holidays: [] }, pause_state_keys: ["blocked"] };
    await apiRequest(endpoint, { method: "POST", body: JSON.stringify(payload) }).then(load).catch((reason: Error) => setError(reason.message));
  }

  if (!data) return <div className="panel">{error || "Loading scheduling contract..."}</div>;
  return <div className="space-y-6">
    <header className="border-b border-line pb-6"><p className="eyebrow">{section === "dispatch" ? "KL-F-09" : "KL-F-10"}</p><h1 className="mt-2 font-heading text-4xl font-semibold tracking-[-.05em]">{section === "dispatch" ? "Dispatch board" : "SLA engine"}</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-muted">{section === "dispatch" ? "Live technician capacity, unscheduled work and conflict-safe assignment." : "Versioned response and completion targets calculated against business time."}</p></header>
    {error ? <p role="alert" className="border-l-2 border-danger bg-danger-soft p-3 text-sm text-danger-ink">{error}</p> : null}
    {section === "dispatch" ? <Dispatch data={data} submit={submit}/> : <Sla data={data} submit={submit}/>}
  </div>;
}

function Dispatch({ data, submit }: { data: Row; submit: (form: FormData) => Promise<void> }) {
  const technicians = (data.technicians as Row[]) ?? []; const unscheduled = (data.unscheduled as Row[]) ?? [];
  return <div className="space-y-5"><PaginatedCollection items={technicians} itemLabel="technicians">{visibleTechnicians => <div className="grid gap-4 border border-line p-4 xl:grid-cols-2">{visibleTechnicians.map((tech) => <TechnicianLane tech={tech} submit={submit} key={String(tech.id)}/>)}</div>}</PaginatedCollection><form action={submit} className="panel grid gap-4 lg:grid-cols-2"><p className="eyebrow lg:col-span-2">Schedule editor</p><Select name="work_order_id" label="Unscheduled work" rows={unscheduled} labelKey="title"/><Select name="technician_id" label="Technician" rows={technicians} labelKey="display_name"/><Input name="start_at" label="Start" type="datetime-local"/><Input name="end_at" label="End" type="datetime-local"/><Input name="reason" label="Dispatch reason"/><button className="button-primary self-end">Assign with conflict check</button></form></div>;
}

function TechnicianLane({ tech, submit }: { tech: Row; submit: (form: FormData) => Promise<void> }) {
  const assignments = (tech.assignments as Row[]) ?? [];
  return <section className="panel"><div className="flex justify-between"><div><p className="eyebrow">Capacity lane</p><h2 className="section-title">{String(tech.display_name)}</h2></div><span className="variant-chip">{assignments.length} booked</span></div><PaginatedCollection items={assignments} itemLabel="assignments" className="mt-5" initialPageSize={5} pageSizeOptions={[5, 10, 25]} compact>{visibleAssignments => <div className="space-y-2 border border-line p-2">{visibleAssignments.map((item) => <article className="border-l-4 border-accent bg-subtle p-3" key={String(item.id)}><b className="text-sm">{String(item.title)}</b><p className="mt-1 font-mono text-[10px] text-muted">{format(item.start_at)} - {format(item.end_at)}</p><span className="status-badge mt-2">{String(item.status)} · v{String(item.version)}</span><details className="mt-3"><summary className="cursor-pointer text-xs font-bold">Reschedule</summary><form action={submit} className="mt-3 grid gap-2"><input type="hidden" name="assignment_id" value={String(item.id)}/><input type="hidden" name="expected_version" value={String(item.version)}/><input type="hidden" name="work_order_id" value={String(item.work_order_id)}/><input type="hidden" name="technician_id" value={String(item.technician_id)}/><Input name="start_at" label="New start" type="datetime-local"/><Input name="end_at" label="New end" type="datetime-local"/><Input name="reason" label="Reschedule reason"/><button className="button-primary">Commit reschedule</button></form></details></article>)}</div>}</PaginatedCollection></section>;
}

function Sla({ data, submit }: { data: Row; submit: (form: FormData) => Promise<void> }) {
  const rows = (data.policies as Row[]) ?? [];
  return <div className="grid gap-5 xl:grid-cols-[1fr_380px]"><PaginatedCollection items={rows} itemLabel="policies">{visibleRows => <div className="grid gap-px border border-line bg-line">{visibleRows.map((row) => <article className="bg-panel p-4" key={String(row.id)}><div className="flex justify-between"><div><p className="eyebrow">Policy v{String(row.version)}</p><h2 className="mt-2 font-semibold">{String(row.name)}</h2></div><span className="status-badge">{String(row.priority_key)}</span></div><div className="mt-4 grid grid-cols-2 gap-3"><Metric label="First response" value={`${row.response_minutes} min`}/><Metric label="Completion" value={`${row.completion_minutes} min`}/></div></article>)}</div>}</PaginatedCollection><form action={submit} className="panel self-start space-y-4"><p className="eyebrow">Create policy version</p><Input name="name" label="Policy name"/><label className="field-label">Priority<select className="control" name="priority_key">{["low", "normal", "high", "critical"].map((x) => <option key={x}>{x}</option>)}</select></label><Input name="response_minutes" label="Response minutes" type="number"/><Input name="completion_minutes" label="Completion minutes" type="number"/><button className="button-primary w-full">Save policy</button></form></div>;
}

function Input({ name, label, type = "text" }: { name: string; label: string; type?: string }) { return <label className="field-label">{label}<input className="control" name={name} type={type} required/></label>; }
function Select({ name, label, rows, labelKey }: { name: string; label: string; rows: Row[]; labelKey: string }) { return <label className="field-label">{label}<select className="control" name={name} required>{rows.map((row) => <option key={String(row.id)} value={String(row.id)}>{String(row[labelKey])}</option>)}</select></label>; }
function Metric({ label, value }: { label: string; value: string }) { return <div className="bg-subtle p-3"><p className="eyebrow">{label}</p><b className="mt-2 block text-xl">{value}</b></div>; }
function format(value: unknown) { return new Date(String(value)).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }); }
