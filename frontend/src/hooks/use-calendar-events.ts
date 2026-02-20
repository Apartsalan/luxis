"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────

export interface UserCalendarEvent {
  id: string;
  title: string;
  description: string | null;
  event_type: string;
  start_time: string;
  end_time: string;
  all_day: boolean;
  location: string | null;
  case_id: string | null;
  contact_id: string | null;
  color: string | null;
  reminder_minutes: number | null;
  created_by: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  case: { id: string; case_number: string } | null;
  contact: { id: string; name: string } | null;
  creator: { id: string; full_name: string } | null;
}

export interface CalendarEventCreateInput {
  title: string;
  description?: string;
  event_type: string;
  start_time: string;
  end_time: string;
  all_day?: boolean;
  location?: string;
  case_id?: string;
  contact_id?: string;
  color?: string;
  reminder_minutes?: number | null;
}

export interface CalendarEventUpdateInput {
  title?: string;
  description?: string | null;
  event_type?: string;
  start_time?: string;
  end_time?: string;
  all_day?: boolean;
  location?: string | null;
  case_id?: string | null;
  contact_id?: string | null;
  color?: string | null;
  reminder_minutes?: number | null;
}

// ── Event type config ────────────────────────────────────────────────────

export const EVENT_TYPES = [
  { value: "appointment", label: "Afspraak", color: "#3b82f6" },
  { value: "hearing", label: "Zitting", color: "#ef4444" },
  { value: "deadline", label: "Deadline", color: "#f97316" },
  { value: "reminder", label: "Herinnering", color: "#eab308" },
  { value: "meeting", label: "Vergadering", color: "#8b5cf6" },
  { value: "call", label: "Telefoongesprek", color: "#22c55e" },
  { value: "other", label: "Overig", color: "#6b7280" },
] as const;

export const EVENT_TYPE_LABELS: Record<string, string> = Object.fromEntries(
  EVENT_TYPES.map((t) => [t.value, t.label])
);

export const EVENT_TYPE_COLORS: Record<string, string> = Object.fromEntries(
  EVENT_TYPES.map((t) => [t.value, t.color])
);

// ── Hooks ────────────────────────────────────────────────────────────────

export function useUserCalendarEvents(dateFrom: string, dateTo: string) {
  return useQuery<UserCalendarEvent[]>({
    queryKey: ["calendar-events", dateFrom, dateTo],
    queryFn: async () => {
      const res = await api(
        `/api/calendar/events?date_from=${dateFrom}T00:00:00&date_to=${dateTo}T23:59:59`
      );
      if (!res.ok) throw new Error("Kan agenda-events niet laden");
      return res.json();
    },
    enabled: !!dateFrom && !!dateTo,
  });
}

export function useCreateCalendarEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: CalendarEventCreateInput) => {
      const res = await api("/api/calendar/events", {
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
      qc.invalidateQueries({ queryKey: ["calendar-events"] });
    },
  });
}

export function useUpdateCalendarEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: CalendarEventUpdateInput;
    }) => {
      const res = await api(`/api/calendar/events/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Bijwerken mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["calendar-events"] });
    },
  });
}

export function useDeleteCalendarEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/calendar/events/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Verwijderen mislukt");
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["calendar-events"] });
    },
  });
}
