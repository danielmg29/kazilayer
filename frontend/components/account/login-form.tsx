"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiRequest } from "@/lib/accounts/api";

const demoAccounts = [
  { email: "owner@demo.kazilayer.test", role: "Organisation owner" },
  { email: "dispatcher@demo.kazilayer.test", role: "Dispatcher" },
  { email: "technician@demo.kazilayer.test", role: "Technician" },
  { email: "customer@demo.kazilayer.test", role: "Customer contact" },
  { email: "auditor@demo.kazilayer.test", role: "Auditor" },
];

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState(demoAccounts[0].email);
  const [message, setMessage] = useState("");
  const [needsMfa, setNeedsMfa] = useState(false);
  const [pending, setPending] = useState(false);

  async function submit(formData: FormData) {
    setPending(true); setMessage("");
    try {
      await apiRequest("/api/v1/auth/login/", { method: "POST", body: JSON.stringify({ email: formData.get("email"), password: formData.get("password"), mfa_code: formData.get("mfa_code"), device_label: navigator.userAgent.includes("Mobile") ? "Mobile browser" : "Desktop browser" }) });
      router.push("/meridian-field-services");
    } catch (error) {
      const text = error instanceof Error ? error.message : "Sign-in failed";
      setNeedsMfa(text.toLowerCase().includes("authenticator")); setMessage(text);
    } finally { setPending(false); }
  }

  return <main className="grid min-h-screen bg-canvas lg:grid-cols-[1fr_1.05fr]">
    <section className="flex items-center justify-center px-6 py-10"><div className="w-full max-w-xl"><Image src="/logo/logo-horizontal.svg" alt="KaziLayer - Work in one flow" width={200} height={50} priority/><p className="eyebrow mt-9">Secure workspace access</p><h1 className="mt-3 font-heading text-4xl font-semibold tracking-[-.05em]">Sign in to operations.</h1><p className="mt-3 text-sm leading-6 text-muted">Your organisation, role policy and allowed actions are resolved after authentication.</p><form action={submit} className="mt-6 space-y-4"><label className="field-label">Email<input className="control" name="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" required/></label><label className="field-label">Password<input className="control" name="password" type="password" defaultValue="KaziLayerDemo!2026" autoComplete="current-password" required/></label>{needsMfa?<label className="field-label">Authenticator code<input className="control font-mono tracking-[.25em]" name="mfa_code" inputMode="numeric" pattern="[0-9]{6}" maxLength={6} required/></label>:null}{message?<p className="border-l-2 border-danger bg-danger-soft p-3 text-xs text-danger-ink" role="alert">{message}</p>:null}<button className="button-primary w-full" disabled={pending}>{pending?"Signing in...":"Sign in"}</button></form><div className="mt-4 flex items-center justify-between text-xs"><Link className="font-semibold text-primary" href="/password-reset">Forgot password?</Link><span className="text-muted">Password: <code className="font-mono text-ink">KaziLayerDemo!2026</code></span></div><div className="mt-5 border-t border-line pt-4"><div className="flex items-center justify-between"><p className="eyebrow">Demo accounts</p><span className="font-mono text-[9px] uppercase text-muted">Both demo tenants</span></div><div className="mt-3 grid gap-px border border-line bg-line sm:grid-cols-2">{demoAccounts.map((account) => <button key={account.email} type="button" onClick={() => setEmail(account.email)} className={`bg-panel p-3 text-left transition-colors hover:bg-subtle ${email === account.email ? "outline-2 -outline-offset-2 outline-accent" : ""}`}><b className="block text-xs">{account.role}</b><span className="mt-1 block break-all font-mono text-[9px] text-muted">{account.email}</span><span className="mt-2 block text-[9px] text-primary">Meridian · Rift Valley</span></button>)}</div></div></div></section>
    <aside className="relative hidden overflow-hidden bg-primary p-12 text-white blueprint-dark-grid lg:flex lg:flex-col lg:justify-between"><span className="font-mono text-xs tracking-[.14em] text-white/70">KL / IDENTITY LAYER</span><div><p className="max-w-xl font-heading text-5xl font-medium leading-[1.02] tracking-[-.055em]">One identity.<br/>Every tenant boundary intact.</p><div className="mt-12 grid grid-cols-2 gap-px bg-white/20"><div className="bg-primary p-5"><span className="font-mono text-[10px] text-white/60">AUTH</span><p className="mt-8 text-sm">Cookie sessions, revocation and MFA.</p></div><div className="bg-primary p-5"><span className="font-mono text-[10px] text-white/60">POLICY</span><p className="mt-8 text-sm">Server-projected roles and actions.</p></div></div></div><span className="h-px w-full bg-accent"/></aside>
  </main>;
}
