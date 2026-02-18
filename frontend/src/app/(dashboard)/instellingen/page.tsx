"use client";

import { useState } from "react";
import {
  User,
  Building2,
  Palette,
  Bell,
  Shield,
  Save,
  Loader2,
  Eye,
  EyeOff,
  GitBranch,
  Plus,
  Trash2,
  GripVertical,
  ToggleLeft,
  ToggleRight,
  ChevronRight,
  Clock,
  AlertTriangle,
} from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/hooks/use-auth";
import {
  useTenant,
  useUpdateProfile,
  useChangePassword,
  useUpdateTenant,
} from "@/hooks/use-settings";
import {
  useWorkflowStatuses,
  useWorkflowTransitions,
  useWorkflowRules,
  useUpdateWorkflowRule,
  useDeleteWorkflowRule,
  PHASE_LABELS,
  PHASE_ORDER,
  PHASE_COLORS,
  TASK_TYPE_LABELS,
  ACTION_TYPE_LABELS,
  type WorkflowStatus as WFStatus,
  type WorkflowRule,
} from "@/hooks/use-workflow";

const TABS = [
  { id: "profiel", label: "Profiel", icon: User },
  { id: "kantoor", label: "Kantoor", icon: Building2 },
  { id: "workflow", label: "Workflow", icon: GitBranch },
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
          {activeTab === "workflow" && <WorkflowTab />}
          {activeTab === "meldingen" && <MeldingenTab />}
          {activeTab === "weergave" && <WeergaveTab />}
        </div>
      </div>
    </div>
  );
}

// ── Profiel Tab ──────────────────────────────────────────────────────────────

