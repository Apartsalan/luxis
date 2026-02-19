"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Briefcase,
  Building2,
  Euro,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  Calendar,
  CheckCircle2,
  Clock,
  FileText,
  CreditCard,
  ArrowUpRight,
  Users,
  Receipt,
  Timer,
  ShieldAlert,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import { QueryError } from "@/components/query-error";
import { useAuth } from "@/hooks/use-auth";
import { useModules } from "@/hooks/use-modules";
import {
  useMyOpenTasks,
  useCompleteTask,
  TASK_TYPE_LABELS,
  type WorkflowTask,
} from "@/hooks/use-workflow";
import { useMyTodayEntries, useTimeEntrySummary } from "@/hooks/use-time-entries";
import { useInvoices, INVOICE_STATUS_LABELS, INVOICE_STATUS_COLORS } from "@/hooks/use-invoices";
import { useKycDashboard } from "@/hooks/use-kyc";

interface DashboardSummary {
  total_active_cases: number;
  total_contacts: number;
  total_outstanding: number;
  total_principal: number;
  total_paid: number;
  cases_by_status: { status: string; count: number }[];
  cases_by_type: { case_type: string; count: number }[];
  cases_this_month: number;
  cases_closed_this_month: number;
}

interface RecentActivity {
  items: {
    id: string;
    case_id: string;
    case_number: string;
    activity_type: string;
    title: string;
    description: string | null;
    user_name: string | null;
    created_at: string;
  }[];
  total: number;
}

const STATUS_LABELS: Record<string, string> = {
  nieuw: "Nieuw",
  "14_dagenbrief": "14-dagenbrief",
  sommatie: "Sommatie",
  dagvaarding: "Dagvaarding",
  vonnis: "Vonnis",
  executie: "Executie",
  betaald: "Betaald",
  afgesloten: "Afgesloten",
};

const STATUS_COLORS: Record<string, string> = {
  nieuw: "bg-blue-500",
  "14_dagenbrief": "bg-blue-400",
  sommatie: "bg-amber-500",
  dagvaarding: "bg-purple-500",
  vonnis: "bg-purple-500",
  executie: "bg-purple-600",
  betaald: "bg-emerald-500",
  afgesloten: "bg-slate-400",
};

const STATUS_BADGE_CLASSES: Record<string, string> = {
  nieuw: "bg-blue-50 text-blue-700 ring-blue-600/20",
  "14_dagenbrief": "bg-blue-50 text-blue-700 ring-blue-600/20",
  sommatie: "bg-amber-50 text-amber-700 ring-amber-600/20",
  dagvaarding: "bg-purple-50 text-purple-700 ring-purple-600/20",
  vonnis: "bg-purple-50 text-purple-700 ring-purple-600/20",
  executie: "bg-purple-50 text-purple-800 ring-purple-600/20",
  betaald: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  afgesloten: "bg-slate-50 text-slate-600 ring-slate-500/20",
};

const ACTIVITY_ICONS: Record<string, typeof Briefcase> = {
  status_change: FileText,
  note: FileText,
  phone_call: FileText,
  email: FileText,
  document: FileText,
  payment: CreditCard,
};

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Goedemorgen";
  if (hour < 18) return "Goedemiddag";
  return "Goedenavond";
}

function getFirstName(fullName: string): string {
  return fullName.split(" ")[0];
}

