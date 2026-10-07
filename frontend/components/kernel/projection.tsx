import type { Density, Intent, ProjectionSlots, Surface, Tone } from "./types";
import { recipe } from "./recipes";
import { MotionButton, MotionSurface } from "@/components/ui/motion";

export function Projection({ slots, intent = "card", density = "comfortable", surface = "bordered", tone = "neutral" }: { slots: ProjectionSlots; intent?: Intent; density?: Density; surface?: Surface; tone?: Tone }) {
  return <MotionSurface className={`projection ${recipe(density, surface)}`}><article className="contents" data-intent={intent} data-tone={tone}>
    {slots.media ? <div className="projection-media">{slots.media}</div> : null}
    <div className="min-w-0 flex-1">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0"><h3 className="projection-title">{slots.title}</h3>{slots.subtitle ? <p className="projection-subtitle">{slots.subtitle}</p> : null}</div>
        {slots.badge}
      </div>
      {slots.meta ? <div className="projection-meta">{slots.meta}</div> : null}
      {(slots.owner || slots.timestamp || slots.actions) ? <footer className="projection-footer"><span>{slots.owner}</span><span>{slots.timestamp}</span>{slots.actions}</footer> : null}
    </div>
  </article></MotionSurface>;
}

export function ActionBar({ actions }: { actions: readonly { key: string; label: string; enabled?: boolean }[] }) {
  return <div className="flex flex-wrap gap-2" aria-label="Available actions">{actions.map((action, index) => <MotionButton className={index === 0 ? "button-primary" : "button-secondary"} disabled={action.enabled === false} key={action.key}>{action.label}</MotionButton>)}</div>;
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return <div className="border border-dashed border-line p-8 text-center"><p className="font-heading text-lg font-semibold">{title}</p><p className="mt-2 text-sm text-muted">{detail}</p></div>;
}

export function ErrorState({ title, detail }: { title: string; detail: string }) {
  return <div className="border-l-2 border-danger bg-danger-soft p-4" role="alert"><p className="font-semibold text-danger-ink">{title}</p><p className="mt-1 text-sm text-muted">{detail}</p></div>;
}

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return <div className="space-y-2" aria-label={label} aria-busy="true"><div className="h-3 w-2/3 animate-pulse bg-line"/><div className="h-3 w-full animate-pulse bg-line"/><div className="h-3 w-1/2 animate-pulse bg-line"/></div>;
}
