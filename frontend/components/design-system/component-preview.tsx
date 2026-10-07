"use client";

import { motion } from "motion/react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import type { CatalogueItem } from "@/lib/design-system/catalog";
import Image from "next/image";
import { useHydratedReducedMotion } from "@/components/ui/use-hydrated-reduced-motion";

const chartData = [{n:"M",v:32},{n:"T",v:46},{n:"W",v:39},{n:"T",v:61},{n:"F",v:55},{n:"S",v:74}];

export function ComponentPreview({ item, variant = "" }: { item: CatalogueItem; variant?: string }) {
  const reduced = useHydratedReducedMotion();
  const name = item.name;
  const enter = reduced ? {} : { initial: { opacity: 0, y: 5 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true }, transition: { duration: .24 } };

  if (item.classification === "Primitive") return <PrimitiveSpecimen name={name} variant={variant} />;
  if (name.startsWith("Field/")) return <FieldSpecimen name={name} variant={variant} />;
  if (/MetricWidget|StatsBlock|PerformanceProofStrip/.test(name)) return <ChartSpecimen />;
  if (/ActionBar|ActionMenu|BulkActions|ConfirmAction|MarketingCTA/.test(name)) return <ActionSpecimen name={name} variant={variant} />;
  if (/EmptyState|ErrorState|LoadingState|ToastFeedback/.test(name)) return <FeedbackSpecimen name={name} />;
  if (/AppNav|Breadcrumbs|CommandPalette|MarketingHeader|MarketingFooter/.test(name)) return <NavigationSpecimen name={name} />;
  if (/ListBlock|DetailBlock|ActivityBlock|RelatedBlock|SplitBlock|GridBlock|PageBlocks|HeaderBlock|FiltersBlock/.test(name)) return <BlockSpecimen name={name} />;
  if (/ChatBlock|CommentThreadBlock|PresenceStack|TypingIndicator|NotificationCenter/.test(name)) return <CollaborationSpecimen name={name} />;
  if (/DispatchBoardBlock|TechnicianCapacityLane|ScheduleEditorSheet|SlaIndicator/.test(name)) return <DispatchSpecimen name={name} />;
  if (/Contract|FieldDefinitionEditor|WorkflowTransitionEditor|PolicyMatrixEditor/.test(name)) return <ContractSpecimen name={name} />;
  if (/EvidenceGalleryBlock|File/.test(name)) return <EvidenceSpecimen />;
  if (/ImportWizard|ExportJobPanel|Webhook/.test(name)) return <ProgressSpecimen name={name} />;
  if (/DashboardComposerBlock|SavedViewToolbar/.test(name)) return <ComposerSpecimen name={name} />;
  if (/ConflictResolutionSheet|AuditDiffViewer/.test(name)) return <DiffSpecimen />;
  if (/SystemicPrecisionHero|LayerFlowVisualization|AdaptiveProjectionDemo|ArchitectureTraceabilityPanel|ModuleFeatureGrid|RoleOutcomeTabs/.test(name)) return <MarketingSpecimen name={name} />;
  if (/FeedbackCaptureSheet|AccessibilityPreferencesPanel/.test(name)) return <SettingsSpecimen name={name} />;

  return <motion.div className="specimen-stage" {...enter}><div className="specimen-record"><span className="specimen-icon">KL</span><div className="min-w-0 flex-1"><b>{name}</b><span>Operational record projection</span></div><span className="status-badge text-success-ink bg-success-soft"><span className="status-dot"/>Active</span></div></motion.div>;
}

