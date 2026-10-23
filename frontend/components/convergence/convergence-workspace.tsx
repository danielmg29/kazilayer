"use client";

import { useCallback, useEffect, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { apiRequest } from "@/lib/accounts/api";
import { ErrorState, LoadingState } from "@/components/kernel/projection";
import { RichTextEditor } from "@/components/ui/rich-text-editor";
import { PaginatedCollection } from "@/components/ui/paginated-collection";

export type ConvergenceSection = "contracts" | "dynamic-forms" | "adaptive-views" | "dashboards" | "integrations" | "realtime" | "bulk-operations";
type Data = Record<string, unknown>;

const definitions: Record<ConvergenceSection, { code: string; title: string; detail: string }> = {
  contracts: { code: "KL-F-04", title: "Contract registry", detail: "Draft, publish and govern immutable versioned entity contracts." },
  "dynamic-forms": { code: "KL-F-05", title: "Dynamic forms", detail: "Generated controls, validation and permissions projected from a published contract." },
  "adaptive-views": { code: "KL-F-06", title: "Adaptive record views", detail: "Reusable semantic recipes for cards, panels, tables, timelines and compact layouts." },
  dashboards: { code: "KL-F-15", title: "Operational dashboards", detail: "Backend-owned metric definitions composed into tenant dashboard layouts." },
  integrations: { code: "KL-F-21", title: "Integration webhooks", detail: "Encrypted signing secrets, scoped events, rotation and bounded delivery evidence." },
  realtime: { code: "KL-F-18", title: "Realtime updates", detail: "One sequenced tenant stream with gap detection and bounded refetch semantics." },
  "bulk-operations": { code: "KL-F-12", title: "Bulk operations", detail: "Server-previewed bounded selections with frozen queries and progress accounting." },
};

export function ConvergenceWorkspace({ tenantSlug, section }: { tenantSlug: string; section: ConvergenceSection }) {
  const [data, setData] = useState<Data>();
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [lastSequence, setLastSequence] = useState(0);
  const base = `/api/v1/organizations/${tenantSlug}/convergence`;

  const endpoint = useCallback(() => {
    if (section === "dynamic-forms") return `${base}/dynamic-forms/maintenance-work-order/`;
    if (section === "adaptive-views") return `${base}/view-recipes/`;
    if (section === "integrations") return `${base}/webhooks/`;
    if (section === "realtime") return `${base}/realtime/?stream=tenant:${tenantSlug}&after=${lastSequence}`;
    return `${base}/${section}/`;
  }, [base, lastSequence, section, tenantSlug]);

  const load = useCallback(async () => {
    try {
      const result = await apiRequest<Data>(endpoint());
      setData((current) => section === "realtime" && current ? mergeRealtime(current, result) : result);
      if (section === "realtime") setLastSequence(Number(result.last_sequence ?? 0));
      setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "The projection could not be loaded."); }
  }, [endpoint, section]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    const interval = section === "realtime" ? window.setInterval(() => void load(), 10000) : undefined;
    return () => { window.clearTimeout(timer); if (interval) window.clearInterval(interval); };
  }, [load, section]);

  async function post(path: string, values: Data) {
    try {
      const result = await apiRequest<Data>(path, { method: "POST", body: JSON.stringify(values) });
      setNotice("The tenant projection was updated.");
      if (result.signing_secret) setNotice(`Copy this signing secret now; it will not be shown again: ${String(result.signing_secret)}`);
      await load();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "The action could not be completed."); }
  }

  const definition = definitions[section];
  if (error && !data) return <ErrorState title={`${definition.title} unavailable`} detail={error}/>;
  if (!data) return <div className="panel"><LoadingState/></div>;
  return <div className="space-y-6"><header className="border-b border-line pb-6"><p className="eyebrow">{definition.code}</p><h1 className="mt-2 font-heading text-4xl font-semibold tracking-[-.05em]">{definition.title}</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-muted">{definition.detail}</p></header>{notice ? <p className="break-all border-l-2 border-accent bg-success-soft p-3 text-xs text-success-ink">{notice}</p> : null}{error ? <ErrorState title="Action not completed" detail={error}/> : null}<Section section={section} data={data} base={base} post={post}/></div>;
}

function mergeRealtime(current: Data, incoming: Data) {
  const prior = (current.events as Data[] | undefined) ?? [];
  const next = (incoming.events as Data[] | undefined) ?? [];
  const events = [...prior, ...next].filter((event, index, rows) => rows.findIndex((candidate) => candidate.event_id === event.event_id) === index).slice(-100);
  return { ...incoming, events };
}

