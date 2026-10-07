import type { ReactNode } from "react";

export type Density = "compact" | "comfortable" | "spacious";
export type Tone = "neutral" | "info" | "success" | "warning" | "danger";
export type Surface = "flat" | "bordered" | "raised" | "inset";
export type Intent = "row" | "card" | "detail" | "stat" | "media" | "relation" | "audit" | "thread";

export type FieldWidget =
  | "text" | "textarea" | "richtext" | "markdown" | "email" | "phone" | "secret"
  | "select" | "status" | "multiselect" | "relation" | "integer" | "decimal"
  | "boolean" | "date" | "datetime" | "relative-time" | "file" | "image" | "url"
  | "code" | "location" | "timezone" | "locale" | "json";

export type FieldDefinition = {
  key: string;
  label: string;
  widget: FieldWidget;
  help?: string;
  required?: boolean;
  options?: readonly { label: string; value: string }[];
};

export type ActionDefinition = {
  key: string;
  label: string;
  tone?: Tone;
  enabled?: boolean;
};

export type ProjectionSlots = {
  title: ReactNode;
  subtitle?: ReactNode;
  badge?: ReactNode;
  media?: ReactNode;
  meta?: ReactNode;
  timestamp?: ReactNode;
  owner?: ReactNode;
  actions?: ReactNode;
};
