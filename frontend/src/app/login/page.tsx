"use client";

import { useState } from "react";
import { Scale, Eye, EyeOff, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        setError("Onjuist e-mailadres of wachtwoord");
        return;
      }

      const data = await response.json();
      localStorage.setItem("luxis_access_token", data.access_token);
      localStorage.setItem("luxis_refresh_token", data.refresh_token);
      window.location.href = "/";
    } catch {
      setError("Er ging iets mis. Probeer het opnieuw.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between bg-gradient-to-br from-[hsl(224,30%,14%)] via-[hsl(224,35%,20%)] to-[hsl(224,30%,16%)] p-12">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary shadow-lg shadow-primary/25">
              <Scale className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white tracking-tight">
              Luxis
            </span>
          </div>
        </div>

        <div className="space-y-6">
          <h2 className="text-4xl font-bold text-white leading-tight">
            Praktijkmanagement
            <br />
            <span className="text-primary/80">voor de advocatuur</span>
          </h2>
          <p className="text-base text-white/50 max-w-md leading-relaxed">
            Beheer zaken, vorderingen, relaties en documenten vanuit één
            centraal systeem. Gebouwd voor de Nederlandse advocatuur.
          </p>
          <div className="flex gap-6 pt-4">
            <div>
              <p className="text-2xl font-bold text-white">100%</p>
              <p className="text-xs text-white/40 mt-0.5">
                Nederlands recht
              </p>
            </div>
            <div className="w-px bg-white/10" />
            <div>
              <p className="text-2xl font-bold text-white">Art. 6:44</p>
              <p className="text-xs text-white/40 mt-0.5">
                BW betalingsverdeling
              </p>
            </div>
            <div className="w-px bg-white/10" />
            <div>
              <p className="text-2xl font-bold text-white">WIK/BIK</p>
              <p className="text-xs text-white/40 mt-0.5">
                Incassostaffel
              </p>
            </div>
          </div>
        </div>

        <p className="text-xs text-white/20">
          © {new Date().getFullYear()} Luxis · Kesting Legal
        </p>
      </div>

      {/* Right panel — login form */}
      <div className="flex flex-1 items-center justify-center bg-background px-6 sm:px-8">
        <div className="w-full max-w-sm animate-fade-in">
          {/* Mobile logo */}
          <div className="mb-8 text-center lg:hidden">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary shadow-lg shadow-primary/25">
              <Scale className="h-6 w-6 text-white" />
            </div>
            <h1 className="mt-4 text-2xl font-bold text-foreground">Luxis</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Praktijkmanagement
            </p>
          </div>

          {/* Desktop heading */}
          <div className="hidden lg:block mb-8">
            <h1 className="text-2xl font-bold text-foreground">
              Welkom terug
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Log in op je Luxis account
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-foreground mb-1.5"
              >
                E-mailadres
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                autoFocus
                className="w-full rounded-lg border border-input bg-card px-4 py-3 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                placeholder="naam@kantoor.nl"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-foreground mb-1.5"
              >
                Wachtwoord
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="w-full rounded-lg border border-input bg-card px-4 py-3 pr-11 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
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
                  Bezig met inloggen...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  Inloggen
                  <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
                </span>
              )}
            </button>
          </form>

          <p className="mt-8 text-center text-xs text-muted-foreground/50">
            Luxis v0.1.0 · Praktijkmanagementsysteem
          </p>
        </div>
      </div>
    </div>
  );
}