function Section({ section, data, base, post }: { section: ConvergenceSection; data: Data; base: string; post: (path: string, values: Data) => Promise<void> }) {
  if (section === "contracts") return <Contracts rows={(data.contracts as Data[]) ?? []} create={(values) => post(`${base}/contracts/`, values)}/>;
  if (section === "dynamic-forms") return <DynamicForm value={data.form as Data} validate={(values) => post(`${base}/dynamic-forms/maintenance-work-order/`, values)}/>;
  if (section === "adaptive-views") return <Recipes rows={(data.recipes as Data[]) ?? []}/>;
  if (section === "dashboards") return <Dashboards rows={(data.dashboards as Data[]) ?? []} create={(values) => post(`${base}/dashboards/`, values)}/>;
  if (section === "integrations") return <Webhooks rows={(data.endpoints as Data[]) ?? []} create={(values) => post(`${base}/webhooks/`, values)}/>;
  if (section === "realtime") return <Realtime data={data}/>;
  return <Bulk rows={(data.operations as Data[]) ?? []} create={(values) => post(`${base}/bulk-operations/`, values)}/>;
}

function Contracts({ rows, create }: { rows: Data[]; create: (values: Data) => Promise<void> }) {
  return <TwoColumn list={<Cards rows={rows} titleKey="name" statusKey="status" detailKey="plain_change_notes"/>} form={<Form title="Draft successor contract" action={(fd) => create({ contract_key: fd.get("contract_key"), name: fd.get("name"), entity_type: fd.get("entity_type"), change_notes: fd.get("change_notes"), schema: { type: "object" }, validation: { mode: "server_authoritative" }, fields: [{ field_key: "title", label: "Title", field_type: "text", required: true }, { field_key: "instructions", label: "Instructions", field_type: "rich_text", required: false }] })}><Input name="contract_key" label="Contract key" defaultValue="maintenance-work-order"/><Input name="name" label="Version name"/><Input name="entity_type" label="Entity type" defaultValue="work_order"/><RichTextEditor name="change_notes" label="Change notes"/></Form>}/>;
}

function DynamicForm({ value, validate }: { value: Data; validate: (values: Data) => Promise<void> }) {
  const fields = (value.fields as Data[]) ?? [];
  return <div className="grid gap-5 xl:grid-cols-[1fr_320px]"><Form title="Generated create form" submit="Validate projection" action={(fd) => validate({ ...value, field_values: Object.fromEntries(fd.entries()) })}>{fields.map((field) => <GeneratedField key={String(field.field_key)} field={field}/>)}</Form><aside className="panel self-start"><p className="eyebrow">Runtime state</p><dl className="mt-4 space-y-3 text-xs"><Runtime label="Contract version" value={value.contract_version_id}/><Runtime label="Mode" value={value.mode}/><Runtime label="Submit action" value={value.submit_action_key}/><Runtime label="Idempotency key" value={value.idempotency_key}/><Runtime label="Editable fields" value={(value.editable_fields as string[]).join(", ")}/></dl></aside></div>;
}

function GeneratedField({ field }: { field: Data }) {
  const name = String(field.field_key); const label = String(field.label); const required = Boolean(field.required);
  if (field.field_type === "rich_text") return <RichTextEditor name={name} label={label}/>;
  if (field.field_type === "select") return <label className="field-label">{label}<select className="control" name={name} required={required}>{((field.options as string[]) ?? []).map((option) => <option key={option}>{option}</option>)}</select><small className="font-normal text-muted">{String(field.help_text ?? "")}</small></label>;
  return <label className="field-label">{label}<input className="control" name={name} type={field.field_type === "datetime" ? "datetime-local" : "text"} required={required}/><small className="font-normal text-muted">{String(field.help_text ?? "")}</small></label>;
}

function Recipes({ rows }: { rows: Data[] }) { return <PaginatedCollection items={rows} itemLabel="recipes">{visibleRows => <div className="grid gap-4 border border-line p-4 lg:grid-cols-3">{visibleRows.map((row) => <article className="panel" key={String(row.id)}><div className="flex justify-between gap-2"><p className="eyebrow">{String(row.recipe_type)}</p><span className="variant-chip">{String(row.density)}</span></div><h2 className="section-title">{String(row.recipe_key)}</h2><div className="mt-5 grid gap-2 border border-line bg-subtle p-3">{Object.entries((row.slot_mapping as Data) ?? {}).map(([slot, field]) => <div className="flex justify-between bg-panel p-2 text-xs" key={slot}><span className="text-muted">{slot}</span><b>{String(field)}</b></div>)}</div><p className="mt-4 font-mono text-[9px] uppercase text-muted">{((row.action_keys as string[]) ?? []).join(" · ")}</p></article>)}</div>}</PaginatedCollection>; }

