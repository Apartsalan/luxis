"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface CalendarEvent {
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

export function useCalendarEvents(dateFrom: string, dateTo: string) {
  return useQuery<CalendarEvent[]>({
    queryKey: ["calendar", dateFrom, dateTo],
    queryFn: async () => {
      const res = await api(
        `/api/workflow/calendar?date_from=${dateFrom}&date_to=${dateTo}`
      );
      if (!res.ok) throw new Error("Fout bij laden agenda");
      return res.json();
    },
    enabled: !!dateFrom && !!dateTo,
  });
}
