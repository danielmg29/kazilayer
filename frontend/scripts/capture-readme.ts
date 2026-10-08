import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import { chromium } from "@playwright/test";

async function main() {
  const baseUrl = "http://localhost:3000";
  const output = resolve(process.cwd(), "../docs/screenshots");
  await mkdir(output, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    executablePath: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  async function capture(name: string, url: string, heading?: string) {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 90_000 });
    if (heading) await page.getByRole("heading", { name: heading }).waitFor({ timeout: 90_000 });
    await page.waitForTimeout(2_000);
    await page.screenshot({ path: resolve(output, name), animations: "disabled" });
  }
  await capture("01-login.png", `${baseUrl}/login`);
  await page.getByLabel("Email").fill("owner@demo.kazilayer.test");
  await page.getByLabel("Password").fill("KaziLayerDemo!2026");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.waitForURL("**/meridian-field-services", { timeout: 90_000 });
  await page.waitForTimeout(2_000);
  await page.screenshot({ path: resolve(output, "02-tenant-overview.png"), animations: "disabled" });
  await capture("03-dispatch-board.png", `${baseUrl}/meridian-field-services/dispatch`, "Dispatch board");
  await capture("04-operations-dashboard.png", `${baseUrl}/meridian-field-services/dashboards`, "Operational dashboards");
  await capture("05-work-orders.png", `${baseUrl}/meridian-field-services/work-orders`, "Work lifecycle");
  await browser.close();
}

void main();
