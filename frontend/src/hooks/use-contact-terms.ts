"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { tokenStore } from "@/lib/token-store";

export interface ContactTerms {
  id: string;
  contact_id: string;
  file_name: string;
  label: string | null;
  valid_from: string | null;
  valid_to: string | null;
  created_at: string;
}

export interface ContactTermsCreate {
  file: File;
  label?: string;
  valid_from?: string;
  valid_to?: string;
}

export interface ContactTermsUpdate {
  label?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
}

export function useContactTerms(contactId: string | undefined) {
  return useQuery<ContactTerms[]>({
    queryKey: ["contact-terms", contactId],
    queryFn: async () => {
      const res = await api(`/api/relations/${contactId}/terms`);
      if (!res.ok) throw new Error("Failed to fetch AV-versies");
      return res.json();
    },
    enabled: !!contactId,
  });
}

export function useUploadContactTerms(contactId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ContactTermsCreate) => {
      const token = tokenStore.getAccess();
      const formData = new FormData();
      formData.append("file", data.file);
      if (data.label) formData.append("label", data.label);
      if (data.valid_from) formData.append("valid_from", data.valid_from);
      if (data.valid_to) formData.append("valid_to", data.valid_to);

      const res = await fetch(`/api/relations/${contactId}/terms`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || "Upload mislukt");
      }
      return res.json() as Promise<ContactTerms>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contact-terms", contactId] });
    },
  });
}

export function useUpdateContactTerms(contactId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ termsId, data }: { termsId: string; data: ContactTermsUpdate }) => {
      const res = await api(`/api/relations/${contactId}/terms/${termsId}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || "Bijwerken mislukt");
      }
      return res.json() as Promise<ContactTerms>;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contact-terms", contactId] });
    },
  });
}

export function useDeleteContactTerms(contactId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (termsId: string) => {
      const res = await api(`/api/relations/${contactId}/terms/${termsId}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || "Verwijderen mislukt");
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contact-terms", contactId] });
    },
  });
}

export function downloadContactTermsFile(contactId: string, termsId: string, fileName: string) {
  const token = tokenStore.getAccess();
  return fetch(`/api/relations/${contactId}/terms/${termsId}/file`, {
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
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
}
