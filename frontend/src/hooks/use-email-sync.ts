"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

export interface SyncedEmailSummary {
  id: string;
  subject: string;
  from_email: string;
  from_name: string;
  to_emails: string[];
  snippet: string;
  direction: "inbound" | "outbound";
  is_read: boolean;
  has_attachments: boolean;
  email_date: string;
  case_id: string | null;
}

export interface SyncedEmailDetail extends SyncedEmailSummary {
  cc_emails: string[];
  body_html: string;
  body_text: string;
  provider_thread_id: string | null;
}

interface CaseEmailsResponse {
  emails: SyncedEmailSummary[];
  total: number;
}

interface SyncResponse {
  fetched: number;
  new: number;
  linked: number;
  skipped: number;
}

// ── Hooks ────────────────────────────────────────────────────────────────────

/**
 * Trigger inbox sync for the current user's email account.
 */
export function useSyncEmails() {
  const queryClient = useQueryClient();

  return useMutation<SyncResponse, Error, { maxResults?: number; query?: string }>({
    mutationFn: async ({ maxResults = 100, query } = {}) => {
      const params = new URLSearchParams();
      if (maxResults) params.set("max_results", String(maxResults));
      if (query) params.set("query", query);

      const res = await api(`/api/email/sync?${params.toString()}`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Sync mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      // Invalidate all email-related queries after sync
      queryClient.invalidateQueries({ queryKey: ["case-emails"] });
      queryClient.invalidateQueries({ queryKey: ["unlinked-emails"] });
    },
  });
}

/**
 * Get synced emails for a specific case/dossier.
 */
export function useCaseEmails(caseId: string | undefined, limit = 50) {
  return useQuery<CaseEmailsResponse>({
    queryKey: ["case-emails", caseId, limit],
    queryFn: async () => {
      const res = await api(`/api/email/cases/${caseId}/emails?limit=${limit}`);
      if (!res.ok) {
        throw new Error("Kon e-mails niet ophalen");
      }
      return res.json();
    },
    enabled: !!caseId,
  });
}

/**
 * Get unlinked emails (not assigned to any case).
 */
export function useUnlinkedEmails(limit = 50) {
  return useQuery<CaseEmailsResponse>({
    queryKey: ["unlinked-emails", limit],
    queryFn: async () => {
      const res = await api(`/api/email/unlinked?limit=${limit}`);
      if (!res.ok) {
        throw new Error("Kon ongesorteerde e-mails niet ophalen");
      }
      return res.json();
    },
  });
}

/**
 * Get a single synced email with full body.
 */
export function useSyncedEmailDetail(emailId: string | undefined) {
  return useQuery<SyncedEmailDetail>({
    queryKey: ["synced-email", emailId],
    queryFn: async () => {
      const res = await api(`/api/email/messages/${emailId}`);
      if (!res.ok) {
        throw new Error("Kon e-mail niet ophalen");
      }
      return res.json();
    },
    enabled: !!emailId,
  });
}

/**
 * Send email via connected provider from a case context.
 * Falls back to SMTP if no provider connected.
 */
export function useSendViaProvider(caseId: string) {
  const queryClient = useQueryClient();

  return useMutation<
    { success: boolean; provider_message_id?: string; message: string },
    Error,
    {
      recipient_email: string;
      recipient_name?: string;
      cc?: string[];
      subject: string;
      body: string;
    }
  >({
    mutationFn: async (data) => {
      const res = await api(`/api/email/compose/cases/${caseId}`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "E-mail verzenden mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["case-emails", caseId] });
      queryClient.invalidateQueries({ queryKey: ["email-logs", caseId] });
      queryClient.invalidateQueries({ queryKey: ["case-activities", caseId] });
    },
  });
}

/**
 * Create a draft in the connected email provider.
 */
export function useCreateDraft() {
  return useMutation<
    { success: boolean; draft_id?: string; message: string },
    Error,
    { to: string[]; cc?: string[]; subject: string; body_html: string }
  >({
    mutationFn: async (data) => {
      const res = await api("/api/email/compose/draft", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Concept aanmaken mislukt");
      }
      return res.json();
    },
  });
}

/**
 * Manually link an email to a case.
 */
export function useLinkEmail() {
  const queryClient = useQueryClient();

  return useMutation<
    { success: boolean; email_id: string; case_id: string },
    Error,
    { emailId: string; caseId: string }
  >({
    mutationFn: async ({ emailId, caseId }) => {
      const res = await api("/api/email/link", {
        method: "POST",
        body: JSON.stringify({ email_id: emailId, case_id: caseId }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Koppelen mislukt");
      }
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["case-emails", data.case_id] });
      queryClient.invalidateQueries({ queryKey: ["unlinked-emails"] });
    },
  });
}
