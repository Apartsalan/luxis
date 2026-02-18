"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ─── Types ────────────────────────────────────────────────────────
export interface DashboardKPIs {
  total_cases: number;
  active_cases: number;
  total_outstanding: string; // Decimal string
  total_collected: string;
  collection_rate: number; // Percentage 0-100
  avg_days_to_collect: number;
  cases_by_phase: Record<string, number>;
  cases_by_debtor_type: Record<string, number>;
  overdue_tasks: number;
  upcoming_deadlines: number;
}

export interface MonthlyStats {
  month: string; // YYYY-MM
  new_cases: number;
  closed_cases: number;
  amount_collected: string;
  amount_outstanding: string;
}

export interface PhaseDistribution {
  phase: string;
  count: number;
  total_amount: string;
}

// ─── Queries ──────────────────────────────────────────────────────
export function useDashboardKPIs() {
  return useQuery<DashboardKPIs>({
    queryKey: ["reports", "kpis"],
    queryFn: async () => {
      const res = await api("/api/reports/kpis");
      if (!res.ok) throw new Error("Kan KPI's niet ophalen");
      return res.json();
    },
    staleTime: 60_000, // Cache KPIs for 1 minute
  });
}

export function useMonthlyStats(months = 12) {
  return useQuery<MonthlyStats[]>({
    queryKey: ["reports", "monthly", months],
    queryFn: async () => {
      const res = await api(`/api/reports/monthly?months=${months}`);
      if (!res.ok) throw new Error("Kan maandstatistieken niet ophalen");
      return res.json();
    },
    staleTime: 60_000,
  });
}

export function usePhaseDistribution() {
  return useQuery<PhaseDistribution[]>({
    queryKey: ["reports", "phase-distribution"],
    queryFn: async () => {
      const res = await api("/api/reports/phase-distribution");
      if (!res.ok) throw new Error("Kan faseverdeling niet ophalen");
      return res.json();
    },
    staleTime: 60_000,
  });
}

// ─── Helpers ──────────────────────────────────────────────────────
export function formatCurrency(value: string | number): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  return new Intl.NumberFormat("nl-NL", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
  }).format(num);
}

export function formatPercentage(value: number): string {
  return `${value.toFixed(1)}%`;
}
