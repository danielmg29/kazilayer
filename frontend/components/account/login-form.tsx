"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/accounts/api";

export function LoginForm() {
  const router = useRouter();
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
    <section className="flex items-center justify-center px-6 py-12"><div className="w-full max-w-md"><Image src="/logo/logo-horizontal.svg" alt="KaziLayer — Work in one flow" width={200} height={50} priority/><p className="eyebrow mt-14">Secure workspace access</p><h1 className="mt-3 font-heading text-4xl font-semibold tracking-[-.05em]">Sign in to operations.</h1><p className="mt-4 text-sm leading-6 text-muted">Your organisation, role policy and allowed actions are resolved after authentication.</p><form action={submit} className="mt-9 space-y-5"><label className="field-label">Email<input className="control" name="email" type="email" defaultValue="owner@demo.kazilayer.test" autoComplete="email" required/></label><label className="field-label">Password<input className="control" name="password" type="password" defaultValue="KaziLayerDemo!2026" autoComplete="current-password" required/></label>{needsMfa?<label className="field-label">Authenticator code<input className="control font-mono tracking-[.25em]" name="mfa_code" inputMode="numeric" pattern="[0-9]{6}" maxLength={6} required/></label>:null}{message?<p className="border-l-2 border-danger bg-danger-soft p-3 text-xs text-danger-ink" role="alert">{message}</p>:null}<button className="button-primary w-full" disabled={pending}>{pending?"Signing in…":"Sign in"}</button></form><div className="mt-5 flex items-center justify-between text-xs"><Link className="font-semibold text-primary" href="/password-reset">Forgot password?</Link><span className="text-muted">Demo: <code className="font-mono text-ink">KaziLayerDemo!2026</code></span></div></div></section>
    <aside className="relative hidden overflow-hidden bg-primary p-12 text-white blueprint-dark-grid lg:flex lg:flex-col lg:justify-between"><span className="font-mono text-xs tracking-[.14em] text-white/70">KL / IDENTITY LAYER</span><div><p className="max-w-xl font-heading text-5xl font-medium leading-[1.02] tracking-[-.055em]">One identity.<br/>Every tenant boundary intact.</p><div className="mt-12 grid grid-cols-2 gap-px bg-white/20"><div className="bg-primary p-5"><span className="font-mono text-[10px] text-white/60">AUTH</span><p className="mt-8 text-sm">Cookie sessions, revocation and MFA.</p></div><div className="bg-primary p-5"><span className="font-mono text-[10px] text-white/60">POLICY</span><p className="mt-8 text-sm">Server-projected roles and actions.</p></div></div></div><span className="h-px w-full bg-accent"/></aside>
  </main>;
}