function ProfielTab({ user }: { user: any }) {
  const [fullName, setFullName] = useState(user?.full_name || "");
  const updateProfile = useUpdateProfile();

  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const changePassword = useChangePassword();

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  const handleSaveProfile = () => {
    if (!fullName.trim()) {
      toast.error("Naam mag niet leeg zijn");
      return;
    }
    updateProfile.mutate(
      { full_name: fullName.trim() },
      {
        onSuccess: () => toast.success("Profiel bijgewerkt"),
        onError: (err) => toast.error(err.message),
      }
    );
  };

  const handleChangePassword = () => {
    if (!currentPassword || !newPassword) {
      toast.error("Vul beide velden in");
      return;
    }
    if (newPassword.length < 8) {
      toast.error("Nieuw wachtwoord moet minimaal 8 tekens zijn");
      return;
    }
    changePassword.mutate(
      { current_password: currentPassword, new_password: newPassword },
      {
        onSuccess: () => {
          toast.success("Wachtwoord gewijzigd");
          setCurrentPassword("");
          setNewPassword("");
          setShowPasswordForm(false);
        },
        onError: (err) => toast.error(err.message),
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
            <label className="block text-sm font-medium text-foreground">
              Volledige naam
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground">
              E-mailadres
            </label>
            <input
              type="email"
              value={user?.email || ""}
              disabled
              className={`${inputClass} bg-muted/50 cursor-not-allowed`}
            />
            <p className="mt-1 text-xs text-muted-foreground">
              E-mailadres kan niet worden gewijzigd
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
              <label className="block text-sm font-medium text-foreground">
                Huidig wachtwoord
              </label>
              <div className="relative">
                <input
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
              <label className="block text-sm font-medium text-foreground">
                Nieuw wachtwoord
              </label>
              <div className="relative">
                <input
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

// ── Kantoor Tab ──────────────────────────────────────────────────────────────

function KantoorTab() {
  const { data: tenant, isLoading } = useTenant();
  const updateTenant = useUpdateTenant();

  const [form, setForm] = useState({
    name: "",
    kvk_number: "",
    btw_number: "",
    address: "",
    postal_code: "",
    city: "",
  });
  const [initialized, setInitialized] = useState(false);

  // Initialize form when tenant data loads
  if (tenant && !initialized) {
    setForm({
      name: tenant.name || "",
      kvk_number: tenant.kvk_number || "",
      btw_number: tenant.btw_number || "",
      address: tenant.address || "",
      postal_code: tenant.postal_code || "",
      city: tenant.city || "",
    });
    setInitialized(true);
  }

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  const handleSave = () => {
    updateTenant.mutate(
      {
        name: form.name || undefined,
        kvk_number: form.kvk_number || null,
        btw_number: form.btw_number || null,
        address: form.address || null,
        postal_code: form.postal_code || null,
        city: form.city || null,
      },
      {
        onSuccess: () => toast.success("Kantoorgegevens bijgewerkt"),
        onError: (err) => toast.error(err.message),
      }
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-8 justify-center text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Laden...
      </div>
    );
  }

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
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className={inputClass}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-foreground">
                KvK-nummer
              </label>
              <input
                type="text"
                value={form.kvk_number}
                onChange={(e) =>
                  setForm((f) => ({ ...f, kvk_number: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground">
                BTW-nummer
              </label>
              <input
                type="text"
                value={form.btw_number}
                onChange={(e) =>
                  setForm((f) => ({ ...f, btw_number: e.target.value }))
                }
                className={inputClass}
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground">
              Adres
            </label>
            <input
              type="text"
              value={form.address}
              onChange={(e) =>
                setForm((f) => ({ ...f, address: e.target.value }))
              }
              className={inputClass}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-foreground">
                Postcode
              </label>
              <input
                type="text"
                value={form.postal_code}
                onChange={(e) =>
                  setForm((f) => ({ ...f, postal_code: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground">
                Plaats
              </label>
              <input
                type="text"
                value={form.city}
                onChange={(e) =>
                  setForm((f) => ({ ...f, city: e.target.value }))
                }
                className={inputClass}
              />
            </div>
          </div>
          <button
            onClick={handleSave}
            disabled={updateTenant.isPending}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {updateTenant.isPending ? (
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
                { id: "light", label: "Licht" },
                { id: "dark", label: "Donker" },
                { id: "system", label: "Systeem" },
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

// ── Workflow Tab ─────────────────────────────────────────────────────────────

const PHASE_BADGE_CLASSES: Record<string, string> = {
  minnelijk: "bg-blue-50 text-blue-700 ring-blue-600/20",
  regeling: "bg-amber-50 text-amber-700 ring-amber-600/20",
  gerechtelijk: "bg-purple-50 text-purple-700 ring-purple-600/20",
  executie: "bg-red-50 text-red-700 ring-red-600/20",
  afgerond: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
};

const DEBTOR_TYPE_LABELS: Record<string, string> = {
  b2b: "B2B",
  b2c: "B2C",
  both: "Beide",
};

function WorkflowTab() {
  const { data: statuses, isLoading: loadingStatuses } = useWorkflowStatuses();
  const { data: transitions, isLoading: loadingTransitions } =
    useWorkflowTransitions();
  const { data: rules, isLoading: loadingRules } = useWorkflowRules();
  const updateRule = useUpdateWorkflowRule();
  const [activeSection, setActiveSection] = useState<
    "statuses" | "rules"
  >("statuses");

  if (loadingStatuses || loadingTransitions || loadingRules) {
    return (
      <div className="flex items-center gap-2 py-8 justify-center text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Workflow configuratie laden...
      </div>
    );
  }

  const sections = [
    { id: "statuses" as const, label: "Statussen & Fases" },
    { id: "rules" as const, label: "Automatiseringsregels" },
  ];

  return (
    <div className="space-y-6">
      {/* Section toggle */}
      <div className="flex gap-1 rounded-lg bg-muted p-1">
        {sections.map((section) => (
          <button
            key={section.id}
            onClick={() => setActiveSection(section.id)}
            className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-all ${
              activeSection === section.id
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {section.label}
          </button>
        ))}
      </div>

      {activeSection === "statuses" && (
        <StatusesSection statuses={statuses ?? []} transitions={transitions ?? []} />
      )}
      {activeSection === "rules" && (
        <RulesSection
          rules={rules ?? []}
          statuses={statuses ?? []}
          onToggleRule={(id, active) =>
            updateRule.mutate(
              { id, data: { is_active: active } },
              {
                onSuccess: () =>
                  toast.success(
                    active ? "Regel geactiveerd" : "Regel gedeactiveerd"
                  ),
                onError: (err) => toast.error(err.message),
              }
            )
          }
        />
      )}
    </div>
  );
}

// ── Statuses Section ────────────────────────────────────────────────────────

function StatusesSection({
  statuses,
  transitions,
}: {
  statuses: WFStatus[];
  transitions: { from_status_id: string; to_status_id: string; debtor_type: string; is_active: boolean }[];
}) {
  // Group statuses by phase
  const groupedByPhase: Record<string, WFStatus[]> = {};
  for (const phase of PHASE_ORDER) {
    groupedByPhase[phase] = statuses
      .filter((s) => s.phase === phase && s.is_active)
      .sort((a, b) => a.sort_order - b.sort_order);
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-foreground">
              Incasso fases & statussen
            </h2>
            <p className="text-sm text-muted-foreground">
              Statussen gegroepeerd per fase van het incassotraject
            </p>
          </div>
        </div>

        <div className="space-y-4">
          {PHASE_ORDER.map((phase) => {
            const phaseStatuses = groupedByPhase[phase] ?? [];
            if (phaseStatuses.length === 0) return null;

            return (
              <div key={phase} className="rounded-lg border border-border">
                <div className="flex items-center gap-2 border-b border-border bg-muted/30 px-4 py-2.5">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
                      PHASE_BADGE_CLASSES[phase] ?? "bg-slate-50 text-slate-600 ring-slate-500/20"
                    }`}
                  >
                    {PHASE_LABELS[phase]}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {phaseStatuses.length} status{phaseStatuses.length !== 1 ? "sen" : ""}
                  </span>
                </div>
                <div className="divide-y divide-border">
                  {phaseStatuses.map((status) => {
                    // Count outgoing transitions for this status
                    const outgoing = transitions.filter(
                      (t) => t.from_status_id === status.id && t.is_active
                    );
                    return (
                      <div
                        key={status.id}
                        className="flex items-center justify-between px-4 py-3"
                      >
                        <div className="flex items-center gap-3">
                          <GripVertical className="h-4 w-4 text-muted-foreground/40" />
                          <div>
                            <p className="text-sm font-medium text-foreground">
                              {status.label}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {status.slug}
                              {status.is_initial && " · Startpunt"}
                              {status.is_terminal && " · Eindpunt"}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {outgoing.length > 0 && (
                            <span className="text-xs text-muted-foreground">
                              {outgoing.length} transitie{outgoing.length !== 1 ? "s" : ""}
                            </span>
                          )}
                          <div
                            className={`h-3 w-3 rounded-full bg-${status.color}-500`}
                            title={`Kleur: ${status.color}`}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Transition overview */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold text-foreground mb-2">
          Toegestane transities
        </h2>
        <p className="text-sm text-muted-foreground mb-4">
          Welke statusovergangen zijn mogelijk
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="py-2 px-3 text-left font-medium text-muted-foreground">
                  Van
                </th>
                <th className="py-2 px-3 text-center font-medium text-muted-foreground">
                  →
                </th>
                <th className="py-2 px-3 text-left font-medium text-muted-foreground">
                  Naar
                </th>
                <th className="py-2 px-3 text-left font-medium text-muted-foreground">
                  Type
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {transitions
                .filter((t) => t.is_active)
                .map((t, idx) => {
                  const fromStatus = statuses.find(
                    (s) => s.id === t.from_status_id
                  );
                  const toStatus = statuses.find(
                    (s) => s.id === t.to_status_id
                  );
                  if (!fromStatus || !toStatus) return null;
                  return (
                    <tr key={idx} className="hover:bg-muted/50">
                      <td className="py-2 px-3 text-foreground">
                        {fromStatus.label}
                      </td>
                      <td className="py-2 px-3 text-center text-muted-foreground">
                        <ChevronRight className="h-4 w-4 inline" />
                      </td>
                      <td className="py-2 px-3 text-foreground">
                        {toStatus.label}
                      </td>
                      <td className="py-2 px-3">
                        <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset bg-slate-50 text-slate-600 ring-slate-500/20">
                          {DEBTOR_TYPE_LABELS[t.debtor_type] ?? t.debtor_type}
                        </span>
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Rules Section ───────────────────────────────────────────────────────────

function RulesSection({
  rules,
  statuses,
  onToggleRule,
}: {
  rules: WorkflowRule[];
  statuses: WFStatus[];
  onToggleRule: (id: string, active: boolean) => void;
}) {
  const getStatusLabel = (id: string) =>
    statuses.find((s) => s.id === id)?.label ?? "Onbekend";

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-foreground">
              Automatiseringsregels
            </h2>
            <p className="text-sm text-muted-foreground">
              Regels die automatisch taken aanmaken bij statuswijzigingen
            </p>
          </div>
        </div>

        {rules.length === 0 ? (
          <div className="py-8 text-center">
            <AlertTriangle className="mx-auto h-8 w-8 text-muted-foreground/30" />
            <p className="mt-2 text-sm text-muted-foreground">
              Geen regels geconfigureerd
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {rules
              .sort((a, b) => a.sort_order - b.sort_order)
              .map((rule) => (
                <div
                  key={rule.id}
                  className={`rounded-lg border p-4 transition-colors ${
                    rule.is_active
                      ? "border-border bg-background"
                      : "border-border/50 bg-muted/30 opacity-60"
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="text-sm font-medium text-foreground">
                          {rule.name}
                        </p>
                        <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset bg-slate-50 text-slate-600 ring-slate-500/20">
                          {DEBTOR_TYPE_LABELS[rule.debtor_type] ?? rule.debtor_type}
                        </span>
                        {rule.auto_execute && (
                          <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset bg-amber-50 text-amber-700 ring-amber-600/20">
                            Auto
                          </span>
                        )}
                      </div>
                      {rule.description && (
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {rule.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <GitBranch className="h-3 w-3" />
                          Bij: {getStatusLabel(rule.trigger_status_id)}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Na {rule.days_delay} dag{rule.days_delay !== 1 ? "en" : ""}
                        </span>
                        <span>
                          Actie: {ACTION_TYPE_LABELS[rule.action_type] ?? rule.action_type}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => onToggleRule(rule.id, !rule.is_active)}
                      className="shrink-0 mt-0.5"
                      title={rule.is_active ? "Deactiveren" : "Activeren"}
                    >
                      {rule.is_active ? (
                        <ToggleRight className="h-6 w-6 text-primary" />
                      ) : (
                        <ToggleLeft className="h-6 w-6 text-muted-foreground" />
                      )}
                    </button>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
