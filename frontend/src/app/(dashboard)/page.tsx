"use client";

import { useQuery } from "@tanstack/react-query";
import { Briefcase, Users, Euro, TrendingUp, Clock, CheckCircle } from "lucide-react";
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

const TYPE_LABELS: Record<string, string> = {
  incasso: "Incasso",
  insolventie: "Insolventie",
  advies: "Advies",
  overig: "Overig",
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
  const { data: summary, isLoading: summaryLoading } = useQuery<DashboardSummary>({
    queryKey: ["dashboard", "summary"],
    queryFn: async () => {
      const res = await api("/api/dashboard/summary");
      if (!res.ok) throw new Error("Failed to fetch dashboard");
      return res.json();
    },
  });

  const { data: activity, isLoading: activityLoading } = useQuery<RecentActivity>({
    queryKey: ["dashboard", "recent-activity"],
    queryFn: async () => {
      const res = await api("/api/dashboard/recent-activity?limit=10");
      if (!res.ok) throw new Error("Failed to fetch activity");
      return res.json();
    },
  });

  if (summaryLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-navy-200 border-t-navy-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-navy-800">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Overzicht van je praktijk
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          icon={<Briefcase className="h-5 w-5" />}
          label="Actieve zaken"
          value={summary?.total_active_cases ?? 0}
          color="navy"
        />
        <KPICard
          icon={<Users className="h-5 w-5" />}
          label="Relaties"
          value={summary?.total_contacts ?? 0}
          color="navy"
        />
        <KPICard
          icon={<Euro className="h-5 w-5" />}
          label="Openstaand"
          value={formatCurrency(summary?.total_outstanding ?? 0)}
          color="gold"
        />
        <KPICard
          icon={<TrendingUp className="h-5 w-5" />}
          label="Totaal ontvangen"
          value={formatCurrency(summary?.total_paid ?? 0)}
          color="green"
        />
      </div>

      {/* Second row */}
      <div className="grid gap-4 md:grid-cols-2">
        <KPICard
          icon={<Clock className="h-5 w-5" />}
          label="Nieuwe zaken deze maand"
          value={summary?.cases_this_month ?? 0}
          color="navy"
        />
        <KPICard
          icon={<CheckCircle className="h-5 w-5" />}
          label="Afgesloten deze maand"
          value={summary?.cases_closed_this_month ?? 0}
          color="green"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Cases by status */}
        <div className="rounded-lg border border-border bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold text-navy-800">
            Zaken per status
          </h2>
          {summary?.cases_by_status && summary.cases_by_status.length > 0 ? (
            <div className="space-y-3">
              {summary.cases_by_status.map((item) => (
                <div
                  key={item.status}
                  className="flex items-center justify-between"
                >
                  <span className="text-sm text-navy-600">
                    {STATUS_LABELS[item.status] ?? item.status}
                  </span>
                  <span className="inline-flex items-center rounded-full bg-navy-100 px-3 py-1 text-xs font-medium text-navy-700">
                    {item.count}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Geen zaken gevonden</p>
          )}
        </div>

        {/* Recent Activity */}
        <div className="rounded-lg border border-border bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold text-navy-800">
            Recente activiteit
          </h2>
          {activityLoading ? (
            <div className="flex justify-center py-8">
              <div className="h-6 w-6 animate-spin rounded-full border-4 border-navy-200 border-t-navy-500" />
            </div>
          ) : activity?.items && activity.items.length > 0 ? (
            <div className="space-y-3">
              {activity.items.map((item) => (
                <div
                  key={item.id}
                  className="flex items-start gap-3 rounded-md border border-border p-3"
                >
                  <span className="text-lg">
                    {ACTIVITY_ICONS[item.activity_type] ?? "📌"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-navy-800 truncate">
                      {item.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {item.case_number} &middot;{" "}
                      {formatDate(item.created_at)}
                    </p>
                  </div>
                </div>
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
  color: "navy" | "gold" | "green";
}) {
  const colorClasses = {
    navy: "bg-navy-50 text-navy-500",
    gold: "bg-gold-50 text-gold-500",
    green: "bg-emerald-50 text-emerald-600",
  };

  return (
    <div className="rounded-lg border border-border bg-white p-6">
      <div className="flex items-center gap-3">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-lg ${colorClasses[color]}`}
        >
          {icon}
        </div>
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-2xl font-bold text-navy-800">{value}</p>
        </div>
      </div>
    </div>
  );
}
