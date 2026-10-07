import { AppShell } from "@/components/layout/app-shell";

export default async function TenantLayout({ children, params }: LayoutProps<"/[tenant]">) {
  const { tenant } = await params;
  return <AppShell tenantSlug={tenant}>{children}</AppShell>;
}
