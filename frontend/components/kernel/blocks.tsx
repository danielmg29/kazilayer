import type { ReactNode } from "react";
import { Projection } from "./projection";
import { StatusBadge } from "./fields";
import type { Tone } from "./types";

export function HeaderBlock({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: string; actions?: ReactNode }) {
  return <header className="flex flex-col justify-between gap-4 border-b border-line pb-5 md:flex-row md:items-end"><div><p className="eyebrow">{eyebrow}</p><h1 className="mt-2 max-w-3xl font-heading text-3xl font-semibold tracking-[-0.04em] text-ink md:text-4xl">{title}</h1>{description ? <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">{description}</p> : null}</div>{actions}</header>;
}

export function StatsBlock({ items }: { items: readonly { label: string; value: string; delta?: string; tone?: Tone; code: string }[] }) {
  return <section className="grid gap-px border border-line bg-line sm:grid-cols-2 xl:grid-cols-4" aria-label="Operational metrics">{items.map((item) => <article className="bg-panel p-5" key={item.code}><div className="flex items-start justify-between gap-3"><p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">{item.label}</p><span className="font-mono text-[10px] text-faint">{item.code}</span></div><p className="mt-7 font-heading text-4xl font-medium tracking-[-0.055em] text-ink">{item.value}</p>{item.delta ? <p className="mt-3 text-xs text-muted">{item.delta}</p> : null}</article>)}</section>;
}

export function ListBlock({ title, items }: { title: string; items: readonly { id: string; title: string; subtitle: string; status: string; meta: string; tone?: Tone }[] }) {
  return <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Live queue</p><h2 className="section-title">{title}</h2></div><button className="button-quiet">View all <span aria-hidden="true">↗</span></button></div><div className="divide-y divide-line">{items.map((item) => <Projection key={item.id} intent="row" surface="flat" density="compact" slots={{title:item.title, subtitle:item.subtitle, badge:<StatusBadge label={item.status} tone={item.tone}/>, meta:<span>{item.meta}</span>, timestamp:<span className="font-mono text-[11px] text-faint">{item.id}</span>}} />)}</div></section>;
}

export function ActivityBlock({ events }: { events: readonly { id: string; title: string; detail: string; time: string }[] }) {
  return <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Audit stream</p><h2 className="section-title">Recent activity</h2></div><span className="live-label"><span/>Live</span></div><ol>{events.map((event, index) => <li className="grid grid-cols-[18px_minmax(0,1fr)] gap-3" key={event.id}><div className="flex flex-col items-center"><span className="mt-1.5 size-2 border-2 border-primary bg-panel"/>{index < events.length - 1 ? <span className="w-px flex-1 bg-line"/> : null}</div><div className="pb-5"><div className="flex justify-between gap-3"><p className="text-sm font-semibold text-ink">{event.title}</p><time className="shrink-0 font-mono text-[10px] text-faint">{event.time}</time></div><p className="mt-1 text-xs leading-5 text-muted">{event.detail}</p></div></li>)}</ol></section>;
}

export function SlaFlowBlock() {
  const points = [{x:8,h:34},{x:23,h:51},{x:38,h:42},{x:53,h:68},{x:68,h:56},{x:83,h:77}];
  return <section className="panel blueprint-panel"><div className="panel-heading"><div><p className="eyebrow">Flow telemetry</p><h2 className="section-title">SLA control line</h2></div><StatusBadge label="93.4% within target" tone="success"/></div><div className="relative mt-6 h-52 overflow-hidden border-l border-b border-grid" aria-label="SLA trend chart"><div className="absolute inset-0 blueprint-grid"/><svg className="absolute inset-0 h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label="Service level trend rising across six periods"><polyline points={points.map(p=>`${p.x},${100-p.h}`).join(" ")} fill="none" stroke="var(--primary)" strokeWidth="1.4" vectorEffect="non-scaling-stroke"/>{points.map((p,i)=><g key={p.x}><line x1={p.x} y1={100-p.h} x2={p.x} y2="100" stroke="var(--line)" strokeWidth="1" vectorEffect="non-scaling-stroke"/><circle cx={p.x} cy={100-p.h} r="1.2" fill={i===points.length-1?"var(--accent)":"var(--primary)"}/></g>)}</svg><div className="absolute bottom-2 left-3 font-mono text-[10px] uppercase tracking-widest text-faint">06:00</div><div className="absolute right-3 top-2 font-mono text-[10px] uppercase tracking-widest text-faint">18:00</div></div></section>;
}

export function CapacityBlock() {
  const rows=[{name:"Amina K.",load:72,status:"On site"},{name:"Brian M.",load:48,status:"Available"},{name:"Linet W.",load:88,status:"Travel"},{name:"Peter O.",load:31,status:"Available"}];
  return <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Dispatch</p><h2 className="section-title">Technician capacity</h2></div><button className="button-quiet">Open board ↗</button></div><div className="space-y-4">{rows.map(row=><div key={row.name}><div className="mb-1.5 flex items-center justify-between text-xs"><span className="font-semibold text-ink">{row.name}</span><span className="text-muted">{row.status} · {row.load}%</span></div><div className="h-1.5 bg-subtle"><div className="h-full bg-primary" style={{width:`${row.load}%`}}/></div></div>)}</div></section>;
}
