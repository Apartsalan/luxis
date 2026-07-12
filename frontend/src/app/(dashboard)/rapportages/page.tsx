"use client";

import { useState } from "react";
import Link from "next/link";
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Clock,
  AlertTriangle,
  Briefcase,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  useDashboardKPIs,
  useMonthlyStats,
  usePhaseDistribution,
  formatCurrency,
  formatPercentage,
} from "@/hooks/use-reports";

// ── Period filter ────────────────────────────────────────────────────────

type Period = "6" | "12" | "24";

const PERIOD_LABELS: Record<Period, string> = {
  "6": "6 maanden",
  "12": "Dit jaar",
  "24": "2 jaar",
};

// ── Dutch month names ────────────────────────────────────────────────────

const MONTH_NAMES: Record<string, string> = {
  "01": "jan",
  "02": "feb",
  "03": "mrt",
  "04": "apr",
  "05": "mei",
  "06": "jun",
  "07": "jul",
  "08": "aug",
  "09": "sep",
  "10": "okt",
  "11": "nov",
  "12": "dec",
};

function formatMonth(yyyymm: string): string {
  const [, mm] = yyyymm.split("-");
  return MONTH_NAMES[mm] || mm;
}

// CONN-8: zet "YYYY-MM" om naar een datum-range voor drill-down naar /zaken.
function monthRange(yyyymm: string): { from: string; to: string } {
  const [y, m] = yyyymm.split("-").map(Number);
  const lastDay = new Date(y, m, 0).getDate(); // m is 1-gebaseerd → laatste dag van die maand
  return { from: `${yyyymm}-01`, to: `${yyyymm}-${String(lastDay).padStart(2, "0")}` };
}

// ── Page ─────────────────────────────────────────────────────────────────

