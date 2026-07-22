"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ─── Types ────────────────────────────────────────────────────────
export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  case_id?: string;
  case_number?: string;
  task_id?: string;
  is_read: boolean;
  /** FEAT-AI-05: ISO timestamp until which this item is hidden from "Wachtend". null = not snoozed. */
  snoozed_until?: string | null;
  created_at: string;
}

export type NotificationType =
  | "deadline_approaching"
  | "deadline_overdue"
  | "task_assigned"
  | "task_completed"
  | "status_changed"
  | "document_generated"
  | "email_sent"
  | "email_failed"
  | "verjaring_warning"
  | "email_received"
  | "ai_draft_ready"
  | "classification_done"
  | "invoice_overdue"
  | "trust_approval_pending"
  | "trust_stale"
  | "installment_overdue"
  | "case_closed_invoice"
  | "system";

export const NOTIFICATION_TYPE_CONFIG: Record<
  NotificationType,
  { label: string; icon: string; color: string }
> = {
  deadline_approaching: { label: "Deadline nadert", icon: "clock", color: "amber" },
  deadline_overdue: { label: "Deadline verlopen", icon: "alert-triangle", color: "red" },
  task_assigned: { label: "Taak toegewezen", icon: "user-plus", color: "blue" },
  task_completed: { label: "Taak voltooid", icon: "check-circle", color: "emerald" },
  status_changed: { label: "Status gewijzigd", icon: "arrow-right", color: "indigo" },
  document_generated: { label: "Document aangemaakt", icon: "file-text", color: "blue" },
  email_sent: { label: "E-mail verzonden", icon: "mail", color: "emerald" },
  email_failed: { label: "E-mail mislukt", icon: "mail-x", color: "red" },
  verjaring_warning: { label: "Verjaring nadert", icon: "alert-circle", color: "red" },
  email_received: { label: "Nieuwe email", icon: "mail", color: "blue" },
  ai_draft_ready: { label: "AI-concept klaar", icon: "sparkles", color: "violet" },
  classification_done: { label: "Antwoord geclassificeerd", icon: "tag", color: "amber" },
  invoice_overdue: { label: "Factuur te laat", icon: "alert-triangle", color: "red" },
  trust_approval_pending: { label: "Goedkeuring nodig", icon: "alert-circle", color: "amber" },
  trust_stale: { label: "Derdengelden stil", icon: "alert-triangle", color: "amber" },
  installment_overdue: { label: "Termijn gemist", icon: "alert-triangle", color: "red" },
  case_closed_invoice: { label: "Dossier afgesloten", icon: "check-circle", color: "emerald" },
  system: { label: "Systeem", icon: "info", color: "gray" },
};

// ─── Queries ──────────────────────────────────────────────────────
export function useNotifications(limit = 20) {
  return useQuery<Notification[]>({
    queryKey: ["notifications", limit],
    queryFn: async () => {
      const res = await api(`/api/notifications?limit=${limit}`);
      if (!res.ok) return [];
      return res.json();
    },
    refetchInterval: 30_000, // Poll every 30 seconds for new notifications
  });
}

export function useUnreadCount() {
  return useQuery<number>({
    queryKey: ["notifications", "unread-count"],
    queryFn: async () => {
      const res = await api("/api/notifications/unread-count");
      if (!res.ok) return 0;
      const data = await res.json();
      return data.count ?? 0;
    },
    refetchInterval: 30_000,
  });
}

// ─── Mutations ────────────────────────────────────────────────────
export function useMarkAsRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (notificationId: string) => {
      const res = await api(`/api/notifications/${notificationId}/read`, {
        method: "PUT",
      });
      if (!res.ok) throw new Error("Kon melding niet als gelezen markeren");
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useMarkAllAsRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const res = await api("/api/notifications/read-all", {
        method: "PUT",
      });
      if (!res.ok) throw new Error("Kon meldingen niet als gelezen markeren");
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

// ─── Helpers ──────────────────────────────────────────────────────
export function formatNotificationTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffMin < 1) return "Zojuist";
  if (diffMin < 60) return `${diffMin} min geleden`;
  if (diffHours < 24) return `${diffHours} uur geleden`;
  if (diffDays < 7) return `${diffDays} ${diffDays === 1 ? "dag" : "dagen"} geleden`;

  return date.toLocaleDateString("nl-NL", {
    day: "numeric",
    month: "short",
  });
}
