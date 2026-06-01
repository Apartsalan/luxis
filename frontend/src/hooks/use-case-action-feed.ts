"use client";

import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Notification } from "@/hooks/use-notifications";

export type FeedFilter = "wachtend" | "afgehandeld" | "alles";

/** Notification types that surface as actionable cards on the case Overzicht-tab. */
const FEED_TYPES = new Set([
  "ai_draft_ready",
  "email_received",
  "classification_done",
  "deadline_overdue",
  "deadline_approaching",
  "verjaring_warning",
]);

/** Types that count as "wachtend op actie" — exclude pure-info notifications. */
const WAITING_TYPES = new Set([
  "ai_draft_ready",
  "classification_done",
  "deadline_overdue",
  "verjaring_warning",
]);

interface UseCaseActionFeedOptions {
  caseId: string;
  filter?: FeedFilter;
  limit?: number;
}

/**
 * Returns the slice of recent notifications scoped to a single case
 * that should appear in the CaseActionFeed widget.
 *
 * Polls every 30s and refetches on window focus — Lisanne typically has the
 * dossier open while reviewing, so window focus catches the bulk of updates.
 */
export function useCaseActionFeed({
  caseId,
  filter = "wachtend",
  limit = 50,
}: UseCaseActionFeedOptions) {
  const query = useQuery<Notification[]>({
    queryKey: ["notifications", "case-action-feed", limit],
    queryFn: async () => {
      const res = await api(`/api/notifications?limit=${limit}`);
      if (!res.ok) return [];
      return res.json();
    },
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
    staleTime: 15_000,
  });

  const items = useMemo(() => {
    const all = query.data ?? [];
    const now = Date.now();
    const isSnoozed = (n: Notification) =>
      n.snoozed_until != null && new Date(n.snoozed_until).getTime() > now;
    const filtered = all.filter(
      (n) => n.case_id === caseId && FEED_TYPES.has(n.type),
    );
    if (filter === "wachtend") {
      // Hide items the user snoozed until their snooze window passes. The 30s
      // poll picks up returning items automatically — no client-side timer needed.
      return filtered.filter(
        (n) => !n.is_read && WAITING_TYPES.has(n.type) && !isSnoozed(n),
      );
    }
    if (filter === "afgehandeld") {
      return filtered.filter((n) => n.is_read);
    }
    return filtered;
  }, [query.data, caseId, filter]);

  return {
    items,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}

/** Mark a single notification as read — used as "dismiss" on the feed cards. */
export function useDismissFeedItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (notificationId: string) => {
      const res = await api(`/api/notifications/${notificationId}/read`, {
        method: "PUT",
      });
      if (!res.ok) throw new Error("Kon melding niet verwijderen");
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

/** Allowed snooze durations (hours), matching the backend whitelist. */
export const SNOOZE_OPTIONS: { label: string; hours: number }[] = [
  { label: "24 uur", hours: 24 },
  { label: "3 dagen", hours: 72 },
  { label: "1 week", hours: 168 },
];

/** Snooze a feed item — hides it from "Wachtend" until the chosen window passes. */
export function useSnoozeFeedItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, hours }: { id: string; hours: number }) => {
      const res = await api(`/api/notifications/${id}/snooze`, {
        method: "PUT",
        body: JSON.stringify({ hours }),
      });
      if (!res.ok) throw new Error("Kon melding niet uitstellen");
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}
