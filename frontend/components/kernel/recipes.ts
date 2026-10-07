import type { Density, Surface, Tone } from "./types";

const density = {
  compact: "p-3 gap-2",
  comfortable: "p-4 gap-3",
  spacious: "p-6 gap-5",
} satisfies Record<Density, string>;

const surface = {
  flat: "bg-transparent",
  bordered: "border border-line bg-panel",
  raised: "border border-line bg-panel shadow-[0_12px_32px_-24px_rgb(17_24_39/0.35)]",
  inset: "border border-line bg-subtle",
} satisfies Record<Surface, string>;

export const tone = {
  neutral: "text-ink bg-subtle",
  info: "text-primary bg-primary-soft",
  success: "text-success-ink bg-success-soft",
  warning: "text-warning-ink bg-warning-soft",
  danger: "text-danger-ink bg-danger-soft",
} satisfies Record<Tone, string>;

export function recipe(d: Density = "comfortable", s: Surface = "bordered") {
  return `${density[d]} ${surface[s]}`;
}
