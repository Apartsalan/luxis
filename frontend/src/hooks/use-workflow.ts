"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

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
  recurrence: string | null;  // G9: daily, weekly, monthly, quarterly, yearly
  recurrence_end_date: string | null;  // G9
  parent_task_id: string | null;  // G9
  is_active: boolean;
  created_at: string;
  updated_at: string;
  // Nested relations (optional, depending on endpoint)
  case?: { id: string; case_number: string; status: string };
  assigned_to?: { id: string; full_name: string } | null;
}

export const TASK_TYPE_LABELS: Record<string, string> = {
  generate_document: "Document genereren",
  send_letter: "Brief versturen",
  check_payment: "Betaling controleren",
  escalate_status: "Status escaleren",
  manual_review: "Handmatige beoordeling",
  set_deadline: "Deadline instellen",
  review_ai_draft: "Concept-mail reviewen",
  custom: "Eigen taak",
};

export const RECURRENCE_LABELS: Record<string, string> = {
  none: "Eenmalig",
  daily: "Dagelijks",
  weekly: "Wekelijks",
  monthly: "Maandelijks",
  quarterly: "Per kwartaal",
  yearly: "Jaarlijks",
};

export const TASK_STATUS_LABELS: Record<string, string> = {
  pending: "Gepland",
  due: "Openstaand",
  completed: "Afgerond",
  skipped: "Overgeslagen",
  overdue: "Te laat",
};

// ── Hooks: Workflow Tasks ────────────────────────────────────────────────────

export function useWorkflowTasks(params?: {
  case_id?: string;
  status?: string;
}) {
  const case_id = params?.case_id ?? "";
  const status = params?.status ?? "";

  return useQuery<WorkflowTask[]>({
    queryKey: ["workflow-tasks", { case_id, status }],
    queryFn: async () => {
      const queryParams = new URLSearchParams();
      if (case_id) queryParams.set("case_id", case_id);
      if (status) queryParams.set("status", status);

      const qs = queryParams.toString();
      const res = await api(`/api/workflow/tasks${qs ? `?${qs}` : ""}`);
      if (!res.ok) throw new Error("Fout bij ophalen taken");
      return res.json();
    },
  });
}
/** All open tasks for current user (dashboard widget) */
export function useMyOpenTasks(limit = 10) {
  return useQuery<WorkflowTask[]>({
    queryKey: ["workflow-tasks", "my-open", limit],
    queryFn: async () => {
      const res = await api("/api/dashboard/my-tasks");
      if (!res.ok) throw new Error("Fout bij ophalen taken");
      const tasks: WorkflowTask[] = await res.json();
      return tasks.slice(0, limit);
    },
  });
}

/** All tasks assigned to current user — sorted: overdue → due → pending.
 *  Bevat ook afgeronde + overgeslagen taken (nieuwste eerst) zodat de
 *  Takenpagina die filters kan tonen en herstellen (S221 3.4). */
export function useMyTasks() {
  return useQuery<WorkflowTask[]>({
    queryKey: ["workflow-tasks", "my-tasks"],
    queryFn: async () => {
      const res = await api("/api/dashboard/my-tasks?include_done=true");
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

/** Zet een overgeslagen/afgeronde taak terug op de werklijst (→ pending;
 *  effectieve status wordt uit de deadline afgeleid). S221 3.4. */
export function useRestoreTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (taskId: string) => {
      const res = await api(`/api/workflow/tasks/${taskId}`, {
        method: "PUT",
        body: JSON.stringify({ status: "pending" }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij terugzetten taak");
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
      recurrence?: string;  // G9
      recurrence_end_date?: string;  // G9
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
