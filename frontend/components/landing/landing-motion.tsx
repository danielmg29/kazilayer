"use client";

import { motion, useScroll, useSpring } from "motion/react";
import type { ReactNode } from "react";
import { useHydratedReducedMotion } from "@/components/ui/use-hydrated-reduced-motion";

export function LandingProgress() {
  const reduced = useHydratedReducedMotion();
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 160, damping: 28, mass: 0.25 });
  return <motion.div className="landing-progress" style={{ scaleX: reduced ? 0 : scaleX }} aria-hidden="true" />;
}

type RevealMode = "rise" | "left" | "wipe" | "hero";

const hiddenByMode: Record<RevealMode, { opacity: number; x?: number; y?: number; scale?: number; filter?: string }> = {
  rise: { opacity: 0, y: 28 },
  left: { opacity: 0, x: -34 },
  wipe: { opacity: 0, scale: 0.965, filter: "blur(3px)" },
  hero: { opacity: 0, y: 34, filter: "blur(5px)" },
};

export function LandingReveal({ children, className = "", delay = 0, mode = "rise", immediate = false }: { children: ReactNode; className?: string; delay?: number; mode?: RevealMode; immediate?: boolean }) {
  const reduced = useHydratedReducedMotion();
  const visible = mode === "wipe" ? { opacity: 1, scale: 1, filter: "blur(0px)" } : mode === "left" ? { opacity: 1, x: 0 } : mode === "hero" ? { opacity: 1, y: 0, filter: "blur(0px)" } : { opacity: 1, y: 0 };
  return <motion.div className={className} initial={reduced ? false : hiddenByMode[mode]} animate={!reduced && immediate ? visible : undefined} whileInView={!reduced && !immediate ? visible : undefined} viewport={{ once: true, amount: 0.16 }} transition={{ duration: mode === "hero" ? 0.72 : mode === "wipe" ? 0.64 : 0.52, delay, ease: [0.22, 1, 0.36, 1] }}>{children}</motion.div>;
}

export function FlowRoute() {
  const reduced = useHydratedReducedMotion();
  return <div className="landing-flow" aria-label="A connected flow from request to verified work"><div className="landing-flow-line" aria-hidden="true"><motion.span animate={reduced ? undefined : { x: ["0%", "calc(100% - 12px)"] }} transition={{ duration: 5.2, repeat: Infinity, ease: "linear" }} /></div>{["Request", "Dispatch", "Field work", "Verified"].map((label, index) => <div key={label}><b>0{index + 1}</b><span>{label}</span></div>)}</div>;
}

const railItems = ["REQUEST", "ASSIGN", "RESOLVE", "VERIFY"] as const;

export function SignalRail() {
  const reduced = useHydratedReducedMotion();
  return <div className="landing-marquee" aria-hidden="true"><motion.div animate={reduced ? undefined : { x: ["0%", "-50%"] }} transition={{ duration: 18, repeat: Infinity, ease: "linear" }}>{[0, 1].flatMap((group) => railItems.map((item) => <span key={`${group}-${item}`}>{item}<i /></span>))}</motion.div></div>;
}
