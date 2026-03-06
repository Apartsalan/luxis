"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

export interface Classification {
  id: string;
  synced_email_id: string;
  case_id: string;
  case_number: string;
  email_subject: string;
  email_from: string;
  email_date: string;

  // Classification
  category: string;
  category_label: string;
  confidence: number;
  reasoning: string;

  // Suggested action
  suggested_action: string;
  suggested_action_label: string;
  suggested_template_key: string | null;
  suggested_template_name: string | null;
  suggested_reminder_days: number | null;

  // Review status
  status: "pending" | "approved" | "rejected" | "executed";
  reviewed_by_name: string | null;
  reviewed_at: string | null;
  review_note: string | null;

  // Execution
  executed_at: string | null;
  execution_result: string | null;

  created_at: string;
}

// ── Hooks ────────────────────────────────────────────────────────────────────

/**
 * List email classifications with optional filters.
 */
export function useClassifications(
  status?: string,
  caseId?: string,
  page = 1,
  perPage = 20,
) {
  return useQuery<Classification[]>({
    queryKey: ["ai-classifications", status, caseId, page, perPage],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (status) params.set("status", status);
      if (caseId) params.set("case_id", caseId);
      params.set("page", String(page));
      params.set("per_page", String(perPage));
      const res = await api(`/api/ai-agent/classifications?${params.toString()}`);
      if (!res.ok) throw new Error("Kon classificaties niet ophalen");
      return res.json();
    },
  });
}

/**
 * Get the classification for a specific synced email.
 */
export function useEmailClassification(syncedEmailId: string | undefined) {
  return useQuery<Classification | null>({
    queryKey: ["ai-classification-email", syncedEmailId],
    queryFn: async () => {
      const res = await api(`/api/ai-agent/email/${syncedEmailId}/classification`);
      if (!res.ok) return null;
      const data = await res.json();
      return data ?? null;
    },
    enabled: !!syncedEmailId,
  });
}

/**
 * Get pending classification count (for badges).
 */
export function usePendingCount() {
  return useQuery<{ count: number }>({
    queryKey: ["ai-pending-count"],
    queryFn: async () => {
      const res = await api("/api/ai-agent/pending-count");
      if (!res.ok) return { count: 0 };
      return res.json();
    },
    refetchInterval: 60 * 1000, // Refresh every minute
  });
}

/**
 * Approve a pending classification.
 */
export function useApproveClassification() {
  const queryClient = useQueryClient();

  return useMutation<Classification, Error, { id: string; note?: string }>({
    mutationFn: async ({ id, note }) => {
      const res = await api(`/api/ai-agent/classifications/${id}/approve`, {
        method: "POST",
        body: JSON.stringify(note ? { note } : {}),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Goedkeuren mislukt");
      }
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["ai-classifications"] });
      queryClient.invalidateQueries({ queryKey: ["ai-classification-email", data.synced_email_id] });
      queryClient.invalidateQueries({ queryKey: ["ai-pending-count"] });
    },
  });
}

/**
 * Reject a pending classification.
 */
export function useRejectClassification() {
  const queryClient = useQueryClient();

  return useMutation<Classification, Error, { id: string; note?: string }>({
    mutationFn: async ({ id, note }) => {
      const res = await api(`/api/ai-agent/classifications/${id}/reject`, {
        method: "POST",
        body: JSON.stringify(note ? { note } : {}),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Afwijzen mislukt");
      }
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["ai-classifications"] });
      queryClient.invalidateQueries({ queryKey: ["ai-classification-email", data.synced_email_id] });
      queryClient.invalidateQueries({ queryKey: ["ai-pending-count"] });
    },
  });
}

/**
 * Execute an approved classification action.
 */
export function useExecuteClassification() {
  const queryClient = useQueryClient();

  return useMutation<Classification, Error, { id: string }>({
    mutationFn: async ({ id }) => {
      const res = await api(`/api/ai-agent/classifications/${id}/execute`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Uitvoeren mislukt");
      }
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["ai-classifications"] });
      queryClient.invalidateQueries({ queryKey: ["ai-classification-email", data.synced_email_id] });
      queryClient.invalidateQueries({ queryKey: ["ai-pending-count"] });
    },
  });
}

/**
 * Manually trigger classification for a specific email.
 */
export function useClassifyEmail() {
  const queryClient = useQueryClient();

  return useMutation<Classification | null, Error, { emailId: string }>({
    mutationFn: async ({ emailId }) => {
      const res = await api(`/api/ai-agent/classify/${emailId}`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Classificatie mislukt");
      }
      const data = await res.json();
      return data ?? null;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["ai-classification-email", variables.emailId] });
      queryClient.invalidateQueries({ queryKey: ["ai-classifications"] });
      queryClient.invalidateQueries({ queryKey: ["ai-pending-count"] });
    },
  });
}
