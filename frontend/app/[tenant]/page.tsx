import { AccountWorkspace } from "@/components/account/account-workspace";

export default async function TenantOverview({ params }: PageProps<"/[tenant]">) {
  const { tenant } = await params;
  return <AccountWorkspace tenantSlug={tenant} view="overview"/>;
}
