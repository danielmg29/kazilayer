import type { FieldDefinition, FieldWidget, Tone } from "./types";
import { tone as toneRecipe } from "./recipes";

type Value = string | number | boolean | readonly string[] | null | undefined;

function display(value: Value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

export function StatusBadge({ label, tone = "neutral" }: { label: string; tone?: Tone }) {
  return <span className={`status-badge ${toneRecipe[tone]}`}><span className="status-dot" />{label}</span>;
}

export function FieldView({ field, value, compact = false }: { field: FieldDefinition; value: Value; compact?: boolean }) {
  if (field.widget === "status") return <StatusBadge label={display(value)} tone={statusTone(value)} />;
  if (field.widget === "boolean") return <span className="font-medium">{display(value)}</span>;
  if (field.widget === "code") return <code className="font-mono text-xs text-primary">{display(value)}</code>;
  if (field.widget === "relative-time") return <time className="text-muted">{display(value)}</time>;
  return <span className={compact ? "truncate" : "break-words"}>{display(value)}</span>;
}

export function FieldInput({ field, value }: { field: FieldDefinition; value?: Value }) {
  const id = `field-${field.key}`;
  const common = "control";
  return <label className="field-label" htmlFor={id}>
    <span>{field.label}{field.required ? <span aria-hidden="true"> *</span> : null}</span>
    {field.widget === "textarea" || field.widget === "richtext" || field.widget === "markdown" ?
      <textarea id={id} className={`${common} min-h-28 resize-y`} defaultValue={display(value) === "—" ? "" : display(value)} /> :
      field.widget === "select" || field.widget === "status" || field.widget === "relation" ?
        <select id={id} className={common} defaultValue={typeof value === "string" ? value : ""}>
          <option value="">Select {field.label.toLowerCase()}</option>
          {field.options?.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select> :
        <input id={id} className={common} type={inputType[field.widget] ?? "text"} defaultValue={typeof value === "string" || typeof value === "number" ? value : ""} />}
    {field.help ? <small className="text-xs font-normal text-muted">{field.help}</small> : null}
  </label>;
}

export function FieldDiff({ field, before, after }: { field: FieldDefinition; before: Value; after: Value }) {
  const changed = display(before) !== display(after);
  return <div className={`grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-3 border-l-2 p-3 ${changed ? "border-warning bg-warning-soft" : "border-line"}`}>
    <FieldView field={field} value={before} /><span aria-hidden="true">→</span><FieldView field={field} value={after} />
  </div>;
}

const inputType: Partial<Record<FieldWidget, string>> = { email: "email", phone: "tel", secret: "password", integer: "number", decimal: "number", date: "date", datetime: "datetime-local", url: "url" };

function statusTone(value: Value): Tone {
  const normalized = String(value).toLowerCase();
  if (/complete|active|ready|resolved|published/.test(normalized)) return "success";
  if (/risk|pending|waiting|paused/.test(normalized)) return "warning";
  if (/breach|failed|overdue|rejected/.test(normalized)) return "danger";
  if (/scheduled|progress|draft|new/.test(normalized)) return "info";
  return "neutral";
}
