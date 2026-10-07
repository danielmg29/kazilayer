"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/accounts/api";

type Preference = { reduced_motion: boolean; density: string; contrast_mode: string; input_mode: string; large_text: boolean };

export function AccessibilityPreferences() {
  const [value, setValue] = useState<Preference | null>(null); const [notice, setNotice] = useState("");
  useEffect(() => { void apiRequest<{ preference: Preference }>("/api/v1/accessibility-preferences/").then((x) => setValue(x.preference)); }, []);
  if (!value) return <div className="panel">Loading interface preferences...</div>;
  async function save(formData: FormData) {
    const payload = { reduced_motion: formData.get("reduced_motion") === "on", large_text: formData.get("large_text") === "on", density: formData.get("density"), contrast_mode: formData.get("contrast_mode"), input_mode: formData.get("input_mode") };
    const result = await apiRequest<{ preference: Preference }>("/api/v1/accessibility-preferences/", { method: "PATCH", body: JSON.stringify(payload) }); setValue(result.preference); window.dispatchEvent(new Event("kazilayer:accessibility-updated")); setNotice("Preferences saved and applied to this workspace.");
  }
  return <div className="space-y-6"><header className="border-b border-line pb-6"><p className="eyebrow">KL-F-23</p><h1 className="mt-2 font-heading text-4xl font-semibold tracking-[-.05em]">Accessibility preferences</h1><p className="mt-3 text-sm text-muted">Personal presentation settings remain separate from operational records.</p></header>{notice ? <p role="status" className="border-l-2 border-accent bg-success-soft p-3 text-sm">{notice}</p> : null}<form action={save} className="panel grid gap-5 md:grid-cols-2"><Choice name="density" label="Interface density" value={value.density} options={["system_default", "comfortable", "compact"]}/><Choice name="contrast_mode" label="Contrast" value={value.contrast_mode} options={["system", "standard", "high"]}/><Choice name="input_mode" label="Preferred input" value={value.input_mode} options={["auto", "keyboard_first", "pointer_first", "touch_first"]}/><div className="space-y-3"><Toggle name="reduced_motion" label="Reduce nonessential motion" checked={value.reduced_motion}/><Toggle name="large_text" label="Use larger product text" checked={value.large_text}/></div><button className="button-primary md:col-span-2">Save preferences</button></form></div>;
}
function Choice({ name, label, value, options }: { name: string; label: string; value: string; options: string[] }) { return <label className="field-label">{label}<select className="control" name={name} defaultValue={value}>{options.map((x) => <option value={x} key={x}>{x.replaceAll("_", " ")}</option>)}</select></label>; }
function Toggle({ name, label, checked }: { name: string; label: string; checked: boolean }) { return <label className="flex items-center justify-between border border-line p-3 text-sm"><span>{label}</span><input type="checkbox" name={name} defaultChecked={checked}/></label>; }
