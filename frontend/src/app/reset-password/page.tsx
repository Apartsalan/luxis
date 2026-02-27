"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Scale, ArrowRight, ArrowLeft, Eye, EyeOff, CheckCircle2, AlertCircle } from "lucide-react";

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<"form" | "done" | "invalid">(token ? "form" : "invalid");

  // Use relative URL so requests go through Next.js rewrite proxy
  const apiUrl = "";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== passwordConfirm) {
      setError("Wachtwoorden komen niet overeen");
      return;
    }

    if (password.length < 8) {
      setError("Wachtwoord moet minimaal 8 tekens bevatten");
      return;
    }

    setLoading(true);

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 15000);

      const response = await fetch(`${apiUrl}/api/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
        signal: controller.signal,
      });

      clearTimeout(timeout);

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        if (response.status === 400 || response.status === 404) {
          setStep("invalid");
        } else {
          setError(data?.detail || "Er ging iets mis. Probeer het opnieuw.");
        }
        return;
      }

      setStep("done");
    } catch (err: any) {
      if (err?.name === "AbortError") {
        setError("De server reageert niet. Probeer het later opnieuw.");
      } else {
        setError("Kan geen verbinding maken met de server.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6">
      <div className="w-full max-w-sm animate-fade-in">
        {/* Logo */}
        <div className="mb-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary shadow-lg shadow-primary/25">
            <Scale className="h-6 w-6 text-white" />
          </div>
          <h1 className="mt-4 text-2xl font-bold text-foreground">Luxis</h1>
        </div>

        {/* Invalid token */}
        {step === "invalid" && (
          <div className="text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-amber-50 mb-6">
              <AlertCircle className="h-7 w-7 text-amber-600" />
            </div>
            <h2 className="text-xl font-bold text-foreground">Ongeldige link</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Deze herstellink is verlopen of ongeldig. Vraag een nieuwe link aan.
            </p>
            <button
              onClick={() => router.push("/login")}
              className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Terug naar inloggen
            </button>
          </div>
        )}

        {/* Reset form */}
        {step === "form" && (
          <>
            <div className="mb-8 text-center">
              <h2 className="text-xl font-bold text-foreground">Nieuw wachtwoord instellen</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Kies een sterk wachtwoord van minimaal 8 tekens.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="new-password" className="block text-sm font-medium text-foreground mb-1.5">
                  Nieuw wachtwoord
                </label>
                <div className="relative">
                  <input
                    id="new-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="new-password"
                    autoFocus
                    className="w-full rounded-lg border border-input bg-card px-4 py-3 pr-11 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                    placeholder="Minimaal 8 tekens"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label htmlFor="confirm-password" className="block text-sm font-medium text-foreground mb-1.5">
                  Bevestig wachtwoord
                </label>
                <input
                  id="confirm-password"
                  type="password"
                  value={passwordConfirm}
                  onChange={(e) => setPasswordConfirm(e.target.value)}
                  required
                  autoComplete="new-password"
                  className="w-full rounded-lg border border-input bg-card px-4 py-3 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                  placeholder="Herhaal wachtwoord"
                />
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
                    Wachtwoord instellen...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    Wachtwoord instellen
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
            <h2 className="text-xl font-bold text-foreground">Wachtwoord gewijzigd</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Je wachtwoord is succesvol gewijzigd. Je kunt nu inloggen met je nieuwe wachtwoord.
            </p>
            <button
              onClick={() => router.push("/login")}
              className="mt-6 inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors group"
            >
              Naar inloggen
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

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-background">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary/20 border-t-primary" />
        </div>
      }
    >
      <ResetPasswordContent />
    </Suspense>
  );
}
