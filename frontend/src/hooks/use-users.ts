"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { toast } from "sonner";

// ─── Types ────────────────────────────────────────────────────────
export interface UserSummary {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "advocaat" | "medewerker";
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface InviteUserInput {
  email: string;
  full_name: string;
  role: "admin" | "advocaat" | "medewerker";
}

export interface UpdateUserInput {
  full_name?: string;
  role?: "admin" | "advocaat" | "medewerker";
  is_active?: boolean;
}

// ─── Queries ──────────────────────────────────────────────────────
export function useUsers() {
  return useQuery<UserSummary[]>({
    queryKey: ["users"],
    queryFn: async () => {
      const res = await api("/api/users");
      if (!res.ok) throw new Error("Kan gebruikers niet ophalen");
      return res.json();
    },
  });
}

// ─── Mutations ────────────────────────────────────────────────────
export function useInviteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: InviteUserInput) => {
      const res = await api("/api/users/invite", {
        method: "POST",
        body: JSON.stringify(input),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(data?.detail || "Kon gebruiker niet uitnodigen");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      toast.success("Uitnodiging verstuurd");
    },
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...input }: UpdateUserInput & { id: string }) => {
      const res = await api(`/api/users/${id}`, {
        method: "PUT",
        body: JSON.stringify(input),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(data?.detail || "Kon gebruiker niet bijwerken");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      toast.success("Gebruiker bijgewerkt");
    },
  });
}

export function useDeactivateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/users/${id}`, {
        method: "PUT",
        body: JSON.stringify({ is_active: false }),
      });
      if (!res.ok) throw new Error("Kon gebruiker niet deactiveren");
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      toast.success("Gebruiker gedeactiveerd");
    },
  });
}

export function useReactivateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/users/${id}`, {
        method: "PUT",
        body: JSON.stringify({ is_active: true }),
      });
      if (!res.ok) throw new Error("Kon gebruiker niet heractiveren");
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      toast.success("Gebruiker geheractiveerd");
    },
  });
}

// ─── Constants ────────────────────────────────────────────────────
export const ROLE_OPTIONS = [
  { value: "admin", label: "Beheerder", description: "Volledige toegang tot alle functies en instellingen" },
  { value: "advocaat", label: "Advocaat", description: "Zaken beheren, documenten genereren, relaties bekijken" },
  { value: "medewerker", label: "Medewerker", description: "Zaken bekijken, taken uitvoeren, beperkte toegang" },
] as const;
