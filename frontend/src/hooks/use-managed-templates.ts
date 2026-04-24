"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { tokenStore } from "@/lib/token-store";
import { toast } from "sonner";

// ── Types ────────────────────────────────────────────────────────────────

export interface ManagedTemplate {
  id: string;
  name: string;
  description: string | null;
  template_key: string;
  original_filename: string;
  file_size: number;
  is_builtin: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ── Hooks ────────────────────────────────────────────────────────────────

export function useManagedTemplates() {
  return useQuery<ManagedTemplate[]>({
    queryKey: ["managed-templates"],
    queryFn: async () => {
      const res = await api("/api/documents/managed-templates");
      if (!res.ok) throw new Error("Sjablonen ophalen mislukt");
      return res.json();
    },
  });
}

export function useUploadTemplate() {
  const queryClient = useQueryClient();

  return useMutation<ManagedTemplate, Error, {
    file: File;
    name: string;
    template_key: string;
    description?: string;
  }>({
    mutationFn: async ({ file, name, template_key, description }) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("name", name);
      formData.append("template_key", template_key);
      if (description) formData.append("description", description);

      const token = tokenStore.getAccess();
      const res = await fetch("/api/documents/managed-templates/upload", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Upload mislukt" }));
        throw new Error(err.detail || "Upload mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["managed-templates"] });
      toast.success("Sjabloon geüpload");
    },
  });
}

export function useUpdateTemplate() {
  const queryClient = useQueryClient();

  return useMutation<ManagedTemplate, Error, {
    id: string;
    name?: string;
    description?: string;
    template_key?: string;
  }>({
    mutationFn: async ({ id, ...data }) => {
      const res = await api(`/api/documents/managed-templates/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Bijwerken mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["managed-templates"] });
      toast.success("Sjabloon bijgewerkt");
    },
  });
}

export function useReplaceTemplateFile() {
  const queryClient = useQueryClient();

  return useMutation<ManagedTemplate, Error, {
    id: string;
    file: File;
  }>({
    mutationFn: async ({ id, file }) => {
      const formData = new FormData();
      formData.append("file", file);

      const token = tokenStore.getAccess();
      const res = await fetch(
        `/api/documents/managed-templates/${id}/replace`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        }
      );

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Vervangen mislukt" }));
        throw new Error(err.detail || "Vervangen mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["managed-templates"] });
      toast.success("Sjabloonbestand vervangen");
    },
  });
}

export function useDeleteTemplate() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      const res = await api(`/api/documents/managed-templates/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Verwijderen mislukt");
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["managed-templates"] });
      toast.success("Sjabloon verwijderd");
    },
  });
}

// ── Helpers ──────────────────────────────────────────────────────────────

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export async function downloadTemplate(id: string, filename: string) {
  const token = tokenStore.getAccess();
  const res = await fetch(`/api/documents/managed-templates/${id}/download`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    toast.error("Download mislukt");
    return;
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export const TEMPLATE_KEY_LABELS: Record<string, string> = {
  herinnering: "Herinnering",
  aanmaning: "Aanmaning",
  "14_dagenbrief": "14-dagenbrief",
  veertien_dagen_brief: "14-dagenbrief",
  sommatie: "Sommatie",
  sommatie_drukte: "Sommatie (drukte)",
  tweede_sommatie: "Tweede sommatie",
  wederom_sommatie_kort: "Wederom sommatie (kort)",
  ingebrekestelling: "Ingebrekestelling",
  sommatie_laatste_voor_fai: "Laatste sommatie (faillissement)",
  dagvaarding: "Dagvaarding",
  renteoverzicht: "Renteoverzicht",
  reactie_9_3: "Reactie art. 9.3",
  reactie_20_4: "Reactie art. 20.4",
  schikkingsvoorstel: "Schikkingsvoorstel",
  engelse_sommatie: "English Demand",
  reactie_ncnp_9_3: "Reactie NCNP + 9.3",
  reactie_verlengd_9_3: "Reactie verlengd abo + 9.3",
  vaststellingsovereenkomst: "Vaststellingsovereenkomst",
  faillissement_dreigbrief: "Faillissement (dreiging)",
  bevestiging_sluiting: "Bevestiging sluiting",
};

export function getTemplateKeyLabel(key: string): string {
  return TEMPLATE_KEY_LABELS[key] || key;
}
