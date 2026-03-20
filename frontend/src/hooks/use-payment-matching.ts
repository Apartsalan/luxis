"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

export interface BankStatementImport {
  id: string;
  filename: string;
  bank: string;
  account_iban: string | null;
  status: string;
  error_message: string | null;
  total_rows: number;
  credit_count: number;
  debit_count: number;
  skipped_count: number;
  matched_count: number;
  imported_by_name: string | null;
  created_at: string;
}

export interface BankStatementImportList {
  items: BankStatementImport[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface PaymentMatch {
  id: string;
  transaction_id: string;
  case_id: string;
  transaction_date: string;
  amount: string;
  counterparty_name: string | null;
  counterparty_iban: string | null;
  description: string | null;
  case_number: string;
  client_name: string | null;
  opposing_party_name: string | null;
  match_method: string;
  match_method_label: string;
  confidence: number;
  match_details: string | null;
  status: string;
  reviewed_by_name: string | null;
  reviewed_at: string | null;
  review_note: string | null;
  executed_at: string | null;
  payment_id: string | null;
  derdengelden_id: string | null;
  created_at: string;
}

export interface PaymentMatchList {
  items: PaymentMatch[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface PaymentMatchStats {
  pending: number;
  approved: number;
  rejected: number;
  executed: number;
  total_amount_pending: string;
}

// ── Import hooks ─────────────────────────────────────────────────────────────

export function useImports(page = 1, perPage = 20) {
  return useQuery<BankStatementImportList>({
    queryKey: ["payment-imports", page, perPage],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("per_page", String(perPage));
      const res = await api(`/api/payment-matching/imports?${params}`);
      if (!res.ok) throw new Error("Kon imports niet ophalen");
      return res.json();
    },
  });
}

export function useUploadCSV() {
  const queryClient = useQueryClient();

  return useMutation<BankStatementImport, Error, File>({
    mutationFn: async (file) => {
      const formData = new FormData();
      formData.append("file", file);

      const token = localStorage.getItem("luxis_access_token");
      const res = await fetch("/api/payment-matching/import?bank=rabobank", {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Upload mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payment-imports"] });
      queryClient.invalidateQueries({ queryKey: ["payment-matches"] });
      queryClient.invalidateQueries({ queryKey: ["payment-match-stats"] });
      queryClient.invalidateQueries({ queryKey: ["payment-pending-count"] });
    },
  });
}

export function useRematchImport() {
  const queryClient = useQueryClient();

  return useMutation<{ matched: number }, Error, string>({
    mutationFn: async (importId) => {
      const res = await api(`/api/payment-matching/imports/${importId}/rematch`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Opnieuw matchen mislukt");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payment-imports"] });
      queryClient.invalidateQueries({ queryKey: ["payment-matches"] });
      queryClient.invalidateQueries({ queryKey: ["payment-match-stats"] });
      queryClient.invalidateQueries({ queryKey: ["payment-pending-count"] });
    },
  });
}

// ── Match hooks ──────────────────────────────────────────────────────────────

export function usePaymentMatches(status?: string, page = 1, perPage = 20) {
  return useQuery<PaymentMatchList>({
    queryKey: ["payment-matches", status, page, perPage],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (status) params.set("status", status);
      params.set("page", String(page));
      params.set("per_page", String(perPage));
      const res = await api(`/api/payment-matching/matches?${params}`);
      if (!res.ok) throw new Error("Kon matches niet ophalen");
      return res.json();
    },
  });
}

export function usePaymentMatchStats() {
  return useQuery<PaymentMatchStats>({
    queryKey: ["payment-match-stats"],
    queryFn: async () => {
      const res = await api("/api/payment-matching/matches/stats");
      if (!res.ok)
        return {
          pending: 0,
          approved: 0,
          rejected: 0,
          executed: 0,
          total_amount_pending: "0.00",
        };
      return res.json();
    },
    refetchInterval: 60_000,
  });
}

export function usePaymentPendingCount() {
  return useQuery<{ count: number }>({
    queryKey: ["payment-pending-count"],
    queryFn: async () => {
      const res = await api("/api/payment-matching/matches/stats");
      if (!res.ok) return { count: 0 };
      const stats: PaymentMatchStats = await res.json();
      return { count: stats.pending };
    },
    refetchInterval: 60_000,
  });
}

export function useApproveAndExecuteMatch() {
  const queryClient = useQueryClient();

  return useMutation<PaymentMatch, Error, { id: string }>({
    mutationFn: async ({ id }) => {
      const res = await api(
        `/api/payment-matching/matches/${id}/approve-and-execute`,
        { method: "POST" },
      );
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Goedkeuren mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payment-matches"] });
      queryClient.invalidateQueries({ queryKey: ["payment-match-stats"] });
      queryClient.invalidateQueries({ queryKey: ["payment-pending-count"] });
      queryClient.invalidateQueries({ queryKey: ["payment-imports"] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
  });
}

export function useRejectMatch() {
  const queryClient = useQueryClient();

  return useMutation<PaymentMatch, Error, { id: string; note?: string }>({
    mutationFn: async ({ id, note }) => {
      const res = await api(`/api/payment-matching/matches/${id}/reject`, {
        method: "POST",
        body: JSON.stringify(note ? { note } : {}),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Afwijzen mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payment-matches"] });
      queryClient.invalidateQueries({ queryKey: ["payment-match-stats"] });
      queryClient.invalidateQueries({ queryKey: ["payment-pending-count"] });
    },
  });
}

export function useApproveAllMatches() {
  const queryClient = useQueryClient();

  return useMutation<
    { executed: number },
    Error,
    { minConfidence?: number; importId?: string }
  >({
    mutationFn: async ({ minConfidence = 85, importId }) => {
      const params = new URLSearchParams();
      params.set("min_confidence", String(minConfidence));
      if (importId) params.set("import_id", importId);
      const res = await api(
        `/api/payment-matching/matches/approve-all?${params}`,
        { method: "POST" },
      );
      if (!res.ok) throw new Error("Bulk goedkeuren mislukt");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["payment-matches"] });
      queryClient.invalidateQueries({ queryKey: ["payment-match-stats"] });
      queryClient.invalidateQueries({ queryKey: ["payment-pending-count"] });
      queryClient.invalidateQueries({ queryKey: ["payment-imports"] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
  });
}
