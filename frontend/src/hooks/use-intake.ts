"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

export interface IntakeResponse {
  id: string;
  synced_email_id: string;
  email_subject: string;
  email_from: string;
  email_date: string | null;
  client_name: string | null;
  debtor_name: string | null;
  debtor_email: string | null;
  debtor_kvk: string | null;
  debtor_address: string | null;
  debtor_city: string | null;
  debtor_postcode: string | null;
  debtor_type: string;
  invoice_number: string | null;
  invoice_date: string | null;
  due_date: string | null;
  principal_amount: string | null;
  description: string | null;
  ai_model: string;
  ai_confidence: number | null;
  ai_reasoning: string;
  has_pdf_data: boolean;
  status: string;
  error_message: string | null;
  reviewed_by_name: string | null;
  reviewed_at: string | null;
  review_note: string | null;
  created_case_id: string | null;
  created_case_number: string | null;
  created_contact_id: string | null;
  created_contact_name: string | null;
  created_at: string;
}

export interface IntakeUpdateData {
  debtor_name?: string;
  debtor_email?: string;
  debtor_kvk?: string;
  debtor_address?: string;
  debtor_city?: string;
  debtor_postcode?: string;
  debtor_type?: string;
  invoice_number?: string;
  invoice_date?: string;
  due_date?: string;
  principal_amount?: string;
  description?: string;
}

// ── Hooks ────────────────────────────────────────────────────────────────────

export function useIntakes(
  status?: string,
  page = 1,
  perPage = 20,
) {
  return useQuery<IntakeResponse[]>({
    queryKey: ["intakes", status, page, perPage],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (status) params.set("status", status);
      params.set("page", String(page));
      params.set("per_page", String(perPage));
      const res = await api(`/api/intake?${params.toString()}`);
      if (!res.ok) throw new Error("Kon intake verzoeken niet ophalen");
      return res.json();
    },
  });
}

export function useIntake(id: string | undefined) {
  return useQuery<IntakeResponse>({
    queryKey: ["intakes", id],
    queryFn: async () => {
      const res = await api(`/api/intake/${id}`);
      if (!res.ok) throw new Error("Kon intake verzoek niet ophalen");
      return res.json();
    },
    enabled: !!id,
  });
}

export function useIntakePendingCount() {
  return useQuery<{ count: number }>({
    queryKey: ["intake-pending-count"],
    queryFn: async () => {
      const res = await api("/api/intake/pending-count");
      if (!res.ok) return { count: 0 };
      return res.json();
    },
    refetchInterval: 60_000,
  });
}

export function useUpdateIntake() {
  const queryClient = useQueryClient();

  return useMutation<IntakeResponse, Error, { id: string; data: IntakeUpdateData }>({
    mutationFn: async ({ id, data }) => {
      const res = await api(`/api/intake/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Bijwerken mislukt");
      }
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["intakes"] });
      queryClient.setQueryData(["intakes", data.id], data);
    },
  });
}

export function useApproveIntake() {
  const queryClient = useQueryClient();

  return useMutation<IntakeResponse, Error, { id: string; note?: string }>({
    mutationFn: async ({ id, note }) => {
      const res = await api(`/api/intake/${id}/approve`, {
        method: "POST",
        body: JSON.stringify(note ? { note } : {}),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Goedkeuren mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["intakes"] });
      queryClient.invalidateQueries({ queryKey: ["intake-pending-count"] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
  });
}

export function useRejectIntake() {
  const queryClient = useQueryClient();

  return useMutation<IntakeResponse, Error, { id: string; note?: string }>({
    mutationFn: async ({ id, note }) => {
      const res = await api(`/api/intake/${id}/reject`, {
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
      queryClient.invalidateQueries({ queryKey: ["intakes"] });
      queryClient.invalidateQueries({ queryKey: ["intake-pending-count"] });
    },
  });
}

export function useProcessIntake() {
  const queryClient = useQueryClient();

  return useMutation<IntakeResponse, Error, { id: string }>({
    mutationFn: async ({ id }) => {
      const res = await api(`/api/intake/${id}/process`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Verwerking mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["intakes"] });
      queryClient.invalidateQueries({ queryKey: ["intake-pending-count"] });
    },
  });
}
