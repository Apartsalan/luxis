"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Briefcase,
  Users,
  Euro,
  TrendingUp,
  Clock,
  CheckCircle,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";

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
  "14_dagenbrief": "bg-yellow-500",
  sommatie: "bg-orange-500",
  dagvaarding: "bg-red-500",
  vonnis: "bg-purple-500",
  executie: "bg-red-600",
  betaald: "bg-emerald-500",
  afgesloten: "bg-gray-400",
};

const ACTIVITY_ICONS: Record<string, string> = {
  status_change: "📋",
  note: "📝",
  phone_call: "📞",
  email: "📧",
  document: "📄",
  payment: "💰",
};

export default function DashboardPage() {
  const { data: summary, isLoading: summaryLoading } =
    useQuery<DashboardSummary>({
      queryKey: ["dashboard", "summary"],
      queryFn: async () => {
        const res = await api("/api/dashboard/summary");
        if (!res.ok) throw new Error("Failed to fetch dashboard");
        return res.json();
      },
    });

  const { data: activity, isLoading: activityLoading } =
    useQuery<RecentActivity>({
      queryKey: ["dashboard", "recent-activity"],
      queryFn: async () => {
        const res = await api("/api/dashboard/recent-activity?limit=10");
        if (!res.ok) throw new Error("Failed to fetch activity");
        return res.json();
      },
    });

  if (summaryLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="h-8 w-48 rounded-md skeleton" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 rounded-lg skeleton" />
          ))}
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="h-64 rounded-lg skeleton" />
          <div className="h-64 rounded-lg skeleton" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Overzicht van je praktijk
          </p>
        </div>
        <Link
          href="/zaken/nieuw"
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
        >
          Nieuwe zaak
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          icon={<Briefcase className="h-5 w-5" />}
          label="Actieve zaken"
          value={summary?.total_active_cases ?? 0}
          color="primary"
        />
        <KPICard
          icon={<Users className="h-5 w-5" />}
          label="Relaties"
          value={summary?.total_contacts ?? 0}
          color="accent"
        />
        <KPICard
          icon={<Euro className="h-5 w-5" />}
          label="Openstaand"
          value={formatCurrency(summary?.total_outstanding ?? 0)}
          color="warning"
        />
        <KPICard
          icon={<TrendingUp className="h-5 w-5" />}
          label="Totaal ontvangen"
          value={formatCurrency(summary?.total_paid ?? 0)}
          color="success"
        />
      </div>

      {/* Second row */}
      <div className="grid gap-4 md:grid-cols-2">
        <KPICard
          icon={<Clock className="h-5 w-5" />}
          label="Nieuwe zaken deze maand"
          value={summary?.cases_this_month ?? 0}
          color="primary"
        />
        <KPICard
          icon={<CheckCircle className="h-5 w-5" />}
          label="Afgesloten deze maand"
          value={summary?.cases_closed_this_month ?? 0}
          color="success"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Cases by status */}
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-base font-semibold text-card-foreground">
              Zaken per status
            </h2>
            <Link
              href="/zaken"
              className="text-xs text-primary hover:underline"
            >
              Bekijk alle
            </Link>
          </div>
          {summary?.cases_by_status && summary.cases_by_status.length > 0 ? (
            <div className="space-y-3">
              {summary.cases_by_status.map((item) => {
                const total = summary.cases_by_status.reduce(
                  (acc, s) => acc + s.count,
                  0
                );
                const pct = total > 0 ? (item.count / total) * 100 : 0;
                return (
                  <div key={item.status}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-muted-foreground">
                        {STATUS_LABELS[item.status] ?? item.status}
                      </span>
                      <span className="text-sm font-medium text-card-foreground">
                        {item.count}
                      </span>
                    </div>
                    <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          STATUS_COLORS[item.status] ?? "bg-gray-400"
                        } transition-all`}
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

        {/* Recent Activity */}
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-base font-semibold text-card-foreground">
              Recente activiteit
            </h2>
          </div>
          {activityLoading ? (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-14 rounded-md skeleton" />
              ))}
            </div>
          ) : activity?.items && activity.items.length > 0 ? (
            <div className="space-y-1">
              {activity.items.map((item) => (
                <Link
                  key={item.id}
                  href={`/zaken/${item.case_id}`}
                  className="flex items-start gap-3 rounded-lg p-2.5 -mx-1 hover:bg-muted/50 transition-colors"
                >
                  <span className="mt-0.5 text-base">
                    {ACTIVITY_ICONS[item.activity_type] ?? "📌"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-card-foreground truncate">
                      {item.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {item.case_number} &middot; {formatDate(item.created_at)}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Geen activiteit</p>
          )}
        </div>
      </div>
    </div>
  );
}

function KPICard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: "primary" | "accent" | "success" | "warning";
}) {
  const colorClasses = {
    primary: "bg-primary/10 text-primary",
    accent: "bg-accent/10 text-accent",
    success: "bg-success/10 text-success",
    warning: "bg-warning/10 text-warning",
  };

  return (
    <div className="rounded-xl border border-border bg-card p-5 hover:shadow-sm transition-shadow">
      <div className="flex items-center gap-3">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-lg ${colorClasses[color]}`}
        >
          {icon}
        </div>
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-2xl font-bold text-card-foreground">{value}</p>
        </div>
      </div>
    </div>
  );
}