function Dashboards({ rows, create }: { rows: Data[]; create: (values: Data) => Promise<void> }) {
  const metrics = rows.flatMap((dashboard) => ((dashboard.widgets as Data[]) ?? []).map((widget) => widget.metric as Data).filter(Boolean));
  return <div className="space-y-5"><PaginatedCollection items={metrics} itemLabel="dashboard metrics">{visibleMetrics => <div className="grid gap-4 border border-line p-4 md:grid-cols-2">{visibleMetrics.map((metric) => <article className="panel" key={String(metric.key)}><p className="eyebrow">Metric v{String(metric.version)}</p><div className="mt-5 flex items-end justify-between"><div><p className="text-4xl font-semibold">{String(metric.value)}<small className="ml-1 text-xs text-muted">{String(metric.unit)}</small></p><h2 className="mt-2 text-sm font-bold">{String(metric.name)}</h2></div><div className="h-20 w-32"><ResponsiveContainer width="100%" height="100%"><BarChart data={[{ name: "Now", value: Number(metric.value) }]}><XAxis dataKey="name" hide/><YAxis hide/><Tooltip/><Bar dataKey="value" fill="var(--primary)"/></BarChart></ResponsiveContainer></div></div><p className="mt-3 text-xs text-muted">{String(metric.description)}</p></article>)}</div>}</PaginatedCollection><Form title="New personal dashboard" action={(fd) => create({ name: fd.get("name"), visibility: "private" })}><Input name="name" label="Dashboard name"/></Form></div>;
}

function Webhooks({ rows, create }: { rows: Data[]; create: (values: Data) => Promise<void> }) { return <TwoColumn list={<Cards rows={rows} titleKey="name" statusKey="is_active" detailKey="url"/>} form={<Form title="Register endpoint" action={(fd) => create({ name: fd.get("name"), url: fd.get("url"), event_keys: String(fd.get("event_keys")).split(",").map((item) => item.trim()).filter(Boolean) })}><Input name="name" label="Endpoint name"/><Input name="url" label="HTTPS destination" type="url"/><Input name="event_keys" label="Event keys" defaultValue="work_order.updated,request.created"/></Form>}/>; }

function Realtime({ data }: { data: Data }) { const events = (data.events as Data[]) ?? []; return <div className="grid gap-5 lg:grid-cols-[260px_1fr]"><aside className="panel self-start"><p className="eyebrow">Connection</p><p className="mt-4 text-2xl font-semibold capitalize">{String(data.connection_state)}</p><p className="mt-2 font-mono text-[10px] text-muted">Sequence {String(data.last_sequence)}</p><span className={`status-badge mt-4 ${data.gap_detected ? "bg-danger-soft text-danger-ink" : "bg-success-soft text-success-ink"}`}>{data.gap_detected ? "Gap detected · refetch" : "Sequence converged"}</span></aside><Cards rows={events} titleKey="event_type" statusKey="sequence" detailKey="resource_type"/></div>; }

function Bulk({ rows, create }: { rows: Data[]; create: (values: Data) => Promise<void> }) { return <TwoColumn list={<Cards rows={rows} titleKey="action_key" statusKey="status" detailKey="resource_type"/>} form={<Form title="Preview bounded operation" submit="Create preview" action={(fd) => create({ resource_type: fd.get("resource_type"), action_key: fd.get("action_key"), selection_mode: "explicit_ids", selected_ids: String(fd.get("selected_ids")).split(",").map((item) => item.trim()).filter(Boolean), action_params: {} })}><Input name="resource_type" label="Resource type" defaultValue="work_order"/><Input name="action_key" label="Action" defaultValue="export"/><Input name="selected_ids" label="Selected UUIDs, comma separated"/></Form>}/>; }

function Cards({ rows, titleKey, statusKey, detailKey }: { rows: Data[]; titleKey: string; statusKey: string; detailKey: string }) { return <PaginatedCollection items={rows} itemLabel="records">{visibleRows => <div className="grid content-start gap-px border border-line bg-line">{visibleRows.map((row, index) => <article className="bg-panel p-4" key={String(row.id ?? row.event_id ?? index)}><div className="flex items-start justify-between gap-3"><h2 className="text-sm font-bold">{String(row[titleKey] ?? `Record ${index + 1}`)}</h2><span className="variant-chip">{String(row[statusKey] ?? "")}</span></div><p className="mt-3 break-words text-xs leading-5 text-muted">{String(row[detailKey] ?? "")}</p></article>)}</div>}</PaginatedCollection>; }
function TwoColumn({ list, form }: { list: React.ReactNode; form: React.ReactNode }) { return <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">{list}{form}</div>; }
function Form({ title, action, children, submit = "Save" }: { title: string; action: (data: FormData) => void | Promise<void>; children: React.ReactNode; submit?: string }) { return <form action={action} className="panel self-start"><p className="eyebrow">{title}</p><div className="mt-5 space-y-4">{children}<button className="button-primary w-full">{submit}</button></div></form>; }
function Input({ name, label, defaultValue, type = "text" }: { name: string; label: string; defaultValue?: string; type?: string }) { return <label className="field-label">{label}<input className="control" name={name} defaultValue={defaultValue} type={type} required/></label>; }
function Runtime({ label, value }: { label: string; value: unknown }) { return <div><dt className="text-muted">{label}</dt><dd className="mt-1 break-all font-mono">{String(value ?? "—")}</dd></div>; }
