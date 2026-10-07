import { dynamicComponentCatalogue, type CatalogueItem } from "./catalog";

export type ShowcaseEntry = CatalogueItem & {
  slug: string;
  group: string;
  description: string;
  kind: "dynamic" | "primitive";
};

const primitiveGroups = [
  { title: "Action primitives", items: [
    ["Button", ["primary", "secondary", "quiet", "danger", "loading", "disabled"], "Submits commands and triggers permitted actions."],
    ["IconButton", ["default", "selected", "notification", "loading", "disabled"], "Compact toolbar, navigation and row actions with accessible names."],
    ["DropdownMenu", ["default", "grouped", "checked", "danger action"], "Holds lower-priority commands without hiding primary work."],
    ["Command", ["idle", "searching", "results", "no results"], "Keyboard-first navigation and relation lookup."],
    ["Tooltip", ["top", "right", "bottom", "left", "keyboard focus"], "Clarifies unfamiliar compact controls without carrying essential meaning."],
  ]},
  { title: "Form primitives", items: [
    ["Input", ["default", "focus", "filled", "error", "disabled", "read-only"], "Short text, numeric, contact and machine identifier entry."],
    ["Textarea", ["default", "focus", "filled", "error", "over limit", "disabled"], "Plain operational long text where formatting is not required."],
    ["Select", ["placeholder", "selected", "open", "error", "disabled"], "Finite contract-owned choices."],
    ["Combobox", ["empty", "searching", "results", "selected", "unavailable"], "Large or remote option sets and tenant-scoped relations."],
    ["MultiSelect", ["empty", "selected", "searching", "max selected", "disabled"], "Tags, scopes and multiple contract-owned values."],
    ["Checkbox", ["unchecked", "checked", "indeterminate", "error", "disabled"], "Independent Boolean choice and bounded bulk selection."],
    ["Switch", ["off", "on", "disabled", "loading"], "Immediate preference and feature-state toggles."],
    ["Calendar", ["month", "selected day", "range", "unavailable dates", "keyboard focus"], "Date selection for schedules, reports and service policy."],
  ]},
  { title: "Container primitives", items: [
    ["Dialog", ["standard", "wide", "form", "loading"], "Focused modal tasks that must remain in context."],
    ["AlertDialog", ["confirm", "destructive", "pending", "error"], "High-consequence confirmation before a command."],
    ["Sheet", ["right", "left", "full-height", "form"], "Contextual detail, edit and scheduling tasks."],
    ["Drawer", ["bottom", "snap", "full", "mobile filter"], "Touch-friendly narrow-screen secondary surfaces."],
    ["Tabs", ["line", "contained", "compact", "overflow"], "Switches peer views without changing record meaning."],
    ["Accordion", ["collapsed", "expanded", "multiple", "disabled"], "Progressive disclosure for dense configuration and help."],
    ["Popover", ["menu", "picker", "help", "filter"], "Anchored short-lived interaction surfaces."],
  ]},
  { title: "Data and feedback primitives", items: [
    ["Badge", ["neutral", "info", "success", "warning", "danger", "dot"], "Compact labelled metadata and status reinforcement."],
    ["Avatar", ["image", "initials", "online", "away", "overflow"], "People and collaboration identity."],
    ["Table", ["comfortable", "compact", "selectable", "sortable", "loading", "empty"], "Dense aligned operational comparisons."],
    ["ScrollArea", ["vertical", "horizontal", "both", "edge fade"], "Bounds overflow inside dense panels."],
    ["Separator", ["horizontal", "vertical", "labelled"], "Creates precise structural divisions."],
    ["Progress", ["determinate", "indeterminate", "success", "error"], "Shows bounded job, upload and workflow completion."],
    ["Skeleton", ["text", "row", "card", "stat", "chart"], "Preserves the expected content shape while loading."],
    ["Toast", ["info", "success", "warning", "danger", "action", "retry"], "Reports transient outcomes without interrupting work."],
    ["FormMessage", ["help", "error", "warning", "success"], "Connects labels, guidance and validation to controls."],
  ]},
  { title: "Layout primitives", items: [
    ["Stack", ["compact", "comfortable", "spacious", "recursive"], "Vertical rhythm for fields, panels and sections."],
    ["Cluster", ["start", "between", "center", "wrap"], "Groups actions, tags and compact metadata."],
    ["Split", ["1:1", "2:1", "3:2", "stacked"], "Main and supporting regions that collapse by container."],
    ["Grid", ["1 column", "2 columns", "3 columns", "auto-fit"], "Container-aware bento and dashboard composition."],
    ["Shell", ["public", "authenticated", "collapsed nav", "mobile"], "Provides page-wide navigation, header and content boundaries."],
  ]},
] as const;

function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

export const showcaseEntries: ShowcaseEntry[] = [
  ...dynamicComponentCatalogue.flatMap((group) => group.items.map((item) => ({ ...item, slug: `component-${slugify(item.name)}`, group: group.title, description: group.description, kind: "dynamic" as const }))),
  ...primitiveGroups.flatMap((group) => group.items.map(([name, variants, usage]) => ({ name, classification: "Primitive" as const, variants: [...variants], usage, slug: `primitive-${slugify(name)}`, group: group.title, description: "Tier-0 design-system foundation used by dynamic projections.", kind: "primitive" as const }))),
];

export const primitiveShowcaseGroups = primitiveGroups.map((group) => ({
  title: group.title,
  items: showcaseEntries.filter((entry) => entry.kind === "primitive" && entry.group === group.title),
}));

export function getShowcaseEntry(slug: string) {
  return showcaseEntries.find((entry) => entry.slug === slug);
}
