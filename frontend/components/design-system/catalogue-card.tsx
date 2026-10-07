import type { CatalogueItem } from "@/lib/design-system/catalog";
import { InteractiveSpecimen } from "./motion-primitives";
import { ComponentPreview } from "./component-preview";
import Link from "next/link";
import { showcaseEntries } from "@/lib/design-system/showcase";

export function CatalogueCard({ item, index }: { item: CatalogueItem; index: number }) {
  const entry = showcaseEntries.find((candidate) => candidate.name === item.name && candidate.classification === item.classification);
  return <InteractiveSpecimen className="h-full"><article className="catalogue-card group relative h-full"><Link className="absolute inset-0 z-10" href={`/design-system/components/${entry?.slug ?? ""}`} aria-label={`View every ${item.name} variant`}/><header className="flex items-start justify-between gap-3"><div><p className="font-mono text-[10px] text-faint">{String(index + 1).padStart(2, "0")}</p><h3 className="mt-2 font-heading text-lg font-semibold tracking-[-.025em] text-ink">{item.name}</h3></div><span className="spec-label">{item.classification}</span></header><div className="pointer-events-none" inert><ComponentPreview item={item}/></div><div className="mt-5"><p className="spec-kicker">Variants and states</p><div className="mt-2 flex flex-wrap gap-1.5">{item.variants.slice(0, 4).map((variant) => <span className="variant-chip" key={variant}>{variant}</span>)}</div></div><div className="mt-5 border-t border-line pt-4"><p className="spec-kicker">Used in KaziLayer</p><p className="mt-2 text-xs leading-5 text-muted">{item.usage}</p><span className="mt-4 inline-flex text-xs font-bold text-primary">View all {item.variants.length} variants <span className="ml-2 transition-transform group-hover:translate-x-1">→</span></span></div></article></InteractiveSpecimen>;
}
