"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface KycVerification {
  id: string;
  contact_id: string;
  status: "niet_gestart" | "in_behandeling" | "voltooid" | "verlopen";
  risk_level: "laag" | "midden" | "hoog" | null;
  risk_notes: string | null;

  // ID document
  id_type: string | null;
  id_number: string | null;
  id_expiry_date: string | null;
  id_verified_at: string | null;

  // UBO
  ubo_name: string | null;
  ubo_dob: string | null;
  ubo_nationality: string | null;
  ubo_percentage: string | null;
  ubo_verified_at: string | null;

  // PEP
  pep_checked: boolean;
  pep_is_pep: boolean;
  pep_notes: string | null;

  // Sanctions
  sanctions_checked: boolean;
  sanctions_hit: boolean;
  sanctions_notes: string | null;

  // Source of funds
  source_of_funds: string | null;
  source_of_funds_verified: boolean;

  // Meta
  verified_by: { id: string; full_name: string } | null;
  verification_date: string | null;
  next_review_date: string | null;
  notes: string | null;

  created_at: string;
  updated_at: string;
}

export interface KycStatus {
  has_kyc: boolean;
  status: string;
  is_compliant: boolean;
  risk_level: string | null;
  next_review_date: string | null;
  is_overdue: boolean;
}

export interface KycDashboard {
  without_kyc: { contact_id: string; contact_name: string; contact_type: string; kyc_status: string }[];
  without_kyc_count: number;
  incomplete: { contact_id: string; contact_name: string; contact_type: string; kyc_status: string }[];
  incomplete_count: number;
  overdue: { contact_id: string; contact_name: string; contact_type: string; kyc_status: string; next_review_date: string; days_overdue: number }[];
  overdue_count: number;
  upcoming_reviews: { contact_id: string; contact_name: string; contact_type: string; kyc_status: string; next_review_date: string; days_until_review: number }[];
  upcoming_reviews_count: number;
  total_issues: number;
}

// Get full KYC record for a contact
export function useKyc(contactId: string | undefined) {
  return useQuery<KycVerification | null>({
    queryKey: ["kyc", contactId],
    queryFn: async () => {
      const res = await api(`/api/kyc/contact/${contactId}`);
      if (!res.ok) throw new Error("Failed to fetch KYC");
      return res.json();
    },
    enabled: !!contactId,
  });
}

// Get lightweight KYC status (for badges)
export function useKycStatus(contactId: string | undefined) {
  return useQuery<KycStatus>({
    queryKey: ["kyc-status", contactId],
    queryFn: async () => {
      const res = await api(`/api/kyc/contact/${contactId}/status`);
      if (!res.ok) throw new Error("Failed to fetch KYC status");
      return res.json();
    },
    enabled: !!contactId,
  });
}

// Get KYC dashboard data
export function useKycDashboard() {
  return useQuery<KycDashboard>({
    queryKey: ["kyc-dashboard"],
    queryFn: async () => {
      const res = await api("/api/kyc/dashboard");
      if (!res.ok) throw new Error("Failed to fetch KYC dashboard");
      return res.json();
    },
  });
}

// Create or update KYC
export function useSaveKyc() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Record<string, any>) => {
      const res = await api("/api/kyc", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to save KYC");
      }
      return res.json();
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["kyc", result.contact_id] });
      queryClient.invalidateQueries({ queryKey: ["kyc-status", result.contact_id] });
      queryClient.invalidateQueries({ queryKey: ["kyc-dashboard"] });
    },
  });
}

// Update specific KYC fields
export function useUpdateKyc() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Record<string, any> }) => {
      const res = await api(`/api/kyc/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to update KYC");
      }
      return res.json();
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["kyc", result.contact_id] });
      queryClient.invalidateQueries({ queryKey: ["kyc-status", result.contact_id] });
      queryClient.invalidateQueries({ queryKey: ["kyc-dashboard"] });
    },
  });
}

// Complete KYC verification
export function useCompleteKyc() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, notes }: { id: string; notes?: string }) => {
      const res = await api(`/api/kyc/${id}/complete`, {
        method: "POST",
        body: JSON.stringify({ notes }),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to complete KYC");
      }
      return res.json();
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["kyc", result.contact_id] });
      queryClient.invalidateQueries({ queryKey: ["kyc-status", result.contact_id] });
      queryClient.invalidateQueries({ queryKey: ["kyc-dashboard"] });
    },
  });
}
