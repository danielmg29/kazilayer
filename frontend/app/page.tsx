import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { FlowRoute, LandingProgress, LandingReveal } from "@/components/landing/landing-motion";

export const metadata: Metadata = {
  title: "KaziLayer | Keep every job moving",
  description: "Turn service requests into assigned, completed and auditable work—without losing context between the office and the field.",
};

const workflow = [
  { code: "01", title: "A request arrives", body: "Capture the problem, location, priority and evidence once. The job starts with enough context to move." },
  { code: "02", title: "The right person picks it up", body: "Dispatch sees capacity, skills and service windows in one place—then assigns with confidence." },
  { code: "03", title: "The field stays connected", body: "Technicians get the job history, add notes and attach proof without starting a parallel conversation." },
  { code: "04", title: "Nothing disappears at handover", body: "Every decision, SLA event and status change remains searchable and ready for review." },
] as const;

const audiences = [
  ["Operations leads", "See the day as it is—not as yesterday’s spreadsheet remembers it."],
  ["Dispatch teams", "Balance urgent work, technician capacity and service promises from one board."],
  ["Field teams", "Open a job and know what happened, what matters and what proof is needed."],
  ["Customers", "Follow progress without chasing the team for another status update."],
] as const;

export default function Home() {
  return (
    <main className="landing-page">
      <LandingProgress />
      <header className="landing-header">
        <Link className="landing-brand" href="/" aria-label="KaziLayer home"><Image src="/logo/logo-horizontal.svg" alt="KaziLayer — Work in one flow" width={196} height={49} priority /></Link>
        <nav className="landing-nav" aria-label="Public navigation">
          <a href="#how-it-works">How it works</a><a href="#inside">Inside KaziLayer</a><Link href="/design-system">Design system</Link><Link className="landing-login" href="/login">Log in <span aria-hidden="true">↗</span></Link>
        </nav>
      </header>

      <section className="landing-hero" aria-labelledby="hero-title">
        <div className="landing-hero-grid" aria-hidden="true" />
        <div className="landing-shell landing-hero-layout">
          <LandingReveal className="landing-hero-copy">
            <p className="landing-kicker"><span /> Operations, without the gaps</p>
            <h1 id="hero-title">Every job.<br />One clear flow.</h1>
            <p className="landing-lede">KaziLayer keeps requests, dispatch, field work and proof connected—so your team spends less time reconstructing the story and more time finishing the job.</p>
            <div className="landing-actions"><Link className="landing-button landing-button-light" href="/login">Open the demo <span aria-hidden="true">→</span></Link><a className="landing-text-link" href="#how-it-works">See the flow <span aria-hidden="true">↓</span></a></div>
          </LandingReveal>
          <LandingReveal className="landing-hero-visual" delay={0.1}>
            <div className="landing-screen-frame"><div className="landing-screen-label"><span>LIVE WORKSPACE / 02</span><span>MERIDIAN FIELD SERVICES</span></div><Image src="/product/tenant-overview.png" alt="KaziLayer tenant overview showing active operational work" width={1280} height={720} priority /></div>
            <div className="landing-signal"><span className="landing-signal-dot" /> 24 modules · one operational record</div>
          </LandingReveal>
        </div>
        <div className="landing-shell"><FlowRoute /></div>
      </section>

      <section className="landing-problem" aria-labelledby="problem-title">
        <div className="landing-shell landing-two-col">
          <LandingReveal><p className="landing-kicker landing-kicker-dark">The cost of the in-between</p><h2 id="problem-title">Work rarely breaks in the obvious place.</h2></LandingReveal>
          <LandingReveal delay={0.08} className="landing-problem-copy"><p>It breaks between the call and the ticket. Between dispatch and the technician. Between “done” and the proof that it was done.</p><p>KaziLayer closes those gaps with one shared operational layer—clear enough for the office, practical enough for the field and traceable enough for the people who need the full picture later.</p></LandingReveal>
        </div>
        <div className="landing-marquee" aria-hidden="true"><span>REQUEST</span><i /><span>ASSIGN</span><i /><span>RESOLVE</span><i /><span>VERIFY</span></div>
      </section>

      <section className="landing-workflow" id="how-it-works" aria-labelledby="workflow-title">
        <div className="landing-shell">
          <LandingReveal className="landing-section-heading"><p className="landing-kicker landing-kicker-dark">From first signal to final record</p><h2 id="workflow-title">The whole job moves together.</h2><p>No handoff theatre. Each step carries the context from the one before it.</p></LandingReveal>
          <div className="landing-workflow-grid">{workflow.map((step, index) => <LandingReveal key={step.code} delay={index * 0.05} className="landing-workflow-step"><span className="landing-step-code">{step.code}</span><span className="landing-step-node" aria-hidden="true" /><h3>{step.title}</h3><p>{step.body}</p></LandingReveal>)}</div>
        </div>
      </section>

      <section className="landing-product" id="inside" aria-labelledby="inside-title">
        <div className="landing-shell">
          <LandingReveal className="landing-product-intro"><div><p className="landing-kicker">Inside KaziLayer</p><h2 id="inside-title">A control room that still feels human.</h2></div><p>Dense when the work demands detail. Quiet when you need a decision. Every view is shaped around the next useful action.</p></LandingReveal>
          <div className="landing-product-grid">
            <LandingReveal className="landing-product-shot landing-product-shot-wide"><div className="landing-shot-caption"><span>Dispatch board</span><b>Capacity, windows and ownership in view</b></div><Image src="/product/dispatch-board.png" alt="KaziLayer dispatch board with technician lanes and assigned work" width={1280} height={720} /></LandingReveal>
            <LandingReveal className="landing-product-note" delay={0.05}><span className="landing-note-index">A / LIVE FLOW</span><strong>See pressure before it becomes a missed promise.</strong><p>Service windows, workload and assignment state stay visible without turning the screen into noise.</p></LandingReveal>
            <LandingReveal className="landing-product-shot" delay={0.08}><div className="landing-shot-caption"><span>Operations dashboard</span><b>The day, measured</b></div><Image src="/product/operations-dashboard.png" alt="KaziLayer operational dashboard showing live service measures" width={1280} height={720} /></LandingReveal>
            <LandingReveal className="landing-product-shot" delay={0.12}><div className="landing-shot-caption"><span>Work orders</span><b>The record behind every job</b></div><Image src="/product/work-orders.png" alt="KaziLayer work-order list with status and service context" width={1280} height={720} /></LandingReveal>
          </div>
        </div>
      </section>

      <section className="landing-adaptive" aria-labelledby="adaptive-title">
        <div className="landing-shell landing-adaptive-grid">
          <LandingReveal className="landing-adaptive-copy"><p className="landing-kicker landing-kicker-dark">One system, shaped to the work</p><h2 id="adaptive-title">The right view for each person. The same truth underneath.</h2><p>KaziLayer adapts what people see and can do without splitting the work into disconnected tools. Roles stay focused; the operational record stays whole.</p><Link className="landing-button landing-button-dark" href="/design-system">Explore the design system <span aria-hidden="true">→</span></Link></LandingReveal>
          <div className="landing-audience-list">{audiences.map(([title, body], index) => <LandingReveal key={title} delay={index * 0.04} className="landing-audience-row"><span>{String(index + 1).padStart(2, "0")}</span><h3>{title}</h3><p>{body}</p></LandingReveal>)}</div>
        </div>
      </section>

      <section className="landing-close" aria-labelledby="close-title">
        <div className="landing-close-grid" aria-hidden="true" />
        <div className="landing-shell landing-close-inner"><LandingReveal><p className="landing-kicker">Less chasing. More finished work.</p><h2 id="close-title">Put the next job<br />in one clear flow.</h2></LandingReveal><LandingReveal delay={0.08} className="landing-close-action"><p>The demo is already stocked with six months of work across two service organisations. Step in and see how the system behaves.</p><Link className="landing-button landing-button-mint" href="/login">Enter the KaziLayer demo <span aria-hidden="true">↗</span></Link></LandingReveal></div>
      </section>

      <footer className="landing-footer"><div className="landing-shell landing-footer-grid"><Image src="/logo/logo-horizontal.svg" alt="KaziLayer — Work in one flow" width={196} height={49} /><p>Operational work, connected from request to audit.</p><div><Link href="/design-system">Design system</Link><Link href="/login">Log in</Link></div><span>Portfolio concept · 2026</span></div></footer>
    </main>
  );
}
