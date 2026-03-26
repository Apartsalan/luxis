"use client";

import { useState, useEffect, useCallback } from "react";
import { Link, Unlink, CheckCircle2, Loader2, Mail } from "lucide-react";
import { toast } from "sonner";
import { useTestEmail } from "@/hooks/use-documents";
import { useEmailOAuthStatus, useEmailOAuthAuthorize, useEmailOAuthDisconnect } from "@/hooks/use-email-oauth";

export function EmailTab() {
  const [testAddress, setTestAddress] = useState("");
  const testEmail = useTestEmail();
  const oauthStatus = useEmailOAuthStatus();
  const authorize = useEmailOAuthAuthorize();
  const disconnect = useEmailOAuthDisconnect();

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

  return (
    <div className="space-y-6">
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
            <div className="rounded-lg border border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950/30 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/50">
                    <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
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
                    Verbind Gmail of Outlook om e-mail integratie te activeren
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleConnect("gmail")}
                  disabled={authorize.isPending}
                  className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  {authorize.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Link className="h-4 w-4" />
                  )}
                  Verbind met Gmail
                </button>
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
