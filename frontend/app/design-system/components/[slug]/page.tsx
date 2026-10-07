import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ComponentPreview } from "@/components/design-system/component-preview";
import { Reveal } from "@/components/design-system/motion-primitives";
import { getShowcaseEntry, showcaseEntries } from "@/lib/design-system/showcase";

export function generateStaticParams() {
  return showcaseEntries.map((entry) => ({ slug: entry.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const entry = getShowcaseEntry((await params).slug);
  return entry ? { title: `${entry.name} variants | KaziLayer Design System`, description: entry.usage } : {};
}

export default async function ComponentShowcasePage({ params }: { params: Promise<{ slug: string }> }) {
  const entry = getShowcaseEntry((await params).slug);
  if (!entry) notFound();
  const variants = entry.variants.flatMap(expandVariant);
  const current = showcaseEntries.findIndex((candidate) => candidate.slug === entry.slug);
  const previous = showcaseEntries[(current - 1 + showcaseEntries.length) % showcaseEntries.length];
  const next = showcaseEntries[(current + 1) % showcaseEntries.length];

  return (
    <main className="min-h-screen bg-canvas text-ink">
      <header className="border-b border-line bg-panel">
        <div className="mx-auto max-w-[1440px] px-5 py-5 sm:px-8">
          <nav className="flex flex-wrap items-center justify-between gap-4">
            <Link className="font-heading text-sm font-bold text-primary" href="/design-system">← Design system</Link>
            <span className="font-mono text-[10px] uppercase tracking-[.12em] text-muted">{entry.kind} / {entry.group}</span>
          </nav>
        </div>
      </header>

      <div className="mx-auto max-w-[1440px] px-5 py-12 sm:px-8 lg:py-16">
        <div className="grid gap-10 border-b border-line pb-10 lg:grid-cols-[minmax(0,1.2fr)_minmax(280px,.8fr)]">
          <div>
            <span className="spec-label">{entry.classification}</span>
            <h1 className="mt-5 font-heading text-4xl font-semibold tracking-[-.05em] sm:text-6xl">{entry.name}</h1>
            <p className="mt-5 max-w-2xl text-sm leading-6 text-muted">{entry.usage}</p>
          </div>
          <div className="border-l border-line pl-5">
            <p className="spec-kicker">System role</p>
            <p className="mt-3 text-sm leading-6 text-muted">{entry.description}</p>
            <dl className="mt-6 grid grid-cols-2 gap-4">
              <div><dt className="spec-kicker">Variants</dt><dd className="mt-1 font-heading text-2xl">{variants.length}</dd></div>
              <div><dt className="spec-kicker">Theme</dt><dd className="mt-1 text-xs font-bold">70 / 20 / 10</dd></div>
            </dl>
          </div>
        </div>

        <section className="mt-14">
          <div className="flex items-end justify-between gap-4">
            <div><p className="eyebrow">Rendered component states</p><h2 className="mt-2 font-heading text-3xl font-semibold tracking-[-.04em]">Every documented variant</h2></div>
            <span className="font-mono text-[10px] text-muted">RESPONSIVE · REDUCED MOTION SAFE</span>
          </div>
          <div className="variant-gallery mt-7">
            {variants.map((variant, index) => (
              <Reveal delay={Math.min(index * .025, .15)} key={`${variant}-${index}`}>
                <article className="variant-showcase">
                  <header className="flex items-start justify-between gap-4 border-b border-line pb-4">
                    <div><span className="font-mono text-[10px] text-primary">{String(index + 1).padStart(2, "0")}</span><h3 className="mt-2 font-heading text-xl font-semibold">{variant}</h3></div>
                    <span className="spec-label">{entry.name}</span>
                  </header>
                  <VariantPresentation variant={variant}>
                    <ComponentPreview item={entry} variant={variant} />
                  </VariantPresentation>
                  <div className="mt-5 grid gap-4 border-t border-line pt-4 sm:grid-cols-3">
                    <VariantNote label="Use" text={variantUse(entry.name, variant)} />
                    <VariantNote label="Motion" text={motionNote(entry.name, variant)} />
                    <VariantNote label="Accessibility" text="Meaning remains in text, focus order and semantic state; never colour or motion alone." />
                  </div>
                </article>
              </Reveal>
            ))}
          </div>
        </section>

        <section className="mt-16 border-y border-line py-8">
          <div className="grid gap-5 sm:grid-cols-2">
            <Link className="showcase-nav" href={`/design-system/components/${previous.slug}`}><span>Previous</span><b>← {previous.name}</b></Link>
            <Link className="showcase-nav text-right" href={`/design-system/components/${next.slug}`}><span>Next</span><b>{next.name} →</b></Link>
          </div>
        </section>
      </div>
    </main>
  );
}

function VariantNote({ label, text }: { label: string; text: string }) {
  return <div><p className="spec-kicker">{label}</p><p className="mt-2 text-[11px] leading-5 text-muted">{text}</p></div>;
}

function VariantPresentation({ variant, children }: { variant: string; children: React.ReactNode }) {
  const state = variant.toLowerCase();
  const danger = /error|invalid|danger|breached|failed|rejected|conflict|deny/.test(state);
  const warning = /warning|risk|limited|stale|partial|paused/.test(state);
  const success = /success|complete|ready|saved|published|delivered|valid|allow/.test(state);
  const loading = /loading|pending|uploading|processing|running|searching|typing|executing|saving/.test(state);
  const unavailable = /disabled|hidden|unavailable|restricted|read-only|closed|idle/.test(state);
  const compact = /compact|collapsed|inline|row/.test(state);
  const spacious = /spacious|expanded|full|dashboard|cover/.test(state);
  const raised = /raised|sheet|modal|drawer/.test(state);
  const tone = danger ? "border-danger bg-danger-soft/25" : warning ? "border-warning bg-warning-soft/25" : success ? "border-success bg-success-soft/25" : "border-line bg-panel";
  const label = loading ? "IN PROGRESS" : danger ? "ATTENTION" : warning ? "MONITOR" : success ? "CONFIRMED" : unavailable ? "NON-INTERACTIVE" : "APPLIED RECIPE";

  return <div className={`relative mt-5 overflow-hidden border ${tone} ${raised ? "shadow-[0_12px_30px_rgba(17,24,39,.12)]" : ""}`}>
    <div className={`flex min-h-8 items-center justify-between gap-3 border-b px-3 font-mono text-[9px] uppercase tracking-[.1em] ${danger ? "border-danger/30 text-danger" : warning ? "border-warning/30 text-warning-ink" : success ? "border-success/30 text-success-ink" : "border-line text-primary"}`}>
      <span>{variant}</span><span>{label}</span>
    </div>
    <div className={`${compact ? "max-w-[76%]" : "w-full"} ${spacious ? "p-4 sm:p-6" : ""} ${unavailable ? "opacity-55 grayscale-[.35]" : ""}`}>{children}</div>
    <div className="flex flex-wrap gap-1.5 border-t border-line px-3 py-2">
      <span className="variant-chip">{compact ? "compact density" : spacious ? "spacious density" : "standard density"}</span>
      <span className="variant-chip">{raised ? "raised surface" : "bordered surface"}</span>
      <span className="variant-chip">{danger ? "danger tone" : warning ? "warning tone" : success ? "success tone" : "neutral tone"}</span>
    </div>
    {loading ? <span className="absolute bottom-0 left-0 h-0.5 w-2/3 animate-pulse bg-primary" /> : null}
  </div>;
}

function variantUse(name: string, variant: string) {
  return `${variant} is selected by contract metadata, responsive context or explicit recipe configuration for ${name}.`;
}

function motionNote(name: string, variant: string) {
  if (/loading|progress|typing|live|animated|uploading|searching/i.test(variant)) return `The ${variant} state uses bounded transform or opacity feedback and freezes under reduced motion.`;
  if (/Button|Action|Menu|CTA/.test(name)) return "Hover and press feedback use 1–2px travel and a 140ms mechanical response.";
  return "Static by default; local state changes use a short 240ms opacity/transform transition when helpful.";
}

function expandVariant(value: string) {
  const [prefix, rest] = value.includes(":") ? value.split(/:(.+)/) : ["", value];
  return rest.split("/").map((part) => part.trim()).filter(Boolean).map((part) => prefix ? `${prefix.trim()}: ${part}` : part);
}
