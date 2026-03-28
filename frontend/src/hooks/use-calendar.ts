"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  useUserCalendarEvents,
  type UserCalendarEvent,
} from "./use-calendar-events";

// ── Unified CalendarEvent type ──────────────────────────────────────────

export interface CalendarEvent {
  id: string;
  title: string;
  date: string; // YYYY-MM-DD
  event_type: string;
  status: string;
  case_id: string | null;
  case_number: string | null;
  contact_id: string | null;
  contact_name: string | null;
  assigned_to_name: string | null;
  task_type: string | null;
  color: string;
  // User event extras
  source: "workflow" | "user" | "outlook";
  start_time: string | null;
  end_time: string | null;
  all_day: boolean;
  location: string | null;
  description: string | null;
  user_event_id: string | null; // original id for CRUD
}

// ── Workflow events (internal) ──────────────────────────────────────────

interface WorkflowCalendarEvent {
  id: string;
  title: string;
  date: string;
  event_type: "task" | "kyc_review";
  status: string;
  case_id: string | null;
  case_number: string | null;
  contact_id: string | null;
  contact_name: string | null;
  assigned_to_name: string | null;
  task_type: string | null;
  color: string;
}

function useWorkflowCalendarEvents(dateFrom: string, dateTo: string) {
  return useQuery<WorkflowCalendarEvent[]>({
    queryKey: ["calendar-workflow", dateFrom, dateTo],
    queryFn: async () => {
      const res = await api(
        `/api/workflow/calendar?date_from=${dateFrom}&date_to=${dateTo}`
      );
      if (!res.ok) throw new Error("Fout bij laden workflow agenda");
      return res.json();
    },
    enabled: !!dateFrom && !!dateTo,
  });
}

// ── Converters ──────────────────────────────────────────────────────────

function convertWorkflowEvent(e: WorkflowCalendarEvent): CalendarEvent {
  return {
    ...e,
    source: "workflow",
    start_time: null,
    end_time: null,
    all_day: false,
    location: null,
    description: null,
    user_event_id: null,
  };
}

function convertUserEvent(e: UserCalendarEvent): CalendarEvent {
  const dateStr = e.start_time.slice(0, 10);
  return {
    id: `user-${e.id}`,
    title: e.title,
    date: dateStr,
    event_type: e.event_type,
    status: "scheduled",
    case_id: e.case?.id ?? null,
    case_number: e.case?.case_number ?? null,
    contact_id: e.contact?.id ?? null,
    contact_name: e.contact?.name ?? null,
    assigned_to_name: e.creator?.full_name ?? null,
    task_type: null,
    color: e.color || "#3b82f6",
    source: e.provider === "outlook" ? "outlook" : "user",
    start_time: e.start_time,
    end_time: e.end_time,
    all_day: e.all_day,
    location: e.location,
    description: e.description,
    user_event_id: e.id,
  };
}

// ── Unified hook ────────────────────────────────────────────────────────

export function useCalendarEvents(dateFrom: string, dateTo: string) {
  const workflow = useWorkflowCalendarEvents(dateFrom, dateTo);
  const user = useUserCalendarEvents(dateFrom, dateTo);

  const events: CalendarEvent[] = [
    ...(workflow.data ?? []).map(convertWorkflowEvent),
    ...(user.data ?? []).map(convertUserEvent),
  ];

  return {
    data: events,
    isLoading: workflow.isLoading || user.isLoading,
    isError: workflow.isError || user.isError,
    error: workflow.error || user.error,
    refetch: () => {
      workflow.refetch();
      user.refetch();
    },
  };
}
