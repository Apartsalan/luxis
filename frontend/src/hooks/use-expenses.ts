"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────

export interface Expense {
  id: string;
  case_id: string | null;
  description: string;
  amount: number;
  expense_date: string;
  category: string;
  billable: boolean;
  invoiced: boolean;
  tax_type: string;
  file_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface ExpenseCreateInput {
  case_id?: string;
  description: string;
  amount: number;
  expense_date: string;
  category?: string;
  billable?: boolean;
  tax_type?: string;
  file_id?: string;
}

interface ExpenseUpdateInput {
  description?: string;
  amount?: number;
  expense_date?: string;
  category?: string;
  billable?: boolean;
  tax_type?: string;
  file_id?: string | null;
}

// ── Category labels ─────────────────────────────────────────────────────

export const EXPENSE_CATEGORY_LABELS: Record<string, string> = {
  griffierecht: "Griffierecht",
  deurwaarder: "Deurwaarderskosten",
  kvk: "KvK-uittreksel",
  overig: "Overig",
};

// ── Hooks ────────────────────────────────────────────────────────────────

export function useExpenses(params?: {
  case_id?: string;
  billable_only?: boolean;
  uninvoiced_only?: boolean;
}) {
  const case_id = params?.case_id ?? "";
  const billable_only = params?.billable_only ?? false;
  const uninvoiced_only = params?.uninvoiced_only ?? false;

  return useQuery<Expense[]>({
    queryKey: ["expenses", { case_id, billable_only, uninvoiced_only }],
    queryFn: async () => {
      const qp = new URLSearchParams();
      if (case_id) qp.set("case_id", case_id);
      if (billable_only) qp.set("billable_only", "true");
      if (uninvoiced_only) qp.set("uninvoiced_only", "true");
      const res = await api(`/api/expenses?${qp}`);
      if (!res.ok) throw new Error("Kan verschotten niet laden");
      return res.json();
    },
  });
}

export function useCreateExpense() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: ExpenseCreateInput) => {
      const res = await api("/api/expenses", {
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
      qc.invalidateQueries({ queryKey: ["expenses"] });
    },
  });
}

export function useUpdateExpense() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: ExpenseUpdateInput;
    }) => {
      const res = await api(`/api/expenses/${id}`, {
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
      qc.invalidateQueries({ queryKey: ["expenses"] });
    },
  });
}

export function useDeleteExpense() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/expenses/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Verwijderen mislukt");
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["expenses"] });
    },
  });
}
