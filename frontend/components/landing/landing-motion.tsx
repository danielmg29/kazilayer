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

export function LandingReveal({ children, className = "", delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  const reduced = useHydratedReducedMotion();
  return <motion.div className={className} initial={reduced ? false : { opacity: 0, y: 12 }} whileInView={reduced ? undefined : { opacity: 1, y: 0 }} viewport={{ once: true, margin: "-64px" }} transition={{ duration: 0.38, delay, ease: [0.22, 1, 0.36, 1] }}>{children}</motion.div>;
}

export function FlowRoute() {
  const reduced = useHydratedReducedMotion();
  return <div className="landing-flow" aria-label="A connected flow from request to verified work"><div className="landing-flow-line" aria-hidden="true"><motion.span animate={reduced ? undefined : { x: ["0%", "calc(100% - 12px)"] }} transition={{ duration: 5.2, repeat: Infinity, ease: "linear" }} /></div>{["Request", "Dispatch", "Field work", "Verified"].map((label, index) => <div key={label}><b>0{index + 1}</b><span>{label}</span></div>)}</div>;
}
