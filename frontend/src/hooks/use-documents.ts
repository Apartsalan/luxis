"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

export interface DocxTemplateInfo {
  template_type: string;
  filename: string;
  available: boolean;
}

export interface DocumentTemplateSummary {
  id: string;
  name: string;
  template_type: string;
  is_active: boolean;
}

export interface GeneratedDocumentSummary {
  id: string;
  case_id: string;
  title: string;
  document_type: string;
  file_path: string | null;
  created_at: string;
}

export interface GeneratedDocumentDetail {
  id: string;
  case_id: string;
  template_id: string | null;
  title: string;
  document_type: string;
  content_html: string | null;
  file_path: string | null;
  generated_by: { id: string; full_name: string } | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ── Docx Templates ──────────────────────────────────────────────────────────

const TEMPLATE_TYPE_LABELS: Record<string, string> = {
  "14_dagenbrief": "14-dagenbrief",
  herinnering: "Herinnering",
  aanmaning: "Aanmaning",
  sommatie: "Sommatie",
  tweede_sommatie: "Tweede sommatie",
  dagvaarding: "Dagvaarding",
  renteoverzicht: "Renteoverzicht",
};

const TEMPLATE_TYPE_DESCRIPTIONS: Record<string, string> = {
  "14_dagenbrief":
    "Verplichte aanmaning voor B2C op grond van art. 6:96 BW met BIK-berekening",
  herinnering:
    "Eerste herinnering aan openstaande factuur — vriendelijke toon",
  aanmaning:
    "Formele aanmaning met betalingstermijn en renteberekening",
  sommatie:
    "Tweede aanmaning met renteberekening en BIK-specificatie",
  tweede_sommatie:
    "Laatste sommatie voor dagvaarding met laatste termijn",
  dagvaarding:
    "Concept dagvaarding — moet worden afgerond door advocaat",
  renteoverzicht:
    "Gedetailleerd overzicht van rente per vordering en periode",
};

export function getTemplateLabel(type: string): string {
  return TEMPLATE_TYPE_LABELS[type] ?? type;
}

export function getTemplateDescription(type: string): string {
  return TEMPLATE_TYPE_DESCRIPTIONS[type] ?? "";
}

// ── Status → Template Mapping (T1) ─────────────────────────────────────────

interface TemplateSet {
  recommended: string[];
  available: string[];
}

const STATUS_TEMPLATE_MAP: Record<string, TemplateSet> = {
  nieuw:            { recommended: ["herinnering"],                  available: ["herinnering", "renteoverzicht"] },
  herinnering:      { recommended: ["aanmaning"],                   available: ["aanmaning", "renteoverzicht"] },
  aanmaning:        { recommended: ["14_dagenbrief", "sommatie"],   available: ["14_dagenbrief", "sommatie", "renteoverzicht"] },
  "14_dagenbrief":  { recommended: ["sommatie", "tweede_sommatie"], available: ["sommatie", "tweede_sommatie", "renteoverzicht"] },
  sommatie:         { recommended: ["tweede_sommatie"],             available: ["tweede_sommatie", "dagvaarding", "renteoverzicht"] },
  tweede_sommatie:  { recommended: ["dagvaarding"],                 available: ["dagvaarding", "renteoverzicht"] },
  dagvaarding:      { recommended: ["renteoverzicht"],              available: ["renteoverzicht"] },
  vonnis:           { recommended: ["renteoverzicht"],              available: ["renteoverzicht"] },
  executie:         { recommended: ["renteoverzicht"],              available: ["renteoverzicht"] },
};

/**
 * Get recommended and available templates for a given case status + debtor type.
 * B2C: 14_dagenbrief is relevant, sommatie comes after.
 * B2B: sommatie is first, 14_dagenbrief is filtered out.
 */
export function getTemplatesForStatus(
  status: string,
  debtorType?: string | null
): { recommended: string[]; available: string[] } {
  const mapping = STATUS_TEMPLATE_MAP[status];
  if (!mapping) {
    // Fallback: all templates available, none recommended
    return { recommended: [], available: Object.keys(TEMPLATE_TYPE_LABELS) };
  }

  const filterByDebtor = (types: string[]) => {
    if (debtorType === "b2b") {
      // B2B: verwijder 14_dagenbrief
      return types.filter((t) => t !== "14_dagenbrief");
    }
    if (debtorType === "b2c") {
      // B2C: bij aanmaning-status, 14_dagenbrief als eerste aanbevolen
      return types;
    }
    return types;
  };

  return {
    recommended: filterByDebtor(mapping.recommended),
    available: filterByDebtor(mapping.available),
  };
}

// ── Hooks: Docx Templates ───────────────────────────────────────────────────

export function useDocxTemplates() {
  return useQuery<DocxTemplateInfo[]>({
    queryKey: ["docx-templates"],
    queryFn: async () => {
      const res = await api("/api/documents/docx/templates");
      if (!res.ok) throw new Error("Fout bij ophalen templates");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}

// ── Hooks: Generate Docx ────────────────────────────────────────────────────

export function useGenerateDocx(caseId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (templateType: string) => {
      const res = await api(`/api/documents/docx/cases/${caseId}/generate`, {
        method: "POST",
        body: JSON.stringify({ template_type: templateType }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij genereren document");
      }
      // Returns binary docx content
      return {
        blob: await res.blob(),
        filename:
          res.headers
            .get("content-disposition")
            ?.match(/filename="(.+)"/)?.[1] ?? `${templateType}.docx`,
      };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["case-documents", caseId] });
    },
  });
}

// ── Hooks: Case Documents (generated) ───────────────────────────────────────

export function useCaseDocuments(caseId: string) {
  return useQuery<GeneratedDocumentSummary[]>({
    queryKey: ["case-documents", caseId],
    queryFn: async () => {
      const res = await api(`/api/documents/cases/${caseId}`);
      if (!res.ok) throw new Error("Fout bij ophalen documenten");
      return res.json();
    },
    enabled: !!caseId,
  });
}

export function useDocument(documentId: string) {
  return useQuery<GeneratedDocumentDetail>({
    queryKey: ["document", documentId],
    queryFn: async () => {
      const res = await api(`/api/documents/${documentId}`);
      if (!res.ok) throw new Error("Document niet gevonden");
      return res.json();
    },
    enabled: !!documentId,
  });
}

export function useDeleteDocument(caseId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId: string) => {
      const res = await api(`/api/documents/${documentId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Fout bij verwijderen document");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["case-documents", caseId] });
    },
  });
}

// ── Hooks: HTML Document Templates ──────────────────────────────────────────

export function useDocumentTemplates(templateType?: string) {
  return useQuery<DocumentTemplateSummary[]>({
    queryKey: ["document-templates", templateType],
    queryFn: async () => {
      const params = templateType ? `?template_type=${templateType}` : "";
      const res = await api(`/api/documents/templates${params}`);
      if (!res.ok) throw new Error("Fout bij ophalen sjablonen");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}

// ── Types: Send Document ────────────────────────────────────────────────────

export interface SendDocumentInput {
  recipient_email: string;
  recipient_name?: string;
  cc?: string[];
  custom_subject?: string;
  custom_body?: string;
}

export interface SendDocumentResponse {
  email_log_id: string;
  recipient: string;
  subject: string;
  status: string;
}

// ── Hook: Send Document via Email ──────────────────────────────────────────

export function useSendDocument(caseId: string) {
  const queryClient = useQueryClient();

  return useMutation<SendDocumentResponse, Error, { documentId: string; data: SendDocumentInput }>({
    mutationFn: async ({ documentId, data }) => {
      const res = await api(`/api/documents/${documentId}/send`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij verzenden e-mail");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["case-documents", caseId] });
      queryClient.invalidateQueries({ queryKey: ["email-logs", caseId] });
    },
  });
}

// ── Types: Email Logs ──────────────────────────────────────────────────────

export interface EmailLogEntry {
  id: string;
  recipient: string;
  subject: string;
  status: string;
  sent_at: string;
  document_id: string | null;
  template: string | null;
}

// ── Hook: Email Logs per Case ─────────────────────────────────────────────

export function useEmailLogs(caseId: string | undefined) {
  return useQuery<EmailLogEntry[]>({
    queryKey: ["email-logs", caseId ?? ""],
    queryFn: async () => {
      const res = await api(`/api/documents/cases/${caseId}/email-logs`);
      if (!res.ok) throw new Error("Kan e-maillogboek niet laden");
      return res.json();
    },
    enabled: !!caseId,
  });
}

// ── Hook: Test Email ──────────────────────────────────────────────────────

export function useTestEmail() {
  return useMutation<{ message: string }, Error, { email: string }>({
    mutationFn: async ({ email }) => {
      const res = await api("/api/email/test", {
        method: "POST",
        body: JSON.stringify({ recipient_email: email }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Test e-mail verzenden mislukt");
      }
      return res.json();
    },
  });
}

// ── Helper: trigger download ────────────────────────────────────────────────

export function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
