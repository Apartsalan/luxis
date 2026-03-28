"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

export interface ExactConnectionStatus {
  connected: boolean;
  division_name: string | null;
  connected_email: string | null;
  connected_at: string | null;
  last_sync_at: string | null;
  sales_journal_code: string | null;
  bank_journal_code: string | null;
  default_revenue_gl: string | null;
  default_expense_gl: string | null;
}

interface AuthorizeResponse {
  authorize_url: string;
}

interface DisconnectResponse {
  success: boolean;
  message: string;
}

interface SettingsResponse {
  success: boolean;
  message: string;
}

interface SyncResult {
  success: boolean;
  message: string;
  synced_contacts: number;
  synced_invoices: number;
  synced_payments: number;
  errors: string[];
}

export interface ExactJournal {
  code: string;
  description: string;
}

export interface ExactGLAccount {
  id: string;
  code: string;
  description: string;
}

export interface ExactVATCode {
  code: string;
  description: string;
  percentage: number;
}

export interface ExactSetupData {
  journals: ExactJournal[];
  gl_accounts: ExactGLAccount[];
  vat_codes: ExactVATCode[];
}

// ── Hooks ────────────────────────────────────────────────────────────────────

export function useExactOnlineStatus() {
  return useQuery<ExactConnectionStatus>({
    queryKey: ["exact-online-status"],
    queryFn: async () => {
      const res = await api("/api/exact-online/status");
      if (!res.ok) throw new Error("Kon Exact Online status niet ophalen");
      return res.json();
    },
  });
}

export function useExactOnlineAuthorize() {
  return useMutation<AuthorizeResponse, Error>({
    mutationFn: async () => {
      const res = await api("/api/exact-online/authorize");
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Kon autorisatie-URL niet ophalen");
      }
      return res.json();
    },
  });
}

export function useExactOnlineDisconnect() {
  const queryClient = useQueryClient();
  return useMutation<DisconnectResponse, Error>({
    mutationFn: async () => {
      const res = await api("/api/exact-online/disconnect", { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Ontkoppelen mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exact-online-status"] });
    },
  });
}

export function useExactOnlineSetupData() {
  return useQuery<ExactSetupData>({
    queryKey: ["exact-online-setup-data"],
    queryFn: async () => {
      const res = await api("/api/exact-online/setup-data");
      if (!res.ok) throw new Error("Kon setup data niet ophalen");
      return res.json();
    },
    enabled: false, // Only fetch when explicitly triggered
  });
}

export function useExactOnlineUpdateSettings() {
  const queryClient = useQueryClient();
  return useMutation<
    SettingsResponse,
    Error,
    {
      sales_journal_code?: string;
      bank_journal_code?: string;
      default_revenue_gl?: string;
      default_expense_gl?: string;
    }
  >({
    mutationFn: async (settings) => {
      const res = await api("/api/exact-online/settings", {
        method: "PUT",
        body: JSON.stringify(settings),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Opslaan mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exact-online-status"] });
    },
  });
}

export function useExactOnlineSync() {
  const queryClient = useQueryClient();
  return useMutation<SyncResult, Error>({
    mutationFn: async () => {
      const res = await api("/api/exact-online/sync", { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Synchronisatie mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exact-online-status"] });
    },
  });
}
