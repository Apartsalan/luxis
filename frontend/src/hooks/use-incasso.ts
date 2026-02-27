"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────

export interface PipelineStep {
  id: string;
  name: string;
  sort_order: number;
  min_wait_days: number;
  max_wait_days: number;
  template_id: string | null;
  template_type: string | null;
  template_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export type DeadlineStatus = "green" | "orange" | "red" | "gray";

export interface CaseInPipeline {
  id: string;
  case_number: string;
  client_name: string;
  opposing_party_name: string | null;
  total_principal: number;
  total_paid: number;
  outstanding: number;
  days_in_step: number;
  incasso_step_id: string | null;
  status: string;
  date_opened: string;
  deadline_status: DeadlineStatus;
}

export interface PipelineColumn {
  step: PipelineStep;
  cases: CaseInPipeline[];
  count: number;
}

export interface PipelineOverview {
  columns: PipelineColumn[];
  unassigned: CaseInPipeline[];
  total_cases: number;
}

export interface BatchBlocker {
  case_id: string;
  case_number: string;
  reason: string;
}

export interface BatchPreviewResponse {
  action: string;
  total_selected: number;
  ready: number;
  blocked: BatchBlocker[];
  needs_step_assignment: CaseInPipeline[];
}

export interface BatchActionResult {
  action: string;
  processed: number;
  skipped: number;
  errors: string[];
  generated_document_ids: string[];
}

export interface QueueCounts {
  ready_next_step: number;
  wik_expired: number;
  action_required: number;
}

// ── Pipeline Steps Hooks ─────────────────────────────────────────────────

export function useIncassoPipelineSteps(activeOnly = true) {
  return useQuery<PipelineStep[]>({
    queryKey: ["incasso-pipeline-steps", { activeOnly }],
    queryFn: async () => {
      const res = await api(`/api/incasso/pipeline-steps?active_only=${activeOnly}`);
      if (!res.ok) throw new Error("Fout bij ophalen pipeline stappen");
      return res.json();
    },
  });
}

export function useCreatePipelineStep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      name: string;
      sort_order: number;
      min_wait_days: number;
      max_wait_days?: number;
      template_id?: string | null;
      template_type?: string | null;
    }) => {
      const res = await api("/api/incasso/pipeline-steps", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Fout bij aanmaken stap");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incasso-pipeline-steps"] });
    },
  });
}

export function useUpdatePipelineStep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      ...data
    }: {
      id: string;
      name?: string;
      sort_order?: number;
      min_wait_days?: number;
      max_wait_days?: number;
      template_id?: string | null;
      template_type?: string | null;
      is_active?: boolean;
    }) => {
      const res = await api(`/api/incasso/pipeline-steps/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Fout bij bijwerken stap");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incasso-pipeline-steps"] });
      queryClient.invalidateQueries({ queryKey: ["incasso-pipeline"] });
    },
  });
}

export function useDeletePipelineStep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/incasso/pipeline-steps/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Fout bij verwijderen stap");
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incasso-pipeline-steps"] });
      queryClient.invalidateQueries({ queryKey: ["incasso-pipeline"] });
    },
  });
}

export function useSeedPipelineSteps() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const res = await api("/api/incasso/pipeline-steps/seed", {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Fout bij aanmaken standaardstappen");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incasso-pipeline-steps"] });
    },
  });
}

// ── Pipeline Overview Hook ───────────────────────────────────────────────

export function useIncassoPipeline() {
  return useQuery<PipelineOverview>({
    queryKey: ["incasso-pipeline"],
    queryFn: async () => {
      const res = await api("/api/incasso/pipeline");
      if (!res.ok) throw new Error("Fout bij ophalen pipeline overzicht");
      return res.json();
    },
  });
}

// ── Smart Work Queue Counts ─────────────────────────────────────────────

export function useIncassoQueueCounts() {
  return useQuery<QueueCounts>({
    queryKey: ["incasso-queue-counts"],
    queryFn: async () => {
      const res = await api("/api/incasso/queues/counts");
      if (!res.ok) return { ready_next_step: 0, wik_expired: 0, action_required: 0 };
      return res.json();
    },
    refetchInterval: 5 * 60 * 1000, // 5-minute auto-refresh
  });
}

// ── Batch Action Hooks ───────────────────────────────────────────────────

export function useBatchPreview() {
  return useMutation<
    BatchPreviewResponse,
    Error,
    { case_ids: string[]; action: string; target_step_id?: string }
  >({
    mutationFn: async (data) => {
      const res = await api("/api/incasso/batch/preview", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Fout bij preview");
      }
      return res.json();
    },
  });
}

export function useBatchExecute() {
  const queryClient = useQueryClient();
  return useMutation<
    BatchActionResult,
    Error,
    {
      case_ids: string[];
      action: string;
      target_step_id?: string | null;
      auto_assign_step?: boolean;
    }
  >({
    mutationFn: async (data) => {
      const res = await api("/api/incasso/batch", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Fout bij batch-actie");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incasso-pipeline"] });
      queryClient.invalidateQueries({ queryKey: ["incasso-queue-counts"] });
      queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
  });
}
