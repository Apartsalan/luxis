"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

export interface TenantDetail {
  id: string;
  name: string;
  slug: string;
  kvk_number: string | null;
  btw_number: string | null;
  address: string | null;
  postal_code: string | null;
  city: string | null;
  iban: string | null;
  phone: string | null;
  email: string | null;
  modules_enabled: string[];
}

export interface UpdateProfileData {
  full_name?: string;
  default_hourly_rate?: string | number | null;
}

export interface ChangePasswordData {
  current_password: string;
  new_password: string;
}

export interface UpdateTenantData {
  name?: string;
  kvk_number?: string | null;
  btw_number?: string | null;
  address?: string | null;
  postal_code?: string | null;
  city?: string | null;
  iban?: string | null;
  phone?: string | null;
  email?: string | null;
  modules_enabled?: string[];
}

// ── Hooks ────────────────────────────────────────────────────────────────────

export function useTenant() {
  return useQuery<TenantDetail>({
    queryKey: ["tenant"],
    queryFn: async () => {
      const res = await api("/api/settings/tenant");
      if (!res.ok) throw new Error("Fout bij ophalen kantoorgegevens");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: UpdateProfileData) => {
      const res = await api("/api/auth/me", {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij bijwerken profiel");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["auth-user"] });
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: async (data: ChangePasswordData) => {
      const res = await api("/api/auth/change-password", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij wijzigen wachtwoord");
      }
    },
  });
}

export function useUpdateTenant() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: UpdateTenantData) => {
      const res = await api("/api/settings/tenant", {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Fout bij bijwerken kantoorgegevens");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tenant"] });
    },
  });
}