function FieldSpecimen({ name, variant = "" }: { name: string; variant?: string }) {
  const type = name.slice(6);
  const state = variant.toLowerCase();
  const disabled = /disabled|unavailable|restricted/.test(state);
  const invalid = /error|invalid|over-limit|unsupported/.test(state);
  const focused = /focus|searching|editing/.test(state);
  const empty = /empty|default/.test(state);
  const readOnly = /read-only|masked view|view/.test(state) && !/preview/.test(state);
  const controlClass = `control mt-2 ${focused ? "ring-2 ring-primary ring-offset-2 ring-offset-panel" : ""} ${invalid ? "border-danger bg-danger-soft/30" : ""}`;
  const help = invalid ? (state.includes("over-limit") ? "148 / 120 characters — shorten this response." : "Check this value and try again.") : disabled ? "This field is unavailable in the current state." : readOnly ? "Read-only value from the published contract." : "Contract validation and help appear here.";
  if (type === "checkbox") { const checked = /checked/.test(state) && !/unchecked/.test(state); const indeterminate = /indeterminate/.test(state); return <Stage><label className={`flex items-center gap-3 text-xs font-semibold ${disabled ? "cursor-not-allowed opacity-50" : ""}`}><span className={`grid size-5 place-items-center border ${invalid ? "border-danger bg-danger-soft" : checked || indeterminate ? "border-primary bg-primary text-white" : "border-line bg-panel"}`}>{indeterminate ? "—" : checked ? "✓" : ""}</span><span>Include completion evidence</span></label>{invalid ? <span className="mt-2 block text-[10px] font-semibold text-danger">Select an option before continuing.</span> : null}</Stage>; }
  if (type === "switch") { const on = /on/.test(state) && !/off/.test(state); return <Stage><div className="flex items-center justify-between"><span><b className="block text-xs">Realtime updates</b><small className="text-[10px] text-muted">Notify this workspace immediately.</small></span><button className={`mini-switch ${on ? "is-on" : ""}`} aria-label={`Realtime updates ${on ? "on" : "off"}`} disabled={disabled}><span/></button></div></Stage>; }
  if (type === "calendar") { const selected = /selected|range/.test(state); return <Stage><div className={`border border-line bg-panel p-3 ${focused ? "ring-2 ring-primary ring-offset-2" : ""}`}><div className="mb-3 flex items-center justify-between text-xs font-bold"><button aria-label="Previous month">←</button><span>October 2026</span><button aria-label="Next month">→</button></div><div className="grid grid-cols-7 gap-1 text-center font-mono text-[9px]">{[1,2,3,4,5,6,7,8,9,10,11,12,13,14].map(day=><span className={`grid aspect-square place-items-center ${selected && day===6 ? "bg-primary text-white" : /unavailable/.test(state) && day>10 ? "text-faint line-through" : ""}`} key={day}>{day}</span>)}</div></div></Stage>; }
  if (type === "status") return <Stage><div className="flex flex-wrap gap-2"><Status text="Scheduled" cls="bg-primary-soft text-primary"/><Status text="At risk" cls="bg-warning-soft text-warning-ink"/><Status text="Complete" cls="bg-success-soft text-success-ink"/></div></Stage>;
  if (type === "boolean") return <Stage><div className="flex items-center justify-between"><span className="specimen-label">Evidence required</span><button className="mini-switch" aria-label="Evidence required on"><span/></button></div></Stage>;
  if (type === "multiselect") return <Stage><div className="control flex min-h-11 flex-wrap gap-1"><span className="mini-tag">HVAC ×</span><span className="mini-tag">Priority ×</span></div></Stage>;
  if (type === "file" || type === "image") return <EvidenceSpecimen/>;
  if (type === "relative-time") return <Stage><time className="text-sm font-semibold">8 minutes ago</time><span className="mt-1 block text-[10px] text-muted">05 Oct 2026 · 14:22 EAT</span></Stage>;
  if (type === "json" || type === "code" || type === "markdown") return <Stage><pre className="mini-code">{type === "json" ? '{ "state": "ready" }' : type === "markdown" ? '## Completion notes' : 'work_order.scheduled'}</pre></Stage>;
  if (type === "secret") return <Stage><label className="specimen-label">Webhook secret</label><div className="control mt-2 flex items-center justify-between"><span>••••••••••••</span><button className="text-xs font-bold text-primary">Rotate</button></div></Stage>;
  if (type === "boolean") return null;
  const select = ["select","relation","timezone","locale"].includes(type);
  const area = ["textarea","richtext"].includes(type);
  const value = empty ? "" : invalid && type === "email" ? "not-an-email" : area && state.includes("over-limit") ? "Technician confirmed the service window, documented the access constraints, recorded the replacement parts and added additional completion notes." : fieldValue(type);
  return <Stage><label className={`specimen-label ${invalid ? "text-danger" : ""}`}>{fieldLabel(type)}{invalid ? " · Error" : readOnly ? " · Read only" : ""}</label>{area ? <textarea aria-label={fieldLabel(type)} className={`${controlClass} min-h-16`} defaultValue={value || undefined} placeholder={empty ? "Add operational notes…" : undefined} disabled={disabled} readOnly={readOnly}/> : select ? <select aria-label={fieldLabel(type)} className={controlClass} defaultValue={empty ? "" : "selected"} disabled={disabled}><option value="">Choose an option</option><option value="selected">{type === "relation" ? "Amina Kamau" : "Selected option"}</option></select> : <input aria-label={fieldLabel(type)} className={controlClass} type={type === "email" ? "email" : type === "date" ? "date" : type === "datetime" ? "datetime-local" : "text"} defaultValue={value || undefined} placeholder={empty ? "Enter a value…" : undefined} disabled={disabled} readOnly={readOnly}/>}<span className={`mt-1.5 flex justify-between text-[10px] ${invalid ? "font-semibold text-danger" : "text-muted"}`}><span>{help}</span>{state.includes("over-limit") ? <b>OVER LIMIT</b> : null}</span></Stage>;
}

