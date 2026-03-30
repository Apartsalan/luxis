"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Cloud,
  CloudOff,
  ExternalLink,
  Loader2,
  RefreshCw,
  Settings,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import {
  useExactOnlineStatus,
  useExactOnlineAuthorize,
  useExactOnlineDisconnect,
  useExactOnlineSetupData,
  useExactOnlineUpdateSettings,
  useExactOnlineSync,
} from "@/hooks/use-exact-online";
import type { ExactSetupData } from "@/hooks/use-exact-online";

export function ExactTab() {
  const status = useExactOnlineStatus();
  const authorize = useExactOnlineAuthorize();
  const disconnect = useExactOnlineDisconnect();
  const setupData = useExactOnlineSetupData();
  const updateSettings = useExactOnlineUpdateSettings();
  const sync = useExactOnlineSync();

  const [localSettings, setLocalSettings] = useState({
    sales_journal_code: "",
    bank_journal_code: "",
    default_revenue_gl: "",
    default_expense_gl: "",
  });

  // Initialize local settings from connection status
  useEffect(() => {
    if (status.data?.connected) {
      setLocalSettings({
        sales_journal_code: status.data.sales_journal_code || "",
        bank_journal_code: status.data.bank_journal_code || "",
        default_revenue_gl: status.data.default_revenue_gl || "",
        default_expense_gl: status.data.default_expense_gl || "",
      });
    }
  }, [status.data]);

  // Listen for OAuth popup messages
  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      if (event.origin !== window.location.origin) return;
      if (event.data?.type === "LUXIS_EXACT_OAUTH_SUCCESS") {
        toast.success(
          `Exact Online verbonden: ${event.data.division || event.data.email}`
        );
        status.refetch();
      }
      if (event.data?.type === "LUXIS_EXACT_OAUTH_ERROR") {
        toast.error(event.data.error || "Verbinding mislukt");
      }
    }
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [status]);

  const handleConnect = useCallback(async () => {
    try {
      const { authorize_url } = await authorize.mutateAsync();
      const w = 600;
      const h = 700;
      const left = window.screenX + (window.outerWidth - w) / 2;
      const top = window.screenY + (window.outerHeight - h) / 2;
      window.open(
        authorize_url,
        "luxis-exact-oauth",
        `width=${w},height=${h},left=${left},top=${top},popup=yes`
      );
    } catch (e: any) {
      toast.error(e.message);
    }
  }, [authorize]);

  const handleDisconnect = useCallback(async () => {
    try {
      const result = await disconnect.mutateAsync();
      toast.success(result.message);
    } catch (e: any) {
      toast.error(e.message);
    }
  }, [disconnect]);

  const handleLoadSetupData = useCallback(() => {
    setupData.refetch();
  }, [setupData]);

  const handleSaveSettings = useCallback(async () => {
    try {
      const result = await updateSettings.mutateAsync(localSettings);
      toast.success(result.message);
    } catch (e: any) {
      toast.error(e.message);
    }
  }, [updateSettings, localSettings]);

  const handleSync = useCallback(async () => {
    try {
      const result = await sync.mutateAsync();
      if (result.success) {
        toast.success(result.message);
      } else {
        toast.error(result.message);
        result.errors.forEach((err) => toast.error(err));
      }
    } catch (e: any) {
      toast.error(e.message);
    }
  }, [sync]);

  if (status.isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const connected = status.data?.connected;

  return (
    <div className="space-y-6">
      {/* Connection Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {connected ? (
              <Cloud className="h-5 w-5 text-green-600" />
            ) : (
              <CloudOff className="h-5 w-5 text-muted-foreground" />
            )}
            Exact Online
          </CardTitle>
          <CardDescription>
            {connected
              ? "Verbonden met Exact Online voor automatische boekhoudsynchronisatie"
              : "Koppel Exact Online om facturen en betalingen automatisch te synchroniseren"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {connected ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border p-4">
                <div className="space-y-1">
                  <p className="text-sm font-medium">
                    {status.data?.division_name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {status.data?.connected_email}
                  </p>
                  {status.data?.last_sync_at && (
                    <p className="text-xs text-muted-foreground">
                      Laatste sync:{" "}
                      {new Date(status.data.last_sync_at).toLocaleString(
                        "nl-NL"
                      )}
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Badge variant="secondary" className="bg-green-100 text-green-800">
                    Verbonden
                  </Badge>
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSync}
                  disabled={sync.isPending}
                >
                  {sync.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="mr-2 h-4 w-4" />
                  )}
                  Synchroniseren
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDisconnect}
                  disabled={disconnect.isPending}
                  className="text-destructive hover:text-destructive"
                >
                  Ontkoppelen
                </Button>
              </div>
            </div>
          ) : (
            <Button onClick={handleConnect} disabled={authorize.isPending}>
              {authorize.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <ExternalLink className="mr-2 h-4 w-4" />
              )}
              Koppel Exact Online
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Settings Card — only when connected */}
      {connected && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Synchronisatie-instellingen
            </CardTitle>
            <CardDescription>
              Koppel de juiste journalen en grootboekrekeningen voor de synchronisatie
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {!setupData.data && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleLoadSetupData}
                disabled={setupData.isFetching}
              >
                {setupData.isFetching ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="mr-2 h-4 w-4" />
                )}
                Gegevens ophalen uit Exact Online
              </Button>
            )}

            {setupData.data && (
              <>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="settings-sales-journal">Verkoopjournaal</Label>
                    <Select
                      value={localSettings.sales_journal_code}
                      onValueChange={(v) =>
                        setLocalSettings((s) => ({
                          ...s,
                          sales_journal_code: v,
                        }))
                      }
                    >
                      <SelectTrigger id="settings-sales-journal">
                        <SelectValue placeholder="Selecteer journaal" />
                      </SelectTrigger>
                      <SelectContent>
                        {setupData.data.journals.map((j) => (
                          <SelectItem key={j.code} value={j.code}>
                            {j.code} — {j.description}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="settings-bank-journal">Bankjournaal</Label>
                    <Select
                      value={localSettings.bank_journal_code}
                      onValueChange={(v) =>
                        setLocalSettings((s) => ({
                          ...s,
                          bank_journal_code: v,
                        }))
                      }
                    >
                      <SelectTrigger id="settings-bank-journal">
                        <SelectValue placeholder="Selecteer journaal" />
                      </SelectTrigger>
                      <SelectContent>
                        {setupData.data.journals.map((j) => (
                          <SelectItem key={j.code} value={j.code}>
                            {j.code} — {j.description}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="settings-revenue-gl">Omzet-grootboekrekening</Label>
                    <Select
                      value={localSettings.default_revenue_gl}
                      onValueChange={(v) =>
                        setLocalSettings((s) => ({
                          ...s,
                          default_revenue_gl: v,
                        }))
                      }
                    >
                      <SelectTrigger id="settings-revenue-gl">
                        <SelectValue placeholder="Selecteer rekening" />
                      </SelectTrigger>
                      <SelectContent>
                        {setupData.data.gl_accounts.map((g) => (
                          <SelectItem key={g.id} value={g.id}>
                            {g.code} — {g.description}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="settings-expense-gl">Verschotten-grootboekrekening</Label>
                    <Select
                      value={localSettings.default_expense_gl}
                      onValueChange={(v) =>
                        setLocalSettings((s) => ({
                          ...s,
                          default_expense_gl: v,
                        }))
                      }
                    >
                      <SelectTrigger id="settings-expense-gl">
                        <SelectValue placeholder="Selecteer rekening" />
                      </SelectTrigger>
                      <SelectContent>
                        {setupData.data.gl_accounts.map((g) => (
                          <SelectItem key={g.id} value={g.id}>
                            {g.code} — {g.description}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <Button
                  onClick={handleSaveSettings}
                  disabled={updateSettings.isPending}
                >
                  {updateSettings.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : null}
                  Instellingen opslaan
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
