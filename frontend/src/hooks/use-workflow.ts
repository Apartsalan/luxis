"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

export interface WorkflowStatus {
  id: string;
  slug: string;
  label: string;
  phase: string;
  sort_order: number;
  color: string;
  is_terminal: boolean;
  is_initial: boolean;
  is_active: boolean;
}

export interface WorkflowTransition {
  id: string;
  from_status_id: string;
  to_status_id: string;
  from_status: WorkflowStatus;
  to_status: WorkflowStatus;
  debtor_type: string; // 'b2b' | 'b2c' | 'both'
  requires_note: boolean;
  is_active: boolean;
}

export interface WorkflowTask {
  id: string;
  case_id: string;
  assigned_to_id: string | null;
  task_type: string;
  title: string;
  description: string | null;
  due_date: string;
  completed_at: string | null;
  status: string; // 'pending' | 'due' | 'completed' | 'skipped' | 'overdue'
  auto_execute: boolean;
  action_config: Record<string, unknown> | null;
  created_by_rule_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  // Nested relations (optional, depending on endpoint)
  case?: { id: string; case_number: string; status: string };
  assigned_to?: { id: string; full_name: string } | null;
}

export interface WorkflowRule {
  id: string;
  name: string;
  description: string | null;
  trigger_status_id: string;
  trigger_status: WorkflowStatus;
  debtor_type: string; // 'b2b' | 'b2c' | 'both'
  days_delay: number;
  action_type: string;
  action_config: Record<string, unknown> | null;
  auto_execute: boolean;
  assign_to_case_owner: boolean;
  sort_order: number;
  is_active: boolean;
}

