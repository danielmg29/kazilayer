"use client";

import Link from "next/link";
import { useState } from "react";
import { apiRequest } from "@/lib/accounts/api";

export function PasswordReset() {
  const [message, setMessage] = useState("");

  async function requestReset(formData: FormData) {
    const result = await apiRequest<{ message: string }>("/api/v1/auth/password-reset/request/", {
      method: "POST",
      body: JSON.stringify({ email: formData.get("email") }),
    });
    setMessage(result.message);
  }

  async function confirmReset(formData: FormData) {
    try {
      await apiRequest<{ ok: boolean }>("/api/v1/auth/password-reset/confirm/", {
        method: "POST",
        body: JSON.stringify({ token: formData.get("token"), password: formData.get("password") }),
      });
      setMessage("Password updated. You can now sign in.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The password could not be reset.");
    }
  }

  return (
    <main className="mx-auto grid min-h-screen max-w-5xl content-center gap-6 px-6 py-12 lg:grid-cols-2">
      <section className="panel">
        <p className="eyebrow">KL-F-02 · Recovery</p>
        <h1 className="section-title">Request a reset token</h1>
        <p className="mt-3 text-sm leading-6 text-muted">Development emails are printed in the Django terminal by the configured console email backend.</p>
        <form action={requestReset} className="mt-6 space-y-4">
          <label className="field-label">Account email<input className="control" name="email" type="email" required /></label>
          <button className="button-primary w-full">Send reset instructions</button>
        </form>
      </section>
      <section className="panel">
        <p className="eyebrow">One-time token</p>
        <h2 className="section-title">Choose a new password</h2>
        <form action={confirmReset} className="mt-6 space-y-4">
          <label className="field-label">Reset token<input className="control font-mono" name="token" required /></label>
          <label className="field-label">New password<input className="control" name="password" type="password" minLength={12} required /></label>
          <button className="button-primary w-full">Reset password</button>
        </form>
        {message ? <p className="mt-4 border-l-2 border-primary bg-primary-soft p-3 text-xs" role="status">{message}</p> : null}
        <Link className="mt-5 inline-block text-xs font-semibold text-primary" href="/login">← Return to sign in</Link>
      </section>
    </main>
  );
}
