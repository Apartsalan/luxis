"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

export interface EmailAttachmentInfo {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
}

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
  attachment_count: number;
  email_date: string;
  case_id: string | null;
}

export interface SyncedEmailDetail extends SyncedEmailSummary {
  cc_emails: string[];
  body_html: string;
  body_text: string;
  attachments: EmailAttachmentInfo[];
  provider_thread_id: string | null;
}

export interface CaseEmailsResponse {
  emails: SyncedEmailSummary[];
  total: number;
}

export interface CaseSuggestion {
  case_id: string;
  case_number: string;
  description: string | null;
  client_name: string;
  match_reason: string;
  confidence: "high" | "medium";
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

  return useMutation<SyncResponse, Error, { maxResults?: number; query?: string; caseId?: string }>({
    mutationFn: async ({ maxResults = 100, query, caseId } = {}) => {
      const params = new URLSearchParams();
      if (maxResults) params.set("max_results", String(maxResults));
      if (query) params.set("query", query);
      if (caseId) params.set("case_id", caseId);

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
      queryClient.invalidateQueries({ queryKey: ["unlinked-count"] });
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
      recipient_name?: string | null;
      cc?: string[] | null;
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

// ── Compose: create draft in Outlook with attachments ──────────────────────

export interface ComposeInlineAttachment {
  filename: string;
  data_base64: string;
  content_type: string;
}

export interface CaseComposeInput {
  recipient_email: string;
  recipient_name?: string | null;
  cc?: string[] | null;
  subject: string;
  body?: string;
  body_html?: string | null;
  case_file_ids?: string[];
  inline_attachments?: ComposeInlineAttachment[];
}

export interface CaseComposeResult {
  success: boolean;
  draft_id?: string | null;
  web_link?: string | null;
  message: string;
}

/**
 * Create a draft email in Outlook from case context.
 * Returns web_link to open in Outlook Web.
 */
export function useCreateCaseDraft(caseId: string) {
  const queryClient = useQueryClient();

  return useMutation<CaseComposeResult, Error, CaseComposeInput>({
    mutationFn: async (data) => {
      const res = await api(`/api/email/compose/cases/${caseId}`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Concept aanmaken mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["case-activities", caseId] });
    },
  });
}

export interface RenderTemplateResult {
  supported: boolean;
  subject?: string | null;
  body_html?: string | null;
}

/**
 * Render an incasso template as HTML for email body preview.
 */
export function useRenderTemplate(caseId: string) {
  return useMutation<RenderTemplateResult, Error, { template_type: string }>({
    mutationFn: async (data) => {
      const res = await api(
        `/api/email/compose/cases/${caseId}/render-template`,
        { method: "POST", body: JSON.stringify(data) },
      );
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Template laden mislukt");
      }
      return res.json();
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
      queryClient.invalidateQueries({ queryKey: ["unlinked-count"] });
    },
  });
}

/**
 * Get count of unlinked non-dismissed emails (for sidebar badge).
 */
export function useUnlinkedCount() {
  return useQuery<{ count: number }>({
    queryKey: ["unlinked-count"],
    queryFn: async () => {
      const res = await api("/api/email/unlinked/count");
      if (!res.ok) return { count: 0 };
      return res.json();
    },
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes (matches auto-sync)
  });
}

/**
 * Bulk link multiple emails to the same case.
 */
export function useBulkLinkEmails() {
  const queryClient = useQueryClient();

  return useMutation<
    { success: boolean; linked_count: number },
    Error,
    { emailIds: string[]; caseId: string }
  >({
    mutationFn: async ({ emailIds, caseId }) => {
      const res = await api("/api/email/bulk-link", {
        method: "POST",
        body: JSON.stringify({ email_ids: emailIds, case_id: caseId }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Bulk koppelen mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["unlinked-emails"] });
      queryClient.invalidateQueries({ queryKey: ["unlinked-count"] });
      queryClient.invalidateQueries({ queryKey: ["case-emails"] });
    },
  });
}

/**
 * Dismiss emails from the ongesorteerd queue.
 */
export function useDismissEmails() {
  const queryClient = useQueryClient();

  return useMutation<
    { success: boolean; dismissed_count: number },
    Error,
    { emailIds: string[] }
  >({
    mutationFn: async ({ emailIds }) => {
      const res = await api("/api/email/dismiss", {
        method: "POST",
        body: JSON.stringify({ email_ids: emailIds }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Negeren mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["unlinked-emails"] });
      queryClient.invalidateQueries({ queryKey: ["unlinked-count"] });
    },
  });
}

/**
 * Suggest cases for an unlinked email based on contact + reference matching.
 */
export function useSuggestCases(emailId: string | undefined) {
  return useQuery<{ suggestions: CaseSuggestion[] }>({
    queryKey: ["suggest-cases", emailId],
    queryFn: async () => {
      const res = await api(`/api/email/suggest-cases/${emailId}`);
      if (!res.ok) return { suggestions: [] };
      return res.json();
    },
    enabled: !!emailId,
  });
}

/**
 * Save an email attachment as a case file (dossierbestand).
 */
export function useSaveAttachmentToCase() {
  const queryClient = useQueryClient();

  return useMutation<
    { success: boolean; case_file_id: string; filename: string },
    Error,
    { attachmentId: string; caseId: string }
  >({
    mutationFn: async ({ attachmentId, caseId }) => {
      const res = await api(`/api/email/attachments/${attachmentId}/save-to-case/${caseId}`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Opslaan in dossier mislukt");
      }
      return res.json();
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["case-files", variables.caseId] });
    },
  });
}
