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
  sommatie: "Sommatie",
  renteoverzicht: "Renteoverzicht",
};

const TEMPLATE_TYPE_DESCRIPTIONS: Record<string, string> = {
  "14_dagenbrief":
    "Aanmaning op grond van art. 6:96 BW met BIK-berekening",
  sommatie:
    "Tweede aanmaning met renteberekening en betalingstermijn",
  renteoverzicht:
    "Gedetailleerd overzicht van rente per vordering en periode",
};

export function getTemplateLabel(type: string): string {
  return TEMPLATE_TYPE_LABELS[type] ?? type;
}

export function getTemplateDescription(type: string): string {
  return TEMPLATE_TYPE_DESCRIPTIONS[type] ?? "";
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
