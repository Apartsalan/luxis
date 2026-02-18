"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────

export interface TimeEntry {
  id: string;
  user: { id: string; full_name: string };
  case: { id: string; case_number: string };
  date: string;
  duration_minutes: number;
  description: string | null;
  activity_type: string;
  billable: boolean;
  hourly_rate: number | null;
  created_at: string;
  updated_at: string;
}

export interface CaseTimeSummary {
  case_id: string;
  case_number: string;
  total_minutes: number;
  billable_minutes: number;
  total_amount: number;
}

export interface TimeEntrySummary {
  total_minutes: number;
  billable_minutes: number;
  non_billable_minutes: number;
  total_amount: number;
  per_case: CaseTimeSummary[];
}

interface TimeEntryCreateInput {
  case_id: string;
  date: string;
  duration_minutes: number;
  description?: string;
  activity_type?: string;
  billable?: boolean;
  hourly_rate?: number;
}

interface TimeEntryUpdateInput {
  case_id?: string;
  date?: string;
  duration_minutes?: number;
  description?: string;
  activity_type?: string;
  billable?: boolean;
  hourly_rate?: number;
}

// ── Activity type labels ─────────────────────────────────────────────────

export const ACTIVITY_TYPE_LABELS: Record<string, string> = {
  correspondence: "Correspondentie",
  meeting: "Bespreking",
  phone: "Telefonisch",
  research: "Onderzoek",
  court: "Zitting",
  travel: "Reistijd",
  drafting: "Opstellen stukken",
  other: "Overig",
};

// ── Hooks ────────────────────────────────────────────────────────────────

export function useTimeEntries(params?: {
  case_id?: string;
  user_id?: string;
  date_from?: string;
  date_to?: string;
  billable?: boolean;
}) {
  const case_id = params?.case_id ?? "";
  const user_id = params?.user_id ?? "";
  const date_from = params?.date_from ?? "";
  const date_to = params?.date_to ?? "";
  const billable = params?.billable;

  return useQuery<TimeEntry[]>({
    queryKey: ["time-entries", { case_id, user_id, date_from, date_to, billable }],
    queryFn: async () => {
      const qp = new URLSearchParams();
      if (case_id) qp.set("case_id", case_id);
      if (user_id) qp.set("user_id", user_id);
      if (date_from) qp.set("date_from", date_from);
      if (date_to) qp.set("date_to", date_to);
      if (billable !== undefined) qp.set("billable", String(billable));
      const res = await api(`/api/time-entries?${qp}`);
      if (!res.ok) throw new Error("Kan tijdregistraties niet laden");
      return res.json();
    },
  });
}

export function useCreateTimeEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: TimeEntryCreateInput) => {
      const res = await api("/api/time-entries", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Aanmaken mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["time-entries"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useUpdateTimeEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TimeEntryUpdateInput }) => {
      const res = await api(`/api/time-entries/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Bijwerken mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["time-entries"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDeleteTimeEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/time-entries/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Verwijderen mislukt");
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["time-entries"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useTimeEntrySummary(params?: {
  case_id?: string;
  user_id?: string;
  date_from?: string;
  date_to?: string;
}) {
  const case_id = params?.case_id ?? "";
  const user_id = params?.user_id ?? "";
  const date_from = params?.date_from ?? "";
  const date_to = params?.date_to ?? "";

  return useQuery<TimeEntrySummary>({
    queryKey: ["time-entries", "summary", { case_id, user_id, date_from, date_to }],
    queryFn: async () => {
      const qp = new URLSearchParams();
      if (case_id) qp.set("case_id", case_id);
      if (user_id) qp.set("user_id", user_id);
      if (date_from) qp.set("date_from", date_from);
      if (date_to) qp.set("date_to", date_to);
      const res = await api(`/api/time-entries/summary?${qp}`);
      if (!res.ok) throw new Error("Kan samenvatting niet laden");
      return res.json();
    },
  });
}

export function useMyTodayEntries() {
  return useQuery<TimeEntry[]>({
    queryKey: ["time-entries", "my-today"],
    queryFn: async () => {
      const res = await api("/api/time-entries/my/today");
      if (!res.ok) throw new Error("Kan registraties niet laden");
      return res.json();
    },
    refetchInterval: 60_000, // refresh every minute for timer widget
  });
}
