import { notFound } from "next/navigation";
import { AccountWorkspace } from "@/components/account/account-workspace";
import { SessionPanel } from "@/components/account/session-panel";
import { OperationsWorkspace, type OperationsSection } from "@/components/operations/operations-workspace";
import { ConvergenceWorkspace, type ConvergenceSection } from "@/components/convergence/convergence-workspace";

const accountSections = ["members", "roles", "saved-views", "settings", "profile"] as const;
const operationsSections = ["feedback", "requests", "comments", "files", "search", "data-jobs", "audit", "work-orders", "notifications"] as const;
const convergenceSections = ["contracts", "dynamic-forms", "adaptive-views", "dashboards", "integrations", "realtime", "bulk-operations"] as const;

export default async function TenantSection({ params }: PageProps<"/[tenant]/[section]">) {
  const { tenant, section } = await params;
  if (operationsSections.includes(section as OperationsSection)) return <OperationsWorkspace tenantSlug={tenant} section={section as OperationsSection}/>;
  if (convergenceSections.includes(section as ConvergenceSection)) return <ConvergenceWorkspace tenantSlug={tenant} section={section as ConvergenceSection}/>;
  if (!accountSections.includes(section as (typeof accountSections)[number])) notFound();
  return <><AccountWorkspace tenantSlug={tenant} view={section as (typeof accountSections)[number]}/>{section === "profile" ? <SessionPanel /> : null}</>;
}
