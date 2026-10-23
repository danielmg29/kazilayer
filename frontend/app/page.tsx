import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { FlowRoute, LandingProgress, LandingReveal, SignalRail } from "@/components/landing/landing-motion";

export const metadata: Metadata = {
  title: "KaziLayer | Service operations software",
  description: "Manage customer requests, technician dispatch, service deadlines and proof of work in one shared system.",
};

const workflow = [
  { code: "01", title: "Capture the customer request", body: "Record the issue, location, priority and photos once. Everyone starts with the same information." },
  { code: "02", title: "Assign the right technician", body: "Dispatch compares availability, skills and service deadlines before assigning the job." },
  { code: "03", title: "Track work in the field", body: "Technicians see instructions, update progress and attach proof from one job record." },
  { code: "04", title: "Confirm the work is complete", body: "Managers review timestamps, evidence, customer feedback and the full audit trail." },
] as const;

const audiences = [
  ["Operations managers", "See workload, overdue jobs and service performance without rebuilding reports."],
  ["Dispatch teams", "Assign urgent work while protecting technician capacity and customer deadlines."],
  ["Field technicians", "Open each job with the history, instructions and proof requirements already attached."],
  ["Customers", "Receive clear progress updates without calling your team for another status check."],
] as const;

export default function Home() {
  return (
    <main className="landing-page">
      <LandingProgress />
      <header className="landing-header">
        <Link className="landing-brand" href="/" aria-label="KaziLayer home"><Image src="/logo/logo-mark.svg" alt="" width={44} height={44} priority /><span><b>KaziLayer</b><small>Work in one flow</small></span></Link>
        <nav className="landing-nav" aria-label="Public navigation">
          <a href="#how-it-works">How it works</a><a href="#inside">Inside KaziLayer</a><Link href="/design-system">Design system</Link><Link className="landing-login" href="/login">Log in <span aria-hidden="true">↗</span></Link>
        </nav>
      </header>

      <section className="landing-hero" aria-labelledby="hero-title">
        <div className="landing-hero-grid" aria-hidden="true" />
        <div className="landing-shell landing-hero-layout">
          <LandingReveal className="landing-hero-copy" mode="hero" immediate>
            <p className="landing-kicker"><span /> Service operations software</p>
            <h1 id="hero-title"><span>Manage service jobs.</span><span>From request to proof.</span></h1>
            <p className="landing-lede">KaziLayer gives your service team one place to receive customer requests, dispatch technicians, track deadlines and confirm completed work.</p>
            <div className="landing-actions"><Link className="landing-button landing-button-light" href="/login">See KaziLayer in action <span aria-hidden="true">→</span></Link><a className="landing-text-link" href="#how-it-works">How it works <span aria-hidden="true">↓</span></a></div>
          </LandingReveal>
          <LandingReveal className="landing-hero-visual" delay={0.14} mode="wipe" immediate>
            <div className="landing-screen-frame"><div className="landing-screen-label"><span>LIVE WORKSPACE / 02</span><span>MERIDIAN FIELD SERVICES</span></div><Image src="/product/tenant-overview.png" alt="KaziLayer tenant overview showing active operational work" width={1280} height={720} priority /></div>
            <div className="landing-signal"><span className="landing-signal-dot" /> 24 modules · one operational record</div>
          </LandingReveal>
        </div>
        <div className="landing-shell"><FlowRoute /></div>
      </section>

      <section className="landing-problem" aria-labelledby="problem-title">
        <div className="landing-shell landing-two-col">
          <LandingReveal><p className="landing-kicker landing-kicker-dark">One job should not need four tools</p><h2 id="problem-title">Stop piecing service work together from calls, chats and spreadsheets.</h2></LandingReveal>
          <LandingReveal delay={0.08} className="landing-problem-copy"><p>When job details live in different places, dispatch misses context, technicians repeat questions and customers wait for answers.</p><p>KaziLayer keeps the request, assignment, deadline, conversation and proof of work together. Your team can see what happened and what needs to happen next.</p></LandingReveal>
        </div>
        <SignalRail />
      </section>

      <section className="landing-workflow" id="how-it-works" aria-labelledby="workflow-title">
        <div className="landing-shell">
          <LandingReveal className="landing-section-heading"><p className="landing-kicker landing-kicker-dark">How KaziLayer works</p><h2 id="workflow-title">One workflow from customer request to verified completion.</h2><p>Each update stays on the job, so the office and field team always work from the same record.</p></LandingReveal>
          <div className="landing-workflow-grid">{workflow.map((step, index) => <LandingReveal key={step.code} delay={index * 0.05} className="landing-workflow-step"><span className="landing-step-code">{step.code}</span><span className="landing-step-node" aria-hidden="true" /><h3>{step.title}</h3><p>{step.body}</p></LandingReveal>)}</div>
        </div>
      </section>

      <section className="landing-product" id="inside" aria-labelledby="inside-title">
        <div className="landing-shell">
          <LandingReveal className="landing-product-intro"><div><p className="landing-kicker">See the operation clearly</p><h2 id="inside-title">Know what is happening across every job.</h2></div><p>Review technician capacity, active work, service deadlines and completed evidence without waiting for a status meeting.</p></LandingReveal>
          <div className="landing-product-grid">
            <LandingReveal className="landing-product-shot landing-product-shot-wide" mode="wipe"><div className="landing-shot-caption"><span>Dispatch board</span><b>Capacity, windows and ownership in view</b></div><Image src="/product/dispatch-board.png" alt="KaziLayer dispatch board with technician lanes and assigned work" width={1280} height={720} /></LandingReveal>
            <LandingReveal className="landing-product-note" delay={0.05}><span className="landing-note-index">A / LIVE DISPATCH</span><strong>Catch overloaded schedules before customers feel the delay.</strong><p>Compare technician capacity, job priority and service windows before you assign more work.</p></LandingReveal>
            <LandingReveal className="landing-product-shot" delay={0.08} mode="wipe"><div className="landing-shot-caption"><span>Operations dashboard</span><b>The day, measured</b></div><Image src="/product/operations-dashboard.png" alt="KaziLayer operational dashboard showing live service measures" width={1280} height={720} /></LandingReveal>
            <LandingReveal className="landing-product-shot" delay={0.12} mode="wipe"><div className="landing-shot-caption"><span>Work orders</span><b>The record behind every job</b></div><Image src="/product/work-orders.png" alt="KaziLayer work-order list with status and service context" width={1280} height={720} /></LandingReveal>
          </div>
        </div>
      </section>

      <section className="landing-adaptive" aria-labelledby="adaptive-title">
        <div className="landing-shell landing-adaptive-grid">
          <LandingReveal className="landing-adaptive-copy"><p className="landing-kicker landing-kicker-dark">Built for the whole service team</p><h2 id="adaptive-title">Give each person the view they need.</h2><p>Managers, dispatchers, technicians and customers see the information that matters to them. Permissions protect sensitive work while every update stays connected.</p><Link className="landing-button landing-button-dark" href="/login">Explore the working demo <span aria-hidden="true">→</span></Link></LandingReveal>
          <div className="landing-audience-list">{audiences.map(([title, body], index) => <LandingReveal key={title} delay={index * 0.04} mode="left" className="landing-audience-row"><span>{String(index + 1).padStart(2, "0")}</span><h3>{title}</h3><p>{body}</p></LandingReveal>)}</div>
        </div>
      </section>

      <section className="landing-close" id="demo" aria-labelledby="close-title">
        <div className="landing-close-grid" aria-hidden="true" />
        <div className="landing-shell landing-close-inner"><LandingReveal><p className="landing-kicker">Explore a working service operation</p><h2 id="close-title">See KaziLayer with real work already loaded.</h2></LandingReveal><LandingReveal delay={0.08} className="landing-close-action"><p>The demo includes six months of requests, work orders, dispatch activity, service deadlines and customer feedback across two organisations.</p><div className="landing-close-meta"><span>Dispatch</span><span>SLA tracking</span><span>Proof of work</span></div><Link className="landing-button landing-button-mint" href="/login">Open the KaziLayer demo <span aria-hidden="true">↗</span></Link></LandingReveal></div>
      </section>

      <footer className="landing-footer"><div className="landing-shell landing-footer-grid"><div className="landing-footer-brand"><Image src="/logo/logo-mark.svg" alt="" width={40} height={40} /><span><b>KaziLayer</b><small>Work in one flow</small></span></div><p>Operational work, connected from request to audit.</p><div><Link href="/design-system">Design system</Link><Link href="/login">Log in</Link></div><span>Portfolio concept · 2026</span></div></footer>
    </main>
  );
}
