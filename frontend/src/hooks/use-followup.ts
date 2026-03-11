"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

export interface FollowupRecommendation {
  id: string;
  case_id: string;
  case_number: string;
  client_name: string | null;
  opposing_party_name: string | null;

  incasso_step_id: string;
  step_name: string;

  recommended_action: string;
  action_label: string;
  reasoning: string;
  days_in_step: number;
  outstanding_amount: string;
  urgency: string;
  urgency_label: string;

  status: string;
  reviewed_by_name: string | null;
  reviewed_at: string | null;
  review_note: string | null;

  executed_at: string | null;
  execution_result: string | null;
  generated_document_id: string | null;

  created_at: string;
}

export interface FollowupList {
  items: FollowupRecommendation[];
  total: number;
  page: number;
  per_page: number;
}

export interface FollowupStats {
  pending: number;
  approved: number;
  rejected: number;
  executed: number;
}

// ── Hooks ────────────────────────────────────────────────────────────────────

export function useFollowupRecommendations(
  status?: string,
  page = 1,
  perPage = 20,
) {
  return useQuery<FollowupList>({
    queryKey: ["followup", status, page, perPage],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (status) params.set("status", status);
      params.set("page", String(page));
      params.set("per_page", String(perPage));
      const res = await api(`/api/followup?${params.toString()}`);
      if (!res.ok) throw new Error("Kon aanbevelingen niet ophalen");
      return res.json();
    },
  });
}

export function useFollowupStats() {
  return useQuery<FollowupStats>({
    queryKey: ["followup-stats"],
    queryFn: async () => {
      const res = await api("/api/followup/stats");
      if (!res.ok) return { pending: 0, approved: 0, rejected: 0, executed: 0 };
      return res.json();
    },
    refetchInterval: 60_000,
  });
}

export function useFollowupRecommendation(id: string | undefined) {
  return useQuery<FollowupRecommendation>({
    queryKey: ["followup", id],
    queryFn: async () => {
      const res = await api(`/api/followup/${id}`);
      if (!res.ok) throw new Error("Kon aanbeveling niet ophalen");
      return res.json();
    },
    enabled: !!id,
  });
}

export function useFollowupPendingCount() {
  return useQuery<{ count: number }>({
    queryKey: ["followup-pending-count"],
    queryFn: async () => {
      const res = await api("/api/followup/stats");
      if (!res.ok) return { count: 0 };
      const stats: FollowupStats = await res.json();
      return { count: stats.pending };
    },
    refetchInterval: 60_000,
  });
}

export function useFollowupForCase(caseId: string | undefined) {
  return useQuery<FollowupList>({
    queryKey: ["followup", "case", caseId, "pending"],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.set("status", "pending");
      params.set("case_id", caseId!);
      params.set("per_page", "1");
      const res = await api(`/api/followup?${params.toString()}`);
      if (!res.ok) return { items: [], total: 0, page: 1, per_page: 1 };
      return res.json();
    },
    enabled: !!caseId,
  });
}

export function useApproveAndExecuteFollowup() {
  const queryClient = useQueryClient();

  return useMutation<FollowupRecommendation, Error, { id: string }>({
    mutationFn: async ({ id }) => {
      const res = await api(`/api/followup/${id}/approve-and-execute`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Goedkeuren en uitvoeren mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["followup"] });
      queryClient.invalidateQueries({ queryKey: ["followup-stats"] });
      queryClient.invalidateQueries({ queryKey: ["followup-pending-count"] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
  });
}

export function useApproveFollowup() {
  const queryClient = useQueryClient();

  return useMutation<FollowupRecommendation, Error, { id: string }>({
    mutationFn: async ({ id }) => {
      const res = await api(`/api/followup/${id}/approve`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Goedkeuren mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["followup"] });
      queryClient.invalidateQueries({ queryKey: ["followup-stats"] });
      queryClient.invalidateQueries({ queryKey: ["followup-pending-count"] });
    },
  });
}

export function useRejectFollowup() {
  const queryClient = useQueryClient();

  return useMutation<FollowupRecommendation, Error, { id: string; note?: string }>({
    mutationFn: async ({ id, note }) => {
      const res = await api(`/api/followup/${id}/reject`, {
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
      queryClient.invalidateQueries({ queryKey: ["followup"] });
      queryClient.invalidateQueries({ queryKey: ["followup-stats"] });
      queryClient.invalidateQueries({ queryKey: ["followup-pending-count"] });
    },
  });
}

export function useExecuteFollowup() {
  const queryClient = useQueryClient();

  return useMutation<FollowupRecommendation, Error, { id: string }>({
    mutationFn: async ({ id }) => {
      const res = await api(`/api/followup/${id}/execute`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Uitvoeren mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["followup"] });
      queryClient.invalidateQueries({ queryKey: ["followup-stats"] });
      queryClient.invalidateQueries({ queryKey: ["followup-pending-count"] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
  });
}
