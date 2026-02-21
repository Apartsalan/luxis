"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

export interface EmailAccountStatus {
  connected: boolean;
  provider: string | null;
  email_address: string | null;
  connected_at: string | null;
}

interface AuthorizeResponse {
  authorize_url: string;
}

interface DisconnectResponse {
  success: boolean;
  message: string;
}

// ── Hooks ────────────────────────────────────────────────────────────────────

/**
 * Get the current user's email OAuth connection status.
 */
export function useEmailOAuthStatus() {
  return useQuery<EmailAccountStatus>({
    queryKey: ["email-oauth-status"],
    queryFn: async () => {
      const res = await api("/api/email/oauth/status");
      if (!res.ok) {
        throw new Error("Kon e-mail status niet ophalen");
      }
      return res.json();
    },
  });
}

/**
 * Get the OAuth authorize URL to start the connection flow.
 */
export function useEmailOAuthAuthorize() {
  return useMutation<AuthorizeResponse, Error, { provider?: string }>({
    mutationFn: async ({ provider = "gmail" }) => {
      const res = await api(`/api/email/oauth/authorize?provider=${provider}`);
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Kon autorisatie-URL niet ophalen");
      }
      return res.json();
    },
  });
}

/**
 * Disconnect the current user's email account.
 */
export function useEmailOAuthDisconnect() {
  const queryClient = useQueryClient();

  return useMutation<DisconnectResponse, Error>({
    mutationFn: async () => {
      const res = await api("/api/email/oauth/disconnect", {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Ontkoppelen mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["email-oauth-status"] });
    },
  });
}