export default function DashboardPage() {
  const { user } = useAuth();
  const { hasModule } = useModules();

  const {
    data: summary,
    isLoading: summaryLoading,
    isError: summaryError,
    error: summaryErr,
    refetch: refetchSummary,
  } = useQuery<DashboardSummary>({
    queryKey: ["dashboard", "summary"],
    queryFn: async () => {
      const res = await api("/api/dashboard/summary");
      if (!res.ok) throw new Error("Fout bij laden dashboard");
      return res.json();
    },
  });

  const { data: activity, isLoading: activityLoading } =
    useQuery<RecentActivity>({
      queryKey: ["dashboard", "recent-activity"],
      queryFn: async () => {
        const res = await api("/api/dashboard/recent-activity?limit=10");
        if (!res.ok) throw new Error("Fout bij laden activiteit");
        return res.json();
      },
    });

  if (summaryError) {
    return (
      <QueryError
        message={summaryErr?.message}
        onRetry={() => refetchSummary()}
      />
    );
  }

  if (summaryLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="h-10 w-64 rounded-md skeleton" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-28 rounded-xl skeleton" />
          ))}
        </div>
        <div className="h-16 rounded-xl skeleton" />
        <div className="grid gap-6 lg:grid-cols-5">
          <div className="lg:col-span-3 h-80 rounded-xl skeleton" />
          <div className="lg:col-span-2 h-80 rounded-xl skeleton" />
        </div>
      </div>
    );
  }

  const today = new Date().toLocaleDateString("nl-NL", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  const totalPipelineCases =
    summary?.cases_by_status?.reduce((acc, s) => acc + s.count, 0) ?? 0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Greeting */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {getGreeting()},{" "}
            {user ? getFirstName(user.full_name) : ""}
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">{today}</p>
        </div>
        <Link
          href="/zaken/nieuw"
          className="hidden sm:inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
        >
          Nieuwe zaak
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          icon={<Briefcase className="h-5 w-5" />}
          label="Actieve zaken"
          value={summary?.total_active_cases ?? 0}
          subtitle={`${summary?.cases_this_month ?? 0} nieuw deze maand`}
          color="primary"
          href="/zaken"
        />
        <KPICard
          icon={<Users className="h-5 w-5" />}
          label="Relaties"
          value={summary?.total_contacts ?? 0}
          subtitle={`${summary?.cases_closed_this_month ?? 0} zaken afgesloten`}
          color="success"
          href="/relaties"
        />
        {hasModule("incasso") && (
          <KPICard
            icon={<Euro className="h-5 w-5" />}
            label="Openstaand"
            value={formatCurrency(summary?.total_outstanding ?? 0)}
            subtitle={`${formatCurrency(summary?.total_paid ?? 0)} ontvangen`}
            color="warning"
            href="/zaken"
          />
        )}
        {hasModule("tijdschrijven") && <TodayHoursCard />}
        {hasModule("facturatie") && <OpenInvoicesCard />}
      </div>

      {/* Pipeline Bar — incasso only */}
      {hasModule("incasso") && summary?.cases_by_status && summary.cases_by_status.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-card-foreground">
              Pipeline
            </h2>
            <Link
              href="/zaken"
              className="text-xs text-primary hover:underline"
            >
              Alle zaken →
            </Link>
          </div>
          {/* Stacked bar */}
          <div className="flex h-3 rounded-full overflow-hidden gap-0.5">
            {summary.cases_by_status
              .filter((s) => s.count > 0)
              .map((item) => (
                <div
                  key={item.status}
                  className={`${STATUS_COLORS[item.status] ?? "bg-slate-400"} transition-all`}
                  style={{
                    width: `${(item.count / totalPipelineCases) * 100}%`,
                    minWidth: "8px",
                  }}
                  title={`${STATUS_LABELS[item.status] ?? item.status}: ${item.count}`}
                />
              ))}
          </div>
          {/* Legend */}
          <div className="flex flex-wrap gap-x-4 gap-y-1.5 mt-3">
            {summary.cases_by_status
              .filter((s) => s.count > 0)
              .map((item) => (
                <div key={item.status} className="flex items-center gap-1.5">
                  <div
                    className={`h-2.5 w-2.5 rounded-full ${STATUS_COLORS[item.status] ?? "bg-slate-400"}`}
                  />
                  <span className="text-xs text-muted-foreground">
                    {STATUS_LABELS[item.status] ?? item.status}{" "}
                    <span className="font-medium text-foreground">
                      {item.count}
                    </span>
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* KYC Compliance warnings */}
      <KycWarningWidget />

      {/* My Tasks widget */}
      <MyTasksWidget />

      {/* Module widgets row: Uren + Facturen */}
      {(hasModule("tijdschrijven") || hasModule("facturatie")) && (
        <div className={`grid gap-6 ${hasModule("tijdschrijven") && hasModule("facturatie") ? "lg:grid-cols-2" : "lg:grid-cols-1"}`}>
          {hasModule("tijdschrijven") && <WeekSummaryWidget />}
          {hasModule("facturatie") && <RecentInvoicesWidget />}
        </div>
      )}

      {/* Two column: Left (incasso widgets or full-width) + Right (Recent Activity) */}
      <div className={`grid gap-6 ${hasModule("incasso") ? "lg:grid-cols-5" : "lg:grid-cols-1"}`}>
        {/* Left column — incasso specific widgets */}
        {hasModule("incasso") && (
          <div className="lg:col-span-3 space-y-6">
            {/* Action Needed */}
            <div className="rounded-xl border border-border bg-card">
              <div className="flex items-center justify-between px-5 py-4 border-b border-border">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                  <h2 className="text-sm font-semibold text-card-foreground">
                    Actie nodig
                  </h2>
                </div>
              </div>
              <div className="divide-y divide-border">
                {summary?.cases_by_status?.some(
                  (s) =>
                    (s.status === "sommatie" ||
                      s.status === "14_dagenbrief" ||
                      s.status === "nieuw") &&
                    s.count > 0
                ) ? (
                  summary.cases_by_status
                    .filter(
                      (s) =>
                        (s.status === "sommatie" ||
                          s.status === "14_dagenbrief" ||
                          s.status === "nieuw") &&
                        s.count > 0
                    )
                    .map((item) => (
                      <Link
                        key={item.status}
                        href={`/zaken?status=${item.status}`}
                        className="flex items-center justify-between px-5 py-3.5 hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <span
                            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
                              STATUS_BADGE_CLASSES[item.status] ??
                              "bg-slate-50 text-slate-600"
                            }`}
                          >
                            {STATUS_LABELS[item.status] ?? item.status}
                          </span>
                          <span className="text-sm text-muted-foreground">
                            {item.count} {item.count === 1 ? "zaak" : "zaken"}
                          </span>
                        </div>
                        <ArrowRight className="h-4 w-4 text-muted-foreground" />
                      </Link>
                    ))
                ) : (
                  <div className="px-5 py-8 text-center">
                    <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto mb-2" />
                    <p className="text-sm text-muted-foreground">
                      Alles is bij — geen acties nodig
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Cases by status (bars) */}
            <div className="rounded-xl border border-border bg-card p-5">
              <h2 className="text-sm font-semibold text-card-foreground mb-4">
                Zaken per status
              </h2>
              {summary?.cases_by_status && summary.cases_by_status.length > 0 ? (
                <div className="space-y-3">
                  {summary.cases_by_status.map((item) => {
                    const pct =
                      totalPipelineCases > 0
                        ? (item.count / totalPipelineCases) * 100
                        : 0;
                    return (
                      <div key={item.status}>
                        <div className="flex items-center justify-between mb-1.5">
                          <div className="flex items-center gap-2">
                            <div
                              className={`h-2 w-2 rounded-full ${STATUS_COLORS[item.status] ?? "bg-slate-400"}`}
                            />
                            <span className="text-sm text-muted-foreground">
                              {STATUS_LABELS[item.status] ?? item.status}
                            </span>
                          </div>
                          <span className="text-sm font-semibold text-card-foreground tabular-nums">
                            {item.count}
                          </span>
                        </div>
                        <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              STATUS_COLORS[item.status] ?? "bg-slate-400"
                            } transition-all duration-500`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Geen zaken gevonden
                </p>
              )}
            </div>
          </div>
        )}

        {/* Right column: Recent Activity */}
        <div className={hasModule("incasso") ? "lg:col-span-2" : ""}>
          <div className="rounded-xl border border-border bg-card">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold text-card-foreground">
                  Recente activiteit
                </h2>
              </div>
            </div>
            <div className="divide-y divide-border">
              {activityLoading ? (
                <div className="p-5 space-y-3">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="h-12 rounded-md skeleton" />
                  ))}
                </div>
              ) : activity?.items && activity.items.length > 0 ? (
                activity.items.slice(0, 8).map((item) => {
                  const Icon =
                    ACTIVITY_ICONS[item.activity_type] ?? FileText;
                  return (
                    <Link
                      key={item.id}
                      href={`/zaken/${item.case_id}`}
                      className="flex items-start gap-3 px-5 py-3.5 hover:bg-muted/50 transition-colors"
                    >
                      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted">
                        <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-card-foreground truncate">
                          {item.title}
                        </p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {item.case_number} ·{" "}
                          {formatDateShort(item.created_at)}
                        </p>
                      </div>
                    </Link>
                  );
                })
              ) : (
                <div className="px-5 py-8 text-center">
                  <Calendar className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">
                    Nog geen activiteit
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function KPICard({
  icon,
  label,
  value,
  subtitle,
  color,
  href,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  subtitle?: string;
  color: "primary" | "success" | "warning";
  href?: string;
}) {
  const colorClasses = {
    primary: "bg-blue-50 text-blue-600",
    success: "bg-emerald-50 text-emerald-600",
    warning: "bg-amber-50 text-amber-600",
  };

  const content = (
    <div className="rounded-xl border border-border bg-card p-5 hover:shadow-md hover:border-border/80 transition-all group cursor-pointer">
      <div className="flex items-start justify-between">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-lg ${colorClasses[color]}`}
        >
          {icon}
        </div>
        {href && (
          <ArrowUpRight className="h-4 w-4 text-muted-foreground/0 group-hover:text-muted-foreground transition-all" />
        )}
      </div>
      <div className="mt-3">
        <p className="text-2xl font-bold text-card-foreground tabular-nums">
          {value}
        </p>
        <p className="text-sm text-muted-foreground mt-0.5">{label}</p>
        {subtitle && (
          <p className="text-xs text-muted-foreground/70 mt-1">{subtitle}</p>
        )}
      </div>
    </div>
  );

  if (href) {
    return <Link href={href}>{content}</Link>;
  }
  return content;
}

function TodayHoursCard() {
  const { data: todayEntries } = useMyTodayEntries();
  const totalMinutes = todayEntries?.reduce((sum, e) => sum + e.duration_minutes, 0) ?? 0;
  const hours = Math.floor(totalMinutes / 60);
  const mins = totalMinutes % 60;

  return (
    <KPICard
      icon={<Timer className="h-5 w-5" />}
      label="Vandaag gewerkt"
      value={`${hours}:${String(mins).padStart(2, "0")}`}
      subtitle={`${todayEntries?.length ?? 0} registraties`}
      color="primary"
      href="/uren"
    />
  );
}

function OpenInvoicesCard() {
  const { data } = useInvoices({ status: "sent" });
  const totalOpen = data?.items?.reduce((sum, inv) => sum + (inv.total ?? 0), 0) ?? 0;

  return (
    <KPICard
      icon={<Receipt className="h-5 w-5" />}
      label="Open facturen"
      value={formatCurrency(totalOpen)}
      subtitle={`${data?.total ?? 0} verzonden`}
      color="warning"
      href="/facturen"
    />
  );
}

function WeekSummaryWidget() {
  const today = new Date();
  const day = today.getDay();
  const mondayOffset = day === 0 ? -6 : 1 - day;
  const monday = new Date(today);
  monday.setDate(today.getDate() + mondayOffset);
  const friday = new Date(monday);
  friday.setDate(monday.getDate() + 4);

  const dateFrom = monday.toISOString().split("T")[0];
  const dateTo = friday.toISOString().split("T")[0];

  const { data: summary } = useTimeEntrySummary({ date_from: dateFrom, date_to: dateTo });

  const totalHours = summary ? Math.floor(summary.total_minutes / 60) : 0;
  const totalMins = summary ? summary.total_minutes % 60 : 0;
  const billableHours = summary ? Math.floor(summary.billable_minutes / 60) : 0;
  const billableMins = summary ? summary.billable_minutes % 60 : 0;

  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between px-5 py-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Timer className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold text-card-foreground">
            Uren deze week
          </h2>
        </div>
        <Link href="/uren" className="text-xs text-primary hover:underline">
          Alle uren →
        </Link>
      </div>
      <div className="p-5">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-foreground tabular-nums">
              {totalHours}:{String(totalMins).padStart(2, "0")}
            </p>
            <p className="text-xs text-muted-foreground mt-1">Totaal</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-emerald-600 tabular-nums">
              {billableHours}:{String(billableMins).padStart(2, "0")}
            </p>
            <p className="text-xs text-muted-foreground mt-1">Declarabel</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground tabular-nums">
              {summary ? formatCurrency(summary.total_amount) : "—"}
            </p>
            <p className="text-xs text-muted-foreground mt-1">Bedrag</p>
          </div>
        </div>
        {summary && summary.per_case.length > 0 && (
          <div className="mt-4 space-y-2 border-t border-border pt-3">
            {summary.per_case.slice(0, 4).map((cs) => (
              <div key={cs.case_id} className="flex items-center justify-between">
                <Link
                  href={`/zaken/${cs.case_id}`}
                  className="text-sm text-foreground hover:text-primary transition-colors truncate"
                >
                  {cs.case_number}
                </Link>
                <span className="text-sm text-muted-foreground tabular-nums">
                  {Math.floor(cs.total_minutes / 60)}:{String(cs.total_minutes % 60).padStart(2, "0")}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function RecentInvoicesWidget() {
  const { data } = useInvoices({ per_page: 5 });
  const invoices = data?.items ?? [];

  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between px-5 py-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Receipt className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold text-card-foreground">
            Recente facturen
          </h2>
        </div>
        <Link href="/facturen" className="text-xs text-primary hover:underline">
          Alle facturen →
        </Link>
      </div>
      <div className="divide-y divide-border">
        {invoices.length > 0 ? (
          invoices.map((inv) => (
            <Link
              key={inv.id}
              href={`/facturen/${inv.id}`}
              className="flex items-center justify-between px-5 py-3 hover:bg-muted/50 transition-colors"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono font-medium text-foreground">
                    {inv.invoice_number}
                  </span>
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${
                      INVOICE_STATUS_COLORS[inv.status] ?? "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {INVOICE_STATUS_LABELS[inv.status] ?? inv.status}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {inv.contact_name ?? "—"} · {formatDateShort(inv.invoice_date)}
                </p>
              </div>
              <span className="text-sm font-semibold text-foreground tabular-nums ml-4">
                {formatCurrency(inv.total)}
              </span>
            </Link>
          ))
        ) : (
          <div className="px-5 py-8 text-center">
            <Receipt className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">Nog geen facturen</p>
          </div>
        )}
      </div>
    </div>
  );
}

function MyTasksWidget() {
  const { data, isLoading } = useMyOpenTasks(5);
  const completeTask = useCompleteTask();

  const tasks = data?.items ?? [];
  const totalOpen = data?.total ?? 0;

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="h-5 w-32 rounded skeleton mb-4" />
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-14 rounded-lg skeleton" />
          ))}
        </div>
      </div>
    );
  }

  if (tasks.length === 0) return null;

  const now = new Date();

  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between px-5 py-4 border-b border-border">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold text-card-foreground">
            Mijn taken
          </h2>
          {totalOpen > 0 && (
            <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
              {totalOpen}
            </span>
          )}
        </div>
      </div>
      <div className="divide-y divide-border">
        {tasks.map((task: WorkflowTask) => {
          const dueDate = new Date(task.due_date);
          const isOverdue = dueDate < now && task.status !== "completed";
          const isDueSoon =
            !isOverdue &&
            dueDate.getTime() - now.getTime() < 24 * 60 * 60 * 1000;

          return (
            <div
              key={task.id}
              className={`flex items-center gap-3 px-5 py-3.5 ${
                isOverdue ? "bg-red-50/50" : ""
              }`}
            >
              <button
                onClick={() => completeTask.mutate(task.id)}
                disabled={completeTask.isPending}
                className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 border-muted-foreground/30 hover:border-emerald-500 hover:bg-emerald-50 transition-colors"
                title="Markeer als afgerond"
              >
                {completeTask.isPending && (
                  <div className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
                )}
              </button>

              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-card-foreground truncate">
                    {task.title}
                  </p>
                  <span className="inline-flex shrink-0 items-center rounded-full bg-slate-50 px-2 py-0.5 text-[10px] font-medium text-slate-600 ring-1 ring-inset ring-slate-500/20">
                    {TASK_TYPE_LABELS[task.task_type] ?? task.task_type}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  {task.case && (
                    <Link
                      href={`/zaken/${task.case_id}`}
                      className="text-xs text-primary hover:underline"
                    >
                      {task.case.case_number}
                    </Link>
                  )}
                  <span
                    className={`text-xs ${
                      isOverdue
                        ? "text-red-600 font-medium"
                        : isDueSoon
                          ? "text-amber-600"
                          : "text-muted-foreground"
                    }`}
                  >
                    {isOverdue && "Verlopen: "}
                    {formatDateShort(task.due_date)}
                  </span>
                </div>
              </div>

              {isOverdue && (
                <AlertTriangle className="h-4 w-4 text-red-500 shrink-0" />
              )}
            </div>
          );
        })}
      </div>
      {totalOpen > 5 && (
        <div className="px-5 py-3 border-t border-border text-center">
          <span className="text-xs text-muted-foreground">
            +{totalOpen - 5} meer taken openstaand
          </span>
        </div>
      )}
    </div>
  );
}

function KycWarningWidget() {
  const { data: kyc, isLoading } = useKycDashboard();

  if (isLoading || !kyc || kyc.total_issues === 0) return null;

  return (
    <div className="rounded-xl border border-red-200 bg-red-50/50">
      <div className="flex items-center justify-between px-5 py-4 border-b border-red-200">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-red-500" />
          <h2 className="text-sm font-semibold text-red-800">
            WWFT Compliance
          </h2>
          <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
            {kyc.total_issues} {kyc.total_issues === 1 ? "issue" : "issues"}
          </span>
        </div>
      </div>
      <div className="divide-y divide-red-200">
        {kyc.without_kyc.length > 0 && (
          <div className="px-5 py-3">
            <p className="text-xs font-medium text-red-700 mb-2">
              Geen verificatie gestart ({kyc.without_kyc_count})
            </p>
            <div className="flex flex-wrap gap-2">
              {kyc.without_kyc.slice(0, 5).map((item) => (
                <Link
                  key={item.contact_id}
                  href={`/relaties/${item.contact_id}`}
                  className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-xs text-red-700 ring-1 ring-red-200 hover:bg-red-50 transition-colors"
                >
                  {item.contact_type === "company" ? (
                    <Building2 className="h-3 w-3" />
                  ) : (
                    <Users className="h-3 w-3" />
                  )}
                  {item.contact_name}
                </Link>
              ))}
              {kyc.without_kyc.length > 5 && (
                <span className="text-xs text-red-600 self-center">
                  +{kyc.without_kyc.length - 5} meer
                </span>
              )}
            </div>
          </div>
        )}
        {kyc.incomplete.length > 0 && (
          <div className="px-5 py-3">
            <p className="text-xs font-medium text-amber-700 mb-2">
              In behandeling ({kyc.incomplete_count})
            </p>
            <div className="flex flex-wrap gap-2">
              {kyc.incomplete.slice(0, 5).map((item) => (
                <Link
                  key={item.contact_id}
                  href={`/relaties/${item.contact_id}`}
                  className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-xs text-amber-700 ring-1 ring-amber-200 hover:bg-amber-50 transition-colors"
                >
                  {item.contact_name}
                </Link>
              ))}
            </div>
          </div>
        )}
        {kyc.overdue.length > 0 && (
          <div className="px-5 py-3">
            <p className="text-xs font-medium text-red-700 mb-2">
              Review verlopen ({kyc.overdue_count})
            </p>
            <div className="flex flex-wrap gap-2">
              {kyc.overdue.slice(0, 5).map((item) => (
                <Link
                  key={item.contact_id}
                  href={`/relaties/${item.contact_id}`}
                  className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-xs text-red-700 ring-1 ring-red-200 hover:bg-red-50 transition-colors"
                >
                  {item.contact_name}
                  <span className="text-[10px] text-red-500">
                    ({item.days_overdue}d)
                  </span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
