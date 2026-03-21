"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Scale, ArrowRight, CheckCircle2, AlertCircle } from "lucide-react";
import { tokenStore } from "@/lib/token-store";

export default function SetupPage() {
  const router = useRouter();
  const [step, setStep] = useState<"check" | "form" | "done" | "already-setup">("check");
  const [form, setForm] = useState({
    tenant_name: "",
    full_name: "",
    email: "",
    password: "",
    password_confirm: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Use relative URL so requests go through Next.js rewrite proxy
  const apiUrl = "";

  // Check if setup is needed (no users exist yet)
  useEffect(() => {
    fetch(`${apiUrl}/auth/setup-status`)
      .then((res) => res.json())
      .then((data) => {
        if (data.setup_complete) {
          setStep("already-setup");
        } else {
          setStep("form");
        }
      })
      .catch(() => {
        // If endpoint doesn't exist yet, show the form anyway
        setStep("form");
      });
  }, [apiUrl]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (form.password !== form.password_confirm) {
      setError("Wachtwoorden komen niet overeen");
      return;
    }

    if (form.password.length < 8) {
      setError("Wachtwoord moet minimaal 8 tekens bevatten");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${apiUrl}/auth/setup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tenant_name: form.tenant_name,
          full_name: form.full_name,
          email: form.email,
          password: form.password,
        }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        setError(data?.detail || "Er ging iets mis bij het aanmaken van het account.");
        return;
      }

      const data = await response.json();
      tokenStore.setTokens(data.access_token, data.refresh_token);
      setStep("done");
    } catch {
      setError("Kan geen verbinding maken met de server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      <div className="w-full max-w-lg animate-fade-in">
        {/* Logo */}
        <div className="mb-8 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-primary shadow-lg shadow-primary/25">
            <Scale className="h-7 w-7 text-white" />
          </div>
          <h1 className="mt-4 text-2xl font-bold text-foreground">Luxis Setup</h1>
        </div>

        {/* Checking... */}
        {step === "check" && (
          <div className="text-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary/20 border-t-primary mx-auto" />
            <p className="mt-4 text-sm text-muted-foreground">Controleren...</p>
          </div>
        )}

        {/* Already set up */}
        {step === "already-setup" && (
          <div className="text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-amber-50 mb-6">
              <AlertCircle className="h-7 w-7 text-amber-600" />
            </div>
            <h2 className="text-xl font-bold text-foreground">Setup is al voltooid</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Er is al een beheerder aangemaakt. Log in met je bestaande account.
            </p>
            <button
              onClick={() => router.push("/login")}
              className="mt-6 inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Naar inloggen
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Setup form */}
        {step === "form" && (
          <>
            <p className="text-center text-sm text-muted-foreground mb-8">
              Maak het eerste beheerdersaccount aan voor je kantoor.
            </p>

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Tenant / kantoor info */}
              <div className="rounded-lg border border-border p-4 space-y-4">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Kantoorgegevens
                </p>
                <div>
                  <label htmlFor="tenant_name" className="block text-sm font-medium text-foreground mb-1.5">
                    Kantoornaam
                  </label>
                  <input
                    id="tenant_name"
                    type="text"
                    value={form.tenant_name}
                    onChange={(e) => setForm({ ...form, tenant_name: e.target.value })}
                    required
                    autoFocus
                    className="w-full rounded-lg border border-input bg-card px-4 py-3 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                    placeholder="Kesting Legal"
                  />
                </div>
              </div>

              {/* User info */}
              <div className="rounded-lg border border-border p-4 space-y-4">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Beheerder
                </p>
                <div>
                  <label htmlFor="full_name" className="block text-sm font-medium text-foreground mb-1.5">
                    Volledige naam
                  </label>
                  <input
                    id="full_name"
                    type="text"
                    value={form.full_name}
                    onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                    required
                    className="w-full rounded-lg border border-input bg-card px-4 py-3 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                    placeholder="Lisanne Kesting"
                  />
                </div>
                <div>
                  <label htmlFor="setup-email" className="block text-sm font-medium text-foreground mb-1.5">
                    E-mailadres
                  </label>
                  <input
                    id="setup-email"
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    required
                    autoComplete="email"
                    className="w-full rounded-lg border border-input bg-card px-4 py-3 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                    placeholder="lisanne@kestinglegal.nl"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="setup-password" className="block text-sm font-medium text-foreground mb-1.5">
                      Wachtwoord
                    </label>
                    <input
                      id="setup-password"
                      type="password"
                      value={form.password}
                      onChange={(e) => setForm({ ...form, password: e.target.value })}
                      required
                      autoComplete="new-password"
                      className="w-full rounded-lg border border-input bg-card px-4 py-3 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                      placeholder="Min. 8 tekens"
                    />
                  </div>
                  <div>
                    <label htmlFor="setup-password-confirm" className="block text-sm font-medium text-foreground mb-1.5">
                      Bevestig
                    </label>
                    <input
                      id="setup-password-confirm"
                      type="password"
                      value={form.password_confirm}
                      onChange={(e) => setForm({ ...form, password_confirm: e.target.value })}
                      required
                      autoComplete="new-password"
                      className="w-full rounded-lg border border-input bg-card px-4 py-3 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                      placeholder="Herhaal"
                    />
                  </div>
                </div>
              </div>

              {error && (
                <div className="flex items-center gap-2 rounded-lg bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive">
                  <div className="h-1.5 w-1.5 rounded-full bg-destructive shrink-0" />
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-lg bg-primary px-4 py-3 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 transition-all group"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                    Account aanmaken...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    Kantoor instellen
                    <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
                  </span>
                )}
              </button>
            </form>
          </>
        )}

        {/* Done */}
        {step === "done" && (
          <div className="text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50 mb-6">
              <CheckCircle2 className="h-7 w-7 text-emerald-600" />
            </div>
            <h2 className="text-xl font-bold text-foreground">Klaar!</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Je kantoor <strong className="text-foreground">{form.tenant_name}</strong> is aangemaakt
              en je bent ingelogd als beheerder.
            </p>
            <button
              onClick={() => (window.location.href = "/")}
              className="mt-6 inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors group"
            >
              Naar Dashboard
              <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>
        )}

        <p className="mt-8 text-center text-xs text-muted-foreground/50">
          Luxis v0.1.0 · Praktijkmanagementsysteem
        </p>
      </div>
    </div>
  );
}
