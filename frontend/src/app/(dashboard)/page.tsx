"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Briefcase,
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
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import { QueryError } from "@/components/query-error";
import { useAuth } from "@/hooks/use-auth";

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

      {/* KPI Cards — 3 most important */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KPICard
          icon={<Briefcase className="h-5 w-5" />}
          label="Actieve zaken"
          value={summary?.total_active_cases ?? 0}
          subtitle={`${summary?.cases_this_month ?? 0} nieuw deze maand`}
          color="primary"
          href="/zaken"
        />
        <KPICard
          icon={<Euro className="h-5 w-5" />}
          label="Openstaand"
          value={formatCurrency(summary?.total_outstanding ?? 0)}
          subtitle={`${summary?.total_contacts ?? 0} relaties`}
          color="warning"
          href="/relaties"
        />
        <KPICard
          icon={<TrendingUp className="h-5 w-5" />}
          label="Ontvangen"
          value={formatCurrency(summary?.total_paid ?? 0)}
          subtitle={`${summary?.cases_closed_this_month ?? 0} afgesloten deze maand`}
          color="success"
          href="/zaken"
        />
      </div>

      {/* Pipeline Bar */}
      {summary?.cases_by_status && summary.cases_by_status.length > 0 && (
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

      {/* Two column: Action Needed + Recent Activity */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Left column */}
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

        {/* Right column: Recent Activity */}
        <div className="lg:col-span-2">
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
