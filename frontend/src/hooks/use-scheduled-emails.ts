"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

/** Een mail die klaarstaat om later verstuurd te worden (S246). */
export interface ScheduledEmail {
  id: string;
  case_id: string | null;
  /** UTC-tijd; tonen in Nederlandse tijd via toLocaleString("nl-NL"). */
  scheduled_at: string;
  status: "pending" | "sending" | "sent" | "cancelled" | "failed";
  subject: string;
  recipients: string;
  attempts: number;
  last_error: string | null;
  sent_at: string | null;
  created_at: string;
}

export const SCHEDULED_STATUS_LABELS: Record<ScheduledEmail["status"], string> = {
  pending: "Staat klaar",
  sending: "Wordt verstuurd",
  sent: "Verstuurd",
  cancelled: "Geannuleerd",
  failed: "Mislukt",
};

/**
 * Geplande mails. Zonder caseId: alles van het kantoor (Mail-pagina); met
 * caseId: alleen dit dossier.
 */
export function useScheduledEmails(caseId?: string, enabled = true) {
  return useQuery({
    queryKey: ["scheduled-emails", caseId ?? "all"],
    queryFn: async (): Promise<ScheduledEmail[]> => {
      const res = await api(
        caseId ? `/api/email/scheduled?case_id=${caseId}` : "/api/email/scheduled"
      );
      if (!res.ok) throw new Error("Geplande e-mails laden mislukt");
      return res.json();
    },
    enabled,
    // Een geplande mail kan elk moment door de bezorger worden opgepakt; een
    // korte verversing houdt de lijst eerlijk zonder de server te belasten.
    refetchInterval: 60_000,
  });
}

export function useCancelScheduledEmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/email/scheduled/${id}`, { method: "DELETE" });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        const detail = err?.detail;
        throw new Error(
          typeof detail === "string" ? detail : "Annuleren mislukt"
        );
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["scheduled-emails"] });
    },
  });
}
