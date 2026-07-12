"use client";

import { useState, useEffect, useCallback } from "react";
import { Link, Unlink, CheckCircle2, Loader2, Mail, Lock, LockOpen, ShieldAlert } from "lucide-react";
import { toast } from "sonner";
import { useTestEmail } from "@/hooks/use-documents";
import { useEmailOAuthStatus, useEmailOAuthAuthorize, useEmailOAuthDisconnect } from "@/hooks/use-email-oauth";
import { useMailLock, useSetMailLock } from "@/hooks/use-settings";

export function EmailTab() {
  const [testAddress, setTestAddress] = useState("");
  const testEmail = useTestEmail();
  const oauthStatus = useEmailOAuthStatus();
  const authorize = useEmailOAuthAuthorize();
  const disconnect = useEmailOAuthDisconnect();
  const mailLock = useMailLock();
  const setMailLock = useSetMailLock();

  const handleToggleMailLock = async () => {
    const state = mailLock.data;
    if (!state) return;
    const opening = state.db_locked; // nu dicht → we willen openen
    if (
      opening &&
      !window.confirm(
        "Weet je zeker dat je het mailslot OPENT?\n\nVanaf dat moment kan Luxis " +
          "echt e-mails versturen naar debiteuren en wederpartijen.",
      )
    ) {
      return;
    }
    try {
      const res = await setMailLock.mutateAsync(!state.db_locked);
      toast.success(
        res.locked
          ? "Mailslot staat dicht — er gaat niets de deur uit."
          : "Mailslot is open — Luxis kan nu mail versturen.",
      );
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Kon mailslot niet omzetten");
    }
  };

  // Listen for OAuth popup success message (validate origin to prevent spoofing)
  const handleOAuthMessage = useCallback(
    (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return;

      if (event.data?.type === "LUXIS_EMAIL_OAUTH_SUCCESS") {
        toast.success(`E-mail verbonden: ${event.data.email}`);
        oauthStatus.refetch();
      } else if (event.data?.type === "LUXIS_EMAIL_OAUTH_ERROR") {
        toast.error(`Verbinding mislukt: ${event.data.error}`);
      }
    },
    [oauthStatus]
  );

  useEffect(() => {
    window.addEventListener("message", handleOAuthMessage);
    return () => window.removeEventListener("message", handleOAuthMessage);
  }, [handleOAuthMessage]);

  const handleConnect = async (provider: "gmail" | "outlook") => {
    try {
      const result = await authorize.mutateAsync({ provider });
      // Open OAuth in popup window
      const width = 600;
      const height = 700;
      const left = window.screenX + (window.outerWidth - width) / 2;
      const top = window.screenY + (window.outerHeight - height) / 2;
      window.open(
        result.authorize_url,
        "luxis-email-oauth",
        `width=${width},height=${height},left=${left},top=${top},popup=yes`
      );
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Kon OAuth niet starten");
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnect.mutateAsync();
      toast.success("E-mailaccount ontkoppeld");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Ontkoppelen mislukt");
    }
  };

  const handleTestEmail = async () => {
    const email = testAddress.trim();
    if (!email) {
      toast.error("Vul een e-mailadres in");
      return;
    }
    try {
      await testEmail.mutateAsync({ email });
      toast.success("Test e-mail verzonden naar " + email);
      setTestAddress("");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Test e-mail verzenden mislukt");
    }
  };

  const account = oauthStatus.data;

  const lock = mailLock.data;

  return (
    <div className="space-y-6">
      {/* Mailslot (bouwfase) */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold text-foreground mb-2">
          Mailverzending
        </h2>
        <p className="text-sm text-muted-foreground mb-4">
          Tijdens de bouwfase staat uitgaande mail op slot: Luxis stuurt dan
          niets naar debiteuren of wederpartijen. Zet het slot open wanneer je
          echt wilt kunnen versturen. Ontvangen en synchroniseren werkt altijd.
        </p>

        {mailLock.isLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Status ophalen...</span>
          </div>
        ) : !lock ? (
          <div className="text-sm text-destructive">
            Kon de mailslot-stand niet ophalen.
          </div>
        ) : (
          <div className="space-y-3">
            <div
              className={`flex items-center justify-between rounded-lg border p-4 ${
                lock.locked
                  ? "border-red-200 bg-red-50"
                  : "border-green-200 bg-green-50"
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-full ${
                    lock.locked ? "bg-red-100" : "bg-green-100"
                  }`}
                >
                  {lock.locked ? (
                    <Lock className="h-5 w-5 text-red-600" />
                  ) : (
                    <LockOpen className="h-5 w-5 text-green-600" />
                  )}
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {lock.locked
                      ? "Mailverzending staat op slot"
                      : "Mailverzending is open"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {lock.locked
                      ? "Er gaat op dit moment geen mail de deur uit."
                      : "Luxis kan nu e-mails versturen."}
                  </p>
                </div>
              </div>
              <button
                onClick={handleToggleMailLock}
                disabled={setMailLock.isPending || lock.env_hard_lock}
                className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 ${
                  lock.db_locked
                    ? "bg-primary text-primary-foreground hover:bg-primary/90"
                    : "border border-border bg-background text-foreground hover:bg-muted"
                }`}
              >
                {setMailLock.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : lock.db_locked ? (
                  <LockOpen className="h-4 w-4" />
                ) : (
                  <Lock className="h-4 w-4" />
                )}
                {lock.db_locked ? "Openen" : "Op slot zetten"}
              </button>
            </div>

            {lock.env_hard_lock && (
              <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3">
                <ShieldAlert className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" />
                <p className="text-xs text-amber-800">
                  Er staat nog een extra server-noodslot aan. Zolang dat aan is,
                  blijft mail geblokkeerd en kan deze knop niet openen. Vraag
                  Arsalan het server-noodslot eenmalig te verwijderen; daarna is
                  deze knop volledig in je eigen beheer.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Email OAuth Connection */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold text-foreground mb-2">
          E-mail integratie
        </h2>
        <p className="text-sm text-muted-foreground mb-4">
          Verbind je e-mailaccount om e-mails te lezen, versturen en automatisch
          aan dossiers te koppelen.
        </p>

        {oauthStatus.isLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Status ophalen...</span>
          </div>
        ) : account?.connected ? (
          /* Connected state */
          <div className="space-y-4">
            <div className="rounded-lg border border-green-200 bg-green-50 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
                    <CheckCircle2 className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {account.email_address}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Verbonden via{" "}
                      {account.provider === "gmail" ? "Gmail" : "Outlook"}{" "}
                      {account.connected_at &&
                        `op ${new Date(account.connected_at).toLocaleDateString("nl-NL", { day: "numeric", month: "long", year: "numeric" })}`}
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleDisconnect}
                  disabled={disconnect.isPending}
                  className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm text-muted-foreground hover:text-destructive hover:border-destructive/50 transition-colors"
                >
                  {disconnect.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Unlink className="h-4 w-4" />
                  )}
                  Ontkoppelen
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Not connected state */
          <div className="space-y-4">
            <div className="rounded-lg border border-border bg-muted/30 p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                  <Mail className="h-5 w-5 text-muted-foreground" />
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground">
                    Geen e-mailaccount verbonden
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Verbind Outlook om e-mail integratie te activeren
                  </p>
                </div>
              </div>
              {/* S203 #17: Gmail-knop verborgen — beleid sinds feb 2026 is 'alleen
                  Outlook/Microsoft 365' (docs/future-modules.md). De Gmail-OAuth-route
                  blijft in de backend als herstelpad, maar wordt niet meer aangeboden. */}
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleConnect("outlook")}
                  disabled={authorize.isPending}
                  className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground hover:bg-muted disabled:opacity-50 transition-colors"
                >
                  {authorize.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Link className="h-4 w-4" />
                  )}
                  Verbind met Outlook
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* SMTP status info */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold text-foreground mb-2">
          SMTP-configuratie
        </h2>
        <p className="text-sm text-muted-foreground mb-4">
          Naast de e-mail integratie hierboven worden systeemmeldingen verstuurd
          via SMTP.
        </p>
        <div className="rounded-lg border border-border bg-muted/30 p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Mail className="h-4 w-4" />
            <span>
              SMTP-instellingen worden beheerd via omgevingsvariabelen op de
              server.
            </span>
          </div>
        </div>
      </div>

      {/* Test email */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold text-foreground mb-2">
          Test e-mail
        </h2>
        <p className="text-sm text-muted-foreground mb-4">
          Verstuur een test e-mail om te controleren of de SMTP-configuratie
          correct werkt.
        </p>
        <div className="flex gap-3">
          <input
            type="email"
            value={testAddress}
            onChange={(e) => setTestAddress(e.target.value)}
            placeholder="naam@voorbeeld.nl"
            className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleTestEmail();
            }}
          />
          <button
            onClick={handleTestEmail}
            disabled={testEmail.isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {testEmail.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Mail className="h-4 w-4" />
            )}
            Verstuur test
          </button>
        </div>
      </div>
    </div>
  );
}
