"use client";

import { useState } from "react";
import {
  Settings,
  User,
  Building2,
  Palette,
  Bell,
  Shield,
  Save,
} from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/hooks/use-auth";

const TABS = [
  { id: "profiel", label: "Profiel", icon: User },
  { id: "kantoor", label: "Kantoor", icon: Building2 },
  { id: "meldingen", label: "Meldingen", icon: Bell },
  { id: "weergave", label: "Weergave", icon: Palette },
];

export default function InstellingenPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("profiel");

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Instellingen</h1>
        <p className="text-sm text-muted-foreground">
          Beheer je profiel en kantoorinstellingen
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[220px,1fr]">
        {/* Sidebar navigation */}
        <nav className="space-y-0.5">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Content */}
        <div className="space-y-6">
          {activeTab === "profiel" && <ProfielTab user={user} />}
          {activeTab === "kantoor" && <KantoorTab />}
          {activeTab === "meldingen" && <MeldingenTab />}
          {activeTab === "weergave" && <WeergaveTab />}
        </div>
      </div>
    </div>
  );
}

// ── Profiel Tab ──────────────────────────────────────────────────────────────

function ProfielTab({ user }: { user: any }) {
  const [form, setForm] = useState({
    full_name: user?.full_name || "",
    email: user?.email || "",
  });

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold text-foreground mb-4">
          Persoonlijke gegevens
        </h2>
        <div className="space-y-4 max-w-md">
          <div>
            <label className="block text-sm font-medium text-foreground">
              Volledige naam
            </label>
            <input
              type="text"
              value={form.full_name}
              onChange={(e) =>
                setForm((f) => ({ ...f, full_name: e.target.value }))
              }
              className={inputClass}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground">
              E-mailadres
            </label>
            <input
              type="email"
              value={form.email}
              disabled
              className={`${inputClass} bg-muted/50 cursor-not-allowed`}
            />
            <p className="mt-1 text-xs text-muted-foreground">
              E-mailadres kan niet worden gewijzigd
            </p>
          </div>
          <button
            onClick={() => toast.info("Profiel bijwerken wordt binnenkort toegevoegd")}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Save className="h-4 w-4" />
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
        <button
          onClick={() =>
            toast.info("Wachtwoord wijzigen wordt binnenkort toegevoegd")
          }
          className="inline-flex items-center gap-1.5 rounded-lg border border-border px-4 py-2.5 text-sm font-medium hover:bg-muted transition-colors"
        >
          <Shield className="h-4 w-4" />
          Wachtwoord wijzigen
        </button>
      </div>
    </div>
  );
}

// ── Kantoor Tab ──────────────────────────────────────────────────────────────

function KantoorTab() {
  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold text-foreground mb-4">
          Kantoorgegevens
        </h2>
        <div className="space-y-4 max-w-md">
          <div>
            <label className="block text-sm font-medium text-foreground">
              Kantoornaam
            </label>
            <input
              type="text"
              defaultValue="Kesting Legal"
              className={inputClass}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-foreground">
                KvK-nummer
              </label>
              <input type="text" className={inputClass} />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground">
                BTW-nummer
              </label>
              <input type="text" className={inputClass} />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground">
              Adres
            </label>
            <input type="text" className={inputClass} />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-foreground">
                Postcode
              </label>
              <input type="text" className={inputClass} />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground">
                Plaats
              </label>
              <input type="text" defaultValue="Amsterdam" className={inputClass} />
            </div>
          </div>
          <button
            onClick={() =>
              toast.info("Kantoorinstellingen worden binnenkort toegevoegd")
            }
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Save className="h-4 w-4" />
            Opslaan
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold text-foreground mb-2">
          Standaard rente-instellingen
        </h2>
        <p className="text-sm text-muted-foreground mb-4">
          Standaard instellingen voor nieuwe zaken
        </p>
        <div className="max-w-md space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground">
              Standaard rentetype
            </label>
            <select defaultValue="statutory" className={inputClass}>
              <option value="statutory">
                Wettelijke rente (art. 6:119 BW)
              </option>
              <option value="commercial">
                Handelsrente (art. 6:119a BW)
              </option>
              <option value="government">
                Overheidsrente (art. 6:119b BW)
              </option>
              <option value="contractual">Contractuele rente</option>
            </select>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="btw_bik"
              defaultChecked
              className="h-4 w-4 rounded border-input accent-primary"
            />
            <label htmlFor="btw_bik" className="text-sm text-foreground">
              BTW over BIK berekenen (client is btw-plichtig)
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Meldingen Tab ────────────────────────────────────────────────────────────

function MeldingenTab() {
  const notifications = [
    {
      id: "status_change",
      label: "Statuswijzigingen",
      description: "Melding bij wijziging van zaakstatus",
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

// ── Weergave Tab ─────────────────────────────────────────────────────────────

function WeergaveTab() {
  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <h2 className="text-base font-semibold text-foreground mb-2">
        Weergave-instellingen
      </h2>
      <p className="text-sm text-muted-foreground mb-6">
        Pas de weergave van Luxis aan je voorkeuren aan
      </p>
      <div className="space-y-6 max-w-md">
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Thema
          </label>
          <div className="flex gap-3">
            {(
              [
                { id: "light", label: "Licht", emoji: "☀️" },
                { id: "dark", label: "Donker", emoji: "🌙" },
                { id: "system", label: "Systeem", emoji: "💻" },
              ] as const
            ).map((theme) => (
              <button
                key={theme.id}
                onClick={() =>
                  toast.info("Thema-instellingen worden binnenkort toegevoegd")
                }
                className={`flex-1 rounded-lg border p-3 text-center text-sm font-medium transition-all ${
                  theme.id === "light"
                    ? "border-primary bg-primary/5 text-primary ring-1 ring-primary/20"
                    : "border-border text-muted-foreground hover:border-primary/30"
                }`}
              >
                <span className="text-lg block mb-1">{theme.emoji}</span>
                {theme.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Sidebar
          </label>
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="sidebar_collapsed"
              className="h-4 w-4 rounded border-input accent-primary"
            />
            <label
              htmlFor="sidebar_collapsed"
              className="text-sm text-foreground"
            >
              Sidebar standaard ingeklapt
            </label>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Datumformaat
          </label>
          <select
            defaultValue="nl"
            className="w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
          >
            <option value="nl">17-02-2026 (DD-MM-JJJJ)</option>
            <option value="iso">2026-02-17 (JJJJ-MM-DD)</option>
          </select>
        </div>
      </div>
    </div>
  );
}
