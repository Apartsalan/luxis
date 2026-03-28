"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface SyncStats {
  synced: number;
  created: number;
  updated: number;
  deleted: number;
}

export function useSyncCalendar() {
  const qc = useQueryClient();
  return useMutation<SyncStats>({
    mutationFn: async () => {
      const res = await api("/api/calendar/events/sync", { method: "POST" });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Synchronisatie mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["calendar-events"] });
    },
  });
}