export interface PaginatedTasks {
  items: WorkflowTask[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// ── Phase helpers ────────────────────────────────────────────────────────────

export const PHASE_LABELS: Record<string, string> = {
  minnelijk: "Minnelijk",
  regeling: "Regeling",
  gerechtelijk: "Gerechtelijk",
  executie: "Executie",
  afgerond: "Afgerond",
};

export const PHASE_ORDER = [
  "minnelijk",
  "regeling",
  "gerechtelijk",
  "executie",
  "afgerond",
];

export const PHASE_COLORS: Record<string, string> = {
  minnelijk: "blue",
  regeling: "amber",
  gerechtelijk: "purple",
  executie: "red",
  afgerond: "emerald",
};

export const TASK_TYPE_LABELS: Record<string, string> = {
  generate_document: "Document genereren",
  send_letter: "Brief versturen",
  check_payment: "Betaling controleren",
  escalate_status: "Status escaleren",
  manual_review: "Handmatige beoordeling",
  set_deadline: "Deadline instellen",
  custom: "Eigen taak",
};

export const TASK_STATUS_LABELS: Record<string, string> = {
  pending: "Gepland",
  due: "Openstaand",
  completed: "Afgerond",
  skipped: "Overgeslagen",
  overdue: "Te laat",
};

export const ACTION_TYPE_LABELS: Record<string, string> = {
  generate_document: "Document genereren",
  create_task: "Taak aanmaken",
  change_status: "Status wijzigen",
  send_notification: "Melding versturen",
};

// ── Group statuses by phase ──────────────────────────────────────────────────

export function groupStatusesByPhase(
  statuses: WorkflowStatus[]
): Record<string, WorkflowStatus[]> {
  const groups: Record<string, WorkflowStatus[]> = {};
  for (const phase of PHASE_ORDER) {
    groups[phase] = statuses
      .filter((s) => s.phase === phase && s.is_active)
      .sort((a, b) => a.sort_order - b.sort_order);
  }
  return groups;
}

/** Find which phase a status slug belongs to */
export function getPhaseForStatus(
  statuses: WorkflowStatus[],
  slug: string
): string | null {
  const status = statuses.find((s) => s.slug === slug);
  return status?.phase ?? null;
}

/** Get available transitions for a given status slug and debtor type */
export function getAvailableTransitions(
  transitions: WorkflowTransition[],
  currentStatusSlug: string,
  debtorType: string,
  statuses: WorkflowStatus[]
): WorkflowStatus[] {
  const currentStatus = statuses.find((s) => s.slug === currentStatusSlug);
  if (!currentStatus) return [];

  return transitions
    .filter(
      (t) =>
        t.from_status_id === currentStatus.id &&
        t.is_active &&
        (t.debtor_type === "both" || t.debtor_type === debtorType)
    )
    .map((t) => t.to_status)
    .filter(Boolean);
}

// ── Hooks: Workflow Statuses ─────────────────────────────────────────────────

export function useWorkflowStatuses() {
  return useQuery<WorkflowStatus[]>({
    queryKey: ["workflow-statuses"],
    queryFn: async () => {
      const res = await api("/api/workflow/statuses");
      if (!res.ok) throw new Error("Fout bij ophalen statussen");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateWorkflowStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (
      data: Omit<WorkflowStatus, "id" | "is_active">
    ) => {
      const res = await api("/api/workflow/statuses", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij aanmaken status");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow-statuses"] });
    },
  });
}

export function useUpdateWorkflowStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: Partial<WorkflowStatus>;
    }) => {
      const res = await api(`/api/workflow/statuses/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij bijwerken status");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow-statuses"] });
    },
  });
}

export function useDeleteWorkflowStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/workflow/statuses/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij verwijderen status");
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow-statuses"] });
    },
  });
}

// ── Hooks: Workflow Transitions ──────────────────────────────────────────────

export function useWorkflowTransitions() {
  return useQuery<WorkflowTransition[]>({
    queryKey: ["workflow-transitions"],
    queryFn: async () => {
      const res = await api("/api/workflow/transitions");
      if (!res.ok) throw new Error("Fout bij ophalen transities");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateWorkflowTransition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      from_status_id: string;
      to_status_id: string;
      debtor_type: string;
      requires_note?: boolean;
    }) => {
      const res = await api("/api/workflow/transitions", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij aanmaken transitie");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow-transitions"] });
    },
  });
}

export function useDeleteWorkflowTransition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/workflow/transitions/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij verwijderen transitie");
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow-transitions"] });
    },
  });
}

// ── Hooks: Workflow Tasks ────────────────────────────────────────────────────

export function useWorkflowTasks(params?: {
  case_id?: string;
  status?: string;
  page?: number;
  per_page?: number;
}) {
  const case_id = params?.case_id ?? "";
  const status = params?.status ?? "";
  const page = params?.page ?? 1;
  const per_page = params?.per_page ?? 20;

  return useQuery<PaginatedTasks>({
    queryKey: ["workflow-tasks", { case_id, status, page, per_page }],
    queryFn: async () => {
      const queryParams = new URLSearchParams({
        page: String(page),
        per_page: String(per_page),
      });
      if (case_id) queryParams.set("case_id", case_id);
      if (status) queryParams.set("status", status);

      const res = await api(`/api/workflow/tasks?${queryParams}`);
      if (!res.ok) throw new Error("Fout bij ophalen taken");
      return res.json();
    },
  });
}

/** All open tasks for current user (dashboard widget) */
export function useMyOpenTasks(limit = 10) {
  return useQuery<PaginatedTasks>({
    queryKey: ["workflow-tasks", "my-open", limit],
    queryFn: async () => {
      const res = await api(
        `/api/workflow/tasks?status=due&per_page=${limit}`
      );
      if (!res.ok) throw new Error("Fout bij ophalen taken");
      return res.json();
    },
  });
}

/** All tasks assigned to current user — sorted: overdue → due → pending */
export function useMyTasks() {
  return useQuery<WorkflowTask[]>({
    queryKey: ["workflow-tasks", "my-tasks"],
    queryFn: async () => {
      const res = await api("/api/dashboard/my-tasks");
      if (!res.ok) throw new Error("Fout bij ophalen taken");
      return res.json();
    },
  });
}

export function useCompleteTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (taskId: string) => {
      const res = await api(`/api/workflow/tasks/${taskId}`, {
        method: "PUT",
        body: JSON.stringify({ status: "completed" }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij afronden taak");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useSkipTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (taskId: string) => {
      const res = await api(`/api/workflow/tasks/${taskId}`, {
        method: "PUT",
        body: JSON.stringify({ status: "skipped" }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij overslaan taak");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      case_id: string;
      task_type: string;
      title: string;
      description?: string;
      due_date: string;
      assigned_to_id?: string;
    }) => {
      const res = await api("/api/workflow/tasks", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij aanmaken taak");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

// ── Hooks: Workflow Rules ────────────────────────────────────────────────────

export function useWorkflowRules() {
  return useQuery<WorkflowRule[]>({
    queryKey: ["workflow-rules"],
    queryFn: async () => {
      const res = await api("/api/workflow/rules");
      if (!res.ok) throw new Error("Fout bij ophalen regels");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateWorkflowRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (
      data: Omit<WorkflowRule, "id" | "is_active" | "trigger_status">
    ) => {
      const res = await api("/api/workflow/rules", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij aanmaken regel");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow-rules"] });
    },
  });
}

export function useUpdateWorkflowRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: Partial<WorkflowRule>;
    }) => {
      const res = await api(`/api/workflow/rules/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij bijwerken regel");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow-rules"] });
    },
  });
}

export function useDeleteWorkflowRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/workflow/rules/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij verwijderen regel");
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflow-rules"] });
    },
  });
}
