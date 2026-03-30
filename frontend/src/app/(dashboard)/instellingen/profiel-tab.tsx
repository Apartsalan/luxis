"use client";

import { useState } from "react";
import { Shield, Save, Loader2, Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import { useUpdateProfile, useChangePassword } from "@/hooks/use-settings";

import type { User } from "@/hooks/use-auth";

export function ProfielTab({ user }: { user: User | null }) {
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [hourlyRate, setHourlyRate] = useState(
    user?.default_hourly_rate != null ? String(user.default_hourly_rate) : ""
  );
  const updateProfile = useUpdateProfile();

  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const changePassword = useChangePassword();
  const [profileError, setProfileError] = useState("");
  const [passwordError, setPasswordError] = useState("");

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  const handleSaveProfile = () => {
    if (!fullName.trim()) {
      setProfileError("Naam mag niet leeg zijn");
      return;
    }
    setProfileError("");
    updateProfile.mutate(
      {
        full_name: fullName.trim(),
        default_hourly_rate: hourlyRate || null,
      },
      {
        onSuccess: () => toast.success("Profiel bijgewerkt"),
      }
    );
  };

  const handleChangePassword = () => {
    if (!currentPassword || !newPassword) {
      setPasswordError("Vul beide velden in");
      return;
    }
    if (newPassword.length < 8) {
      setPasswordError("Nieuw wachtwoord moet minimaal 8 tekens zijn");
      return;
    }
    setPasswordError("");
    changePassword.mutate(
      { current_password: currentPassword, new_password: newPassword },
      {
        onSuccess: () => {
          toast.success("Wachtwoord gewijzigd");
          setCurrentPassword("");
          setNewPassword("");
          setShowPasswordForm(false);
        },
      }
    );
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold text-foreground mb-4">
          Persoonlijke gegevens
        </h2>
        <div className="space-y-4 max-w-md">
          <div>
            <label htmlFor="settings-full-name" className="block text-sm font-medium text-foreground">
              Volledige naam
            </label>
            <input
              id="settings-full-name"
              type="text"
              value={fullName}
              onChange={(e) => { setFullName(e.target.value); setProfileError(""); }}
              className={`${inputClass} ${profileError ? "border-destructive ring-1 ring-destructive/30" : ""}`}
            />
            {profileError && (
              <p className="mt-1 text-xs text-destructive">{profileError}</p>
            )}
          </div>
          <div>
            <label htmlFor="settings-email" className="block text-sm font-medium text-foreground">
              E-mailadres
            </label>
            <input
              id="settings-email"
              type="email"
              value={user?.email || ""}
              disabled
              className={`${inputClass} bg-muted/50 cursor-not-allowed`}
            />
            <p className="mt-1 text-xs text-muted-foreground">
              E-mailadres kan niet worden gewijzigd
            </p>
          </div>
          <div>
            <label htmlFor="settings-hourly-rate" className="block text-sm font-medium text-foreground">
              Standaard uurtarief
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm mt-0.5">
                &euro;
              </span>
              <input
                id="settings-hourly-rate"
                type="number"
                min="0"
                step="0.01"
                placeholder="bijv. 250.00"
                value={hourlyRate}
                onChange={(e) => setHourlyRate(e.target.value)}
                className={`${inputClass} pl-7`}
              />
            </div>
            <p className="mt-1 text-xs text-muted-foreground">
              Wordt automatisch ingevuld bij nieuwe tijdregistraties
            </p>
          </div>
          <button
            onClick={handleSaveProfile}
            disabled={updateProfile.isPending}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {updateProfile.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            Opslaan
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold text-foreground mb-2">
          Beveiliging
        </h2>
        <p className="text-sm text-muted-foreground mb-4">
          Beheer je wachtwoord en beveiligingsinstellingen
        </p>

        {!showPasswordForm ? (
          <button
            onClick={() => setShowPasswordForm(true)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border px-4 py-2.5 text-sm font-medium hover:bg-muted transition-colors"
          >
            <Shield className="h-4 w-4" />
            Wachtwoord wijzigen
          </button>
        ) : (
          <div className="space-y-4 max-w-md">
            <div>
              <label htmlFor="settings-current-password" className="block text-sm font-medium text-foreground">
                Huidig wachtwoord
              </label>
              <div className="relative">
                <input
                  id="settings-current-password"
                  type={showCurrent ? "text" : "password"}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className={inputClass}
                />
                <button
                  type="button"
                  onClick={() => setShowCurrent(!showCurrent)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground mt-0.5"
                >
                  {showCurrent ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
            <div>
              <label htmlFor="settings-new-password" className="block text-sm font-medium text-foreground">
                Nieuw wachtwoord
              </label>
              <div className="relative">
                <input
                  id="settings-new-password"
                  type={showNew ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Minimaal 8 tekens"
                  className={inputClass}
                />
                <button
                  type="button"
                  onClick={() => setShowNew(!showNew)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground mt-0.5"
                >
                  {showNew ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
            {passwordError && (
              <p className="text-xs text-destructive">{passwordError}</p>
            )}
            <div className="flex gap-2">
              <button
                onClick={handleChangePassword}
                disabled={changePassword.isPending}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {changePassword.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Shield className="h-4 w-4" />
                )}
                Wachtwoord wijzigen
              </button>
              <button
                onClick={() => {
                  setShowPasswordForm(false);
                  setCurrentPassword("");
                  setNewPassword("");
                }}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border px-4 py-2.5 text-sm font-medium hover:bg-muted transition-colors"
              >
                Annuleren
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
