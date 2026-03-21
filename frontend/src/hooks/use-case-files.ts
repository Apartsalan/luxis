"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { tokenStore } from "@/lib/token-store";
import { toast } from "sonner";

// ── Types ────────────────────────────────────────────────────────────────

export interface CaseFile {
  id: string;
  case_id: string;
  original_filename: string;
  file_size: number;
  content_type: string;
  document_direction: string | null;
  description: string | null;
  uploaded_by: string;
  uploader_name: string | null;
  created_at: string;
}

// ── Hooks ────────────────────────────────────────────────────────────────

export function useCaseFiles(caseId: string) {
  return useQuery<CaseFile[]>({
    queryKey: ["case-files", caseId],
    queryFn: async () => {
      const res = await api(`/api/cases/${caseId}/files`);
      if (!res.ok) throw new Error("Bestanden ophalen mislukt");
      return res.json();
    },
    enabled: !!caseId,
  });
}

export function useUploadCaseFile(caseId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      file,
      description,
      documentDirection,
    }: {
      file: File;
      description?: string;
      documentDirection?: string;
    }) => {
      const formData = new FormData();
      formData.append("file", file);
      if (description) formData.append("description", description);
      if (documentDirection) formData.append("document_direction", documentDirection);

      const token = tokenStore.getAccess();
      const apiUrl = "";
      const res = await fetch(
        `${apiUrl}/api/cases/${caseId}/files`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Upload mislukt" }));
        throw new Error(err.detail || "Upload mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["case-files", caseId] });
    },
  });
}

export function useDeleteCaseFile(caseId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (fileId: string) => {
      const res = await api(`/api/cases/${caseId}/files/${fileId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Verwijderen mislukt");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["case-files", caseId] });
      toast.success("Bestand verwijderd");
    },
  });
}

// ── Email Attachments (LF-17) ────────────────────────────────────────────

export interface CaseEmailAttachment {
  id: string;
  filename: string;
  file_size: number;
  content_type: string;
  email_subject: string | null;
  email_date: string | null;
  email_from: string | null;
  synced_email_id: string;
}

export function useCaseEmailAttachments(caseId: string) {
  return useQuery<CaseEmailAttachment[]>({
    queryKey: ["case-email-attachments", caseId],
    queryFn: async () => {
      const res = await api(`/api/cases/${caseId}/email-attachments`);
      if (!res.ok) throw new Error("Email bijlagen ophalen mislukt");
      return res.json();
    },
    enabled: !!caseId,
  });
}

export function downloadEmailAttachment(attachmentId: string, filename: string) {
  const token = tokenStore.getAccess();
  const apiUrl = "";
  fetch(`${apiUrl}/api/email/attachments/${attachmentId}/download`, {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((res) => {
      if (!res.ok) throw new Error("Download mislukt");
      return res.blob();
    })
    .then((blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    })
    .catch(() => {
      toast.error("Download mislukt");
    });
}

// ── Helpers ──────────────────────────────────────────────────────────────

/** Check whether a content type can be previewed inline (PDF, images, DOCX). */
export function isPreviewable(contentType: string): boolean {
  if (!contentType) return false;
  if (contentType === "application/pdf") return true;
  if (contentType.startsWith("image/")) return true;
  if (
    contentType ===
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document" ||
    contentType === "application/msword"
  )
    return true;
  return false;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function getFileIcon(contentType: string): { color: string; label: string } {
  if (contentType === "application/pdf") return { color: "text-red-600 bg-red-50", label: "PDF" };
  if (contentType.includes("word") || contentType.includes("msword"))
    return { color: "text-blue-600 bg-blue-50", label: "DOC" };
  if (contentType.includes("excel") || contentType.includes("spreadsheet"))
    return { color: "text-green-600 bg-green-50", label: "XLS" };
  if (contentType.startsWith("image/")) return { color: "text-purple-600 bg-purple-50", label: "IMG" };
  return { color: "text-gray-600 bg-gray-50", label: "FILE" };
}

export function downloadCaseFile(caseId: string, fileId: string, filename: string) {
  const token = tokenStore.getAccess();
  const apiUrl = "";
  fetch(`${apiUrl}/api/cases/${caseId}/files/${fileId}/download`, {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((res) => {
      if (!res.ok) throw new Error("Download mislukt");
      return res.blob();
    })
    .then((blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    })
    .catch(() => {
      toast.error("Download mislukt");
    });
}