export default function RapportagesPage() {
  const [period, setPeriod] = useState<Period>("12");
  const { data: kpis, isLoading: kpisLoading } = useDashboardKPIs(
    parseInt(period)
  );
  const { data: monthly, isLoading: monthlyLoading } = useMonthlyStats(
    parseInt(period)
  );
  const { data: phases, isLoading: phasesLoading } = usePhaseDistribution();

  const isLoading = kpisLoading || monthlyLoading || phasesLoading;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Rapportages</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Overzicht van uw praktijk en incasso-prestaties
          </p>
        </div>
        <div className="flex rounded-md border border-border overflow-hidden">
          {(Object.entries(PERIOD_LABELS) as [Period, string][]).map(
            ([key, label]) => (
              <button
                key={key}
                onClick={() => setPeriod(key)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium transition-colors",
                  period === key
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground hover:bg-muted/50",
                  key !== "6" && "border-l border-border"
                )}
              >
                {label}
              </button>
            )
          )}
        </div>
      </div>

      {/* KPI Cards */}
      {isLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="rounded-xl border border-border bg-card p-5">
              <div className="h-4 w-24 rounded skeleton mb-3" />
              <div className="h-8 w-32 rounded skeleton" />
            </div>
          ))}
        </div>
      ) : kpis ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            label="Openstaand"
            value={formatCurrency(kpis.total_outstanding)}
            icon={TrendingUp}
            color="text-orange-600"
            bgColor="bg-orange-50"
            href="/incasso"
          />
          <KpiCard
            label="Geïnd"
            value={formatCurrency(kpis.total_collected)}
            icon={TrendingDown}
            color="text-emerald-600"
            bgColor="bg-emerald-50"
          />
          <KpiCard
            label="Incasso-ratio"
            value={formatPercentage(kpis.collection_rate)}
            icon={BarChart3}
            color="text-blue-600"
            bgColor="bg-blue-50"
          />
          <KpiCard
            label="Gem. doorlooptijd"
            value={`${kpis.avg_days_to_collect} dagen`}
            icon={Clock}
            color="text-purple-600"
            bgColor="bg-purple-50"
          />
        </div>
      ) : null}

      {/* Secondary KPIs */}
      {kpis && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MiniCard label="Actieve zaken" value={kpis.active_cases} href="/zaken" />
          <MiniCard label="Totaal zaken" value={kpis.total_cases} href="/zaken" />
          <MiniCard
            label="Achterstallige taken"
            value={kpis.overdue_tasks}
            warning={kpis.overdue_tasks > 0}
            href="/taken"
          />
          <MiniCard label="Deadlines (7d)" value={kpis.upcoming_deadlines} href="/agenda" />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly chart */}
        <div className="rounded-xl border border-border bg-card">
          <div className="px-5 py-4 border-b border-border">
            <h2 className="text-sm font-semibold text-card-foreground">
              Zaken per maand
            </h2>
          </div>
          <div className="p-5">
            {monthly && monthly.length > 0 ? (
              <MonthlyChart data={monthly} />
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">
                Nog geen data beschikbaar
              </p>
            )}
          </div>
        </div>

        {/* Pipeline distribution */}
        <div className="rounded-xl border border-border bg-card">
          <div className="px-5 py-4 border-b border-border">
            <h2 className="text-sm font-semibold text-card-foreground">
              Faseverdeling
            </h2>
          </div>
          <div className="p-5">
            {phases && phases.length > 0 ? (
              <PipelineChart data={phases} />
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">
                Geen incassozaken in pipeline
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Debtor type distribution */}
      {kpis && Object.keys(kpis.cases_by_debtor_type).length > 0 && (
        <div className="rounded-xl border border-border bg-card">
          <div className="px-5 py-4 border-b border-border">
            <h2 className="text-sm font-semibold text-card-foreground">
              Verdeling type debiteur
            </h2>
          </div>
          <div className="p-5 flex gap-6">
            {Object.entries(kpis.cases_by_debtor_type).map(([type, count]) => (
              <div key={type} className="flex items-center gap-3">
                <div
                  className={cn(
                    "h-3 w-3 rounded-full",
                    type === "Bedrijf" ? "bg-blue-500" : "bg-emerald-500"
                  )}
                />
                <span className="text-sm text-foreground">
                  {type}: <span className="font-semibold">{count}</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Components ───────────────────────────────────────────────────────────

function KpiCard({
  label,
  value,
  icon: Icon,
  color,
  bgColor,
  href,
}: {
  label: string;
  value: string;
  icon: React.ElementType;
  color: string;
  bgColor: string;
  href?: string;
}) {
  const inner = (
    <>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {label}
        </span>
        <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", bgColor)}>
          <Icon className={cn("h-4 w-4", color)} />
        </div>
      </div>
      <p className="text-2xl font-bold text-card-foreground">{value}</p>
    </>
  );
  if (href) {
    return (
      <Link
        href={href}
        className="rounded-xl border border-border bg-card p-5 block hover:bg-muted/40 hover:border-primary/30 transition-colors"
      >
        {inner}
      </Link>
    );
  }
  return <div className="rounded-xl border border-border bg-card p-5">{inner}</div>;
}

function MiniCard({
  label,
  value,
  warning = false,
  href,
}: {
  label: string;
  value: number;
  warning?: boolean;
  href?: string;
}) {
  const content = (
    <>
      <span className="text-xs text-muted-foreground">{label}</span>
      <span
        className={cn(
          "text-lg font-semibold",
          warning ? "text-destructive" : "text-card-foreground"
        )}
      >
        {warning && <AlertTriangle className="h-3.5 w-3.5 inline mr-1" />}
        {value}
      </span>
    </>
  );
  if (href) {
    return (
      <Link
        href={href}
        className="rounded-lg border border-border bg-card px-4 py-3 flex items-center justify-between hover:bg-muted/40 hover:border-primary/30 transition-colors"
      >
        {content}
      </Link>
    );
  }
  return (
    <div className="rounded-lg border border-border bg-card px-4 py-3 flex items-center justify-between">
      {content}
    </div>
  );
}

function MonthlyChart({ data }: { data: { month: string; new_cases: number; closed_cases: number; amount_collected: string }[] }) {
  const maxCases = Math.max(
    ...data.map((d) => Math.max(d.new_cases, d.closed_cases)),
    1
  );

  return (
    <div className="space-y-1">
      {/* Legend */}
      <div className="flex items-center gap-4 mb-4">
        <div className="flex items-center gap-1.5">
          <div className="h-2.5 w-2.5 rounded-sm bg-blue-500" />
          <span className="text-xs text-muted-foreground">Nieuw</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-2.5 w-2.5 rounded-sm bg-emerald-500" />
          <span className="text-xs text-muted-foreground">Gesloten</span>
        </div>
      </div>

      {/* Bars — elke maand linkt naar de dossiers geopend in die maand (CONN-8) */}
      <div className="flex items-end gap-1" style={{ height: "180px" }}>
        {data.map((d) => {
          const { from, to } = monthRange(d.month);
          return (
            <Link
              key={d.month}
              href={`/zaken?date_from=${from}&date_to=${to}`}
              className="flex-1 flex flex-col items-center gap-0.5 h-full justify-end rounded-md hover:bg-muted/50 transition-colors"
              title={`${d.new_cases} nieuw · ${d.closed_cases} gesloten — bekijk dossiers`}
            >
              <div className="flex gap-0.5 items-end flex-1 w-full justify-center">
                <div
                  className="bg-blue-500 rounded-t-sm min-h-[2px]"
                  style={{
                    height: `${(d.new_cases / maxCases) * 100}%`,
                    width: "40%",
                  }}
                />
                <div
                  className="bg-emerald-500 rounded-t-sm min-h-[2px]"
                  style={{
                    height: `${(d.closed_cases / maxCases) * 100}%`,
                    width: "40%",
                  }}
                />
              </div>
              <span className="text-[10px] text-muted-foreground mt-1">
                {formatMonth(d.month)}
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

function PipelineChart({ data }: { data: { phase: string; count: number; total_amount: string }[] }) {
  const totalCases = data.reduce((sum, d) => sum + d.count, 0);

  const STEP_COLORS = [
    "bg-blue-500",
    "bg-yellow-500",
    "bg-orange-500",
    "bg-red-500",
    "bg-purple-500",
    "bg-pink-500",
  ];

  return (
    <div className="space-y-4">
      {/* Stacked bar */}
      <div className="flex rounded-lg overflow-hidden h-8">
        {data.map((d, i) => {
          const pct = totalCases > 0 ? (d.count / totalCases) * 100 : 0;
          if (pct === 0) return null;
          return (
            <div
              key={d.phase}
              className={cn(STEP_COLORS[i % STEP_COLORS.length], "transition-all")}
              style={{ width: `${pct}%` }}
              title={`${d.phase}: ${d.count} zaken`}
            />
          );
        })}
      </div>

      {/* Legend — elke fase linkt naar de incasso-werkstroom (CONN-8) */}
      <div className="space-y-0.5">
        {data.map((d, i) => (
          <Link
            key={d.phase}
            href="/incasso"
            className="flex items-center justify-between rounded-md -mx-1 px-1 py-1 hover:bg-muted/50 transition-colors"
            title="Open de incasso-werkstroom"
          >
            <div className="flex items-center gap-2">
              <div className={cn("h-2.5 w-2.5 rounded-sm", STEP_COLORS[i % STEP_COLORS.length])} />
              <span className="text-xs text-foreground">{d.phase}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-medium text-foreground">{d.count} zaken</span>
              <span className="text-xs text-muted-foreground">{formatCurrency(d.total_amount)}</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
