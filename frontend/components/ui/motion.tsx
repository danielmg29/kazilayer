"use client";

import { motion } from "motion/react";
import type { ComponentProps, ReactNode } from "react";
import { useHydratedReducedMotion } from "./use-hydrated-reduced-motion";

export function MotionButton({ children, className = "", ...props }: ComponentProps<typeof motion.button>) {
  const reduced = useHydratedReducedMotion();
  return <motion.button className={className} whileHover={props.disabled || reduced ? undefined : { y: -1 }} whileTap={props.disabled || reduced ? undefined : { scale: .975 }} transition={{ duration: .14, ease: [.22, 1, .36, 1] }} {...props}>{children}</motion.button>;
}

export function MotionSurface({ children, className = "" }: { children: ReactNode; className?: string }) {
  const reduced = useHydratedReducedMotion();
  return <motion.div className={className} whileHover={reduced ? undefined : { x: 2 }} transition={{ duration: .16, ease: [.22, 1, .36, 1] }}>{children}</motion.div>;
}
