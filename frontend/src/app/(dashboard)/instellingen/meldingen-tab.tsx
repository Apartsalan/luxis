"use client";

import { toast } from "sonner";

export function MeldingenTab() {
  const notifications = [
    {
      id: "status_change",
      label: "Statuswijzigingen",
      description: "Melding bij wijziging van dossierstatus",
      enabled: true,
    },
    {
      id: "payment_received",
      label: "Betalingen ontvangen",
      description: "Melding wanneer een betaling wordt geregistreerd",
      enabled: true,
    },
    {
      id: "deadline_reminder",
      label: "Deadline herinneringen",
      description: "Herinnering 3 dagen voor een deadline",
      enabled: false,
    },
    {
      id: "weekly_summary",
      label: "Wekelijks overzicht",
      description: "Samenvatting van de week per e-mail",
      enabled: false,
    },
  ];

  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <h2 className="text-base font-semibold text-foreground mb-2">
        Meldingsvoorkeuren
      </h2>
      <p className="text-sm text-muted-foreground mb-6">
        Kies welke meldingen je wilt ontvangen
      </p>
      <div className="space-y-4">
        {notifications.map((notif) => (
          <div
            key={notif.id}
            className="flex items-center justify-between rounded-lg border border-border p-4"
          >
            <div>
              <p className="text-sm font-medium text-foreground">
                {notif.label}
              </p>
              <p className="text-xs text-muted-foreground">
                {notif.description}
              </p>
            </div>
            <button
              onClick={() =>
                toast.info("Meldingsvoorkeuren worden binnenkort toegevoegd")
              }
              className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors ${
                notif.enabled ? "bg-primary" : "bg-muted"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transition-transform ${
                  notif.enabled ? "translate-x-5" : "translate-x-0"
                }`}
              />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