function ChartSpecimen(){return <Stage><div className="flex items-end justify-between"><div><span className="specimen-label">SLA within target</span><b className="mt-1 block font-heading text-2xl">93.4%</b></div><span className="text-[10px] font-bold text-success-ink">+2.8%</span></div><div className="mt-3 h-24 w-full"><ResponsiveContainer width="100%" height="100%"><AreaChart data={chartData}><defs><linearGradient id="metricFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--primary)" stopOpacity={.24}/><stop offset="1" stopColor="var(--primary)" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="var(--line)" vertical={false}/><XAxis dataKey="n" axisLine={false} tickLine={false} tick={{fill:"var(--muted)",fontSize:9}}/><Tooltip contentStyle={{background:"var(--panel)",border:"1px solid var(--line)",fontSize:10}}/><Area type="monotone" dataKey="v" stroke="var(--primary)" strokeWidth={2} fill="url(#metricFill)" isAnimationActive={false}/></AreaChart></ResponsiveContainer></div></Stage>}
function ActionSpecimen({name,variant=""}:{name:string;variant?:string}) {
  const state=variant.toLowerCase();
  const disabled=/disabled|hidden/.test(state);
  const destructive=/destructive|danger|delete/.test(state);
  const pending=/pending|executing|loading/.test(state);
  const full=/full-width/.test(state);
  const primitiveButton=name==="Button";
  const buttonClass=destructive?"button-secondary border-danger bg-danger-soft text-danger":state==="secondary"?"button-secondary":state==="quiet"?"px-2 py-2 text-xs font-bold text-primary underline-offset-4 hover:underline":"button-primary";
  return <Stage><div className={`flex flex-wrap gap-2 ${full?"grid grid-cols-1":""}`}><motion.button className={`${buttonClass} ${full?"w-full":""}`} whileTap={disabled?undefined:{scale:.96}} disabled={disabled}>{pending?"Processing…":destructive?"Archive record":state==="secondary"?"Add note":state==="quiet"?"View details":"Assign work"}</motion.button>{!primitiveButton&&!/confirm-only|primary|full-width/.test(state)?<motion.button className="button-secondary" whileHover={disabled?undefined:{y:-1}} disabled={disabled}>Add note</motion.button>:null}{/Bulk|Menu/.test(name)?<button className="icon-button" aria-label="More actions" disabled={disabled}>•••</button>:null}</div>{/Confirm/.test(name)||destructive?<p className={`mt-3 border-l-2 p-2 text-[10px] ${destructive?"border-danger bg-danger-soft text-danger":"border-warning bg-warning-soft text-warning-ink"}`}>{destructive?"This action cannot be undone.":"This transition requires confirmation."}</p>:null}</Stage>;
}
function FeedbackSpecimen({name}:{name:string}){if(name==="LoadingState")return <Stage><div className="space-y-2"><i className="skeleton-line w-2/3"/><i className="skeleton-line w-full"/><i className="skeleton-line w-1/2"/></div></Stage>;const error=name==="ErrorState";return <Stage><div className={`border-l-2 p-3 ${error?"border-danger bg-danger-soft":"border-primary bg-primary-soft"}`}><b className="text-xs">{error?"Could not update assignment":"No work matches this view"}</b><p className="mt-1 text-[10px] text-muted">{error?"Reload the current record and try again.":"Adjust filters or create a permitted record."}</p></div></Stage>}
function NavigationSpecimen({name}:{name:string}){return <Stage><div className="flex items-center gap-1 border-b border-line pb-2 text-[10px]"><b className="mr-auto text-primary">KAZILAYER</b><span>Operations</span><span className="text-faint">/</span><span>{name.replace(/([A-Z])/g," $1").trim()}</span><button className="ml-auto border border-line px-2 py-1">⌘ K</button></div></Stage>}
function BlockSpecimen({name}:{name:string}){return <Stage><div className="grid gap-2"><div className="flex items-center justify-between"><b className="text-xs">{name.replace("Block","")}</b><span className="font-mono text-[9px] text-muted">LIVE · 04</span></div>{[1,2,3].map(i=><div className="grid grid-cols-[8px_1fr_auto] items-center gap-2 border-t border-line pt-2" key={i}><span className="size-1.5 bg-primary"/><span className="h-2 bg-subtle"/><span className="text-[9px] text-muted">WO-28{i}4</span></div>)}</div></Stage>}
function CollaborationSpecimen({name}:{name:string}){return <Stage><div className="flex -space-x-1">{["AK","BM","LW"].map((x,i)=><span className="mini-avatar" style={{zIndex:3-i}} key={x}>{x}</span>)}<span className="mini-avatar bg-subtle text-muted">+4</span></div><div className="mt-3 rounded-sm bg-subtle p-2 text-[10px]"><b>Amina</b> {name==="TypingIndicator"?"is typing…":"added completion evidence."}</div></Stage>}
function DispatchSpecimen({name}:{name:string}){return <Stage><div className="grid grid-cols-3 gap-1">{[["Amina",76],["Brian",42],["Linet",91]].map(([n,v])=><div className="border border-line p-2" key={String(n)}><b className="text-[10px]">{n}</b><div className="mt-3 h-12 bg-subtle"><motion.div className="w-full bg-primary" initial={{height:0}} whileInView={{height:`${Number(v)/2}px`}} transition={{duration:.35}}/></div></div>)}</div><span className="mt-2 block text-[9px] text-muted">{name} · capacity and schedule state</span></Stage>}
function ContractSpecimen({name}:{name:string}){return <Stage><div className="grid grid-cols-[74px_1fr] gap-2"><div className="space-y-1">{["Fields","Workflow","Policy"].map((x,i)=><div className={`p-1.5 text-[9px] ${i===0?"bg-primary text-white":"bg-subtle"}`} key={x}>{x}</div>)}</div><div className="border border-line p-2"><div className="flex justify-between"><b className="text-[10px]">{name}</b><Status text="Draft" cls="bg-primary-soft text-primary"/></div><div className="mt-3 h-2 w-4/5 bg-subtle"/><div className="mt-2 h-2 w-2/3 bg-subtle"/></div></div></Stage>}
function EvidenceSpecimen(){return <Stage><div className="grid grid-cols-3 gap-2"><div className="relative col-span-2 aspect-[2/1] overflow-hidden border border-line"><Image src="/images/operations-flow-blueprint.png" alt="Abstract blueprint showing the KaziLayer operational flow" fill sizes="260px" className="object-cover"/></div><div className="aspect-square border border-line bg-subtle blueprint-grid p-2"><span className="font-mono text-[8px] text-muted">DOC.02</span></div></div><div className="mt-2 h-1 overflow-hidden bg-subtle"><motion.div className="h-full bg-accent" initial={{width:0}} whileInView={{width:"72%"}} transition={{duration:.55}}/></div></Stage>}
function ProgressSpecimen({name}:{name:string}){return <Stage><div className="flex items-center justify-between"><b className="text-xs">{name}</b><span className="text-[9px] text-muted">72%</span></div><div className="mt-3 h-1.5 bg-subtle"><motion.div className="h-full bg-primary" initial={{width:0}} whileInView={{width:"72%"}} transition={{duration:.5}}/></div><div className="mt-3 flex justify-between font-mono text-[8px] text-muted"><span>VALIDATE</span><span>PROCESS</span><span>COMPLETE</span></div></Stage>}
function ComposerSpecimen({name}:{name:string}){return <Stage><div className="grid grid-cols-3 gap-1"><div className="col-span-2 h-12 border border-primary bg-primary-soft p-2 text-[9px]">Metric / Trend</div><div className="h-12 border border-line p-2 text-[9px]">Alert</div><div className="h-8 border border-line p-2 text-[9px]">List</div><div className="col-span-2 h-8 border border-line p-2 text-[9px]">{name}</div></div></Stage>}
function DiffSpecimen(){return <Stage><div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 text-[10px]"><div className="border border-line p-2"><span className="specimen-label">Local</span><b className="mt-1 block">14:00</b></div><span>→</span><div className="border border-warning bg-warning-soft p-2"><span className="specimen-label">Server</span><b className="mt-1 block">15:30</b></div></div></Stage>}
function MarketingSpecimen({name}:{name:string}){return <Stage><div className="relative overflow-hidden bg-primary p-4 text-white blueprint-dark-grid"><span className="font-mono text-[8px] text-white/70">{name.toUpperCase()}</span><b className="mt-7 block max-w-[220px] font-heading text-lg leading-tight">One operational truth.<br/>Every role in flow.</b><motion.span className="absolute bottom-3 right-3 h-px w-20 bg-accent" initial={{scaleX:0}} whileInView={{scaleX:1}} style={{transformOrigin:"left"}}/></div></Stage>}
function SettingsSpecimen({name}:{name:string}){return <Stage><div className="space-y-3">{["Reduced motion","High contrast","Compact density"].map((x,i)=><div className="flex items-center justify-between text-[10px]" key={x}><span>{x}</span><span className={`mini-switch ${i===0?"is-on":""}`}><span/></span></div>)}</div><span className="mt-3 block text-[9px] text-muted">{name}</span></Stage>}
function PrimitiveSpecimen({name,variant=""}:{name:string;variant?:string}){
  if(/Button|DropdownMenu|Command|Tooltip/.test(name)) return <ActionSpecimen name={name} variant={variant}/>;
  if(/Input|Textarea|Select|Combobox|MultiSelect|Checkbox|Switch|Calendar/.test(name)) return <FieldSpecimen name={`Field/${name.toLowerCase()}`} variant={variant}/>;
  if(/Badge/.test(name)) return <Stage><div className="flex flex-wrap gap-2"><Status text="Neutral" cls="bg-subtle text-muted"/><Status text="At risk" cls="bg-warning-soft text-warning-ink"/><Status text="Ready" cls="bg-success-soft text-success-ink"/></div></Stage>;
  if(/Avatar/.test(name)) return <CollaborationSpecimen name={name}/>;
  if(/Progress/.test(name)) return <ProgressSpecimen name={name}/>;
  if(/Skeleton/.test(name)) return <FeedbackSpecimen name="LoadingState"/>;
  if(/Toast|FormMessage/.test(name)) return <FeedbackSpecimen name={name==="Toast"?"ToastFeedback":"ErrorState"}/>;
  if(/Table|ScrollArea|Separator/.test(name)) return <BlockSpecimen name={name}/>;
  if(/Stack|Cluster|Split|Grid|Shell/.test(name)) return <Stage><div className={`mini-layout mini-layout-${name.toLowerCase()}`}>{[1,2,3,4].map(i=><span key={i}>{i}</span>)}</div></Stage>;
  return <Stage><div className="relative min-h-24 border border-line bg-panel p-3"><b className="text-xs">{name}</b><div className="mt-3 border border-primary bg-primary-soft p-2 text-[10px]">Focused operational content</div></div></Stage>;
}
function Stage({children}:{children:React.ReactNode}){return <div className="specimen-stage">{children}</div>}
function Status({text,cls}:{text:string;cls:string}){return <span className={`status-badge ${cls}`}><span className="status-dot"/>{text}</span>}
function fieldLabel(type:string){return ({email:"Customer email",phone:"Contact phone",date:"Service date",datetime:"Preferred window",location:"Site location",url:"Webhook URL",integer:"Capacity",decimal:"SLA target"} as Record<string,string>)[type]??"Field label"}
function fieldValue(type:string){return ({email:"ops@example.com",phone:"+254 700 000 000",date:"2026-10-05",datetime:"2026-10-05T14:30",location:"Westlands, Nairobi",url:"https://hooks.example.com/work",integer:"24",decimal:"93.4"} as Record<string,string>)[type]??"Service request"}
