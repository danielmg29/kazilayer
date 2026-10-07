"use client";

import { motion } from "motion/react";
import type { ReactNode } from "react";
import { useHydratedReducedMotion } from "@/components/ui/use-hydrated-reduced-motion";

export function Reveal({ children, delay = 0, className = "" }: { children: ReactNode; delay?: number; className?: string }) {
  const reduced = useHydratedReducedMotion();
  return <motion.div className={className} initial={reduced ? false : { opacity: 0, y: 12 }} whileInView={reduced ? undefined : { opacity: 1, y: 0 }} viewport={{ once: true, margin: "-40px" }} transition={{ duration: .38, delay, ease: [.22, 1, .36, 1] }}>{children}</motion.div>;
}

export function InteractiveSpecimen({ children, className = "" }: { children: ReactNode; className?: string }) {
  const reduced = useHydratedReducedMotion();
  return <motion.div className={className} whileHover={reduced ? undefined : { y: -2 }} whileTap={reduced ? undefined : { scale: .995 }} transition={{ duration: .16, ease: [.22, 1, .36, 1] }}>{children}</motion.div>;
}

export function FlowLine() {
  const reduced = useHydratedReducedMotion();
  return <div className="relative h-20 overflow-hidden border border-line bg-primary blueprint-dark-grid" aria-label="Animated flow from request to audit">
    <svg className="absolute inset-0 h-full w-full" viewBox="0 0 600 80" preserveAspectRatio="none" aria-hidden="true"><path d="M24 40 H150 C180 40 180 20 210 20 H355 C385 20 385 58 415 58 H576" fill="none" stroke="rgba(255,255,255,.34)" strokeWidth="1"/><motion.path d="M24 40 H150 C180 40 180 20 210 20 H355 C385 20 385 58 415 58 H576" fill="none" stroke="var(--accent)" strokeWidth="2" strokeDasharray="34 520" initial={{ strokeDashoffset: 554 }} animate={reduced ? { strokeDashoffset: 0 } : { strokeDashoffset: [554, -554] }} transition={reduced ? { duration: 0 } : { duration: 4.8, repeat: Infinity, ease: "linear" }}/></svg>
    <div className="absolute inset-0 flex items-center justify-between px-5 font-mono text-[10px] uppercase tracking-[.12em] text-white"><span>Request</span><span>Dispatch</span><span>Field work</span><span>Audit</span></div>
  </div>;
}
