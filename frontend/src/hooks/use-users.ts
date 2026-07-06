"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

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

// ─── Queries ──────────────────────────────────────────────────────
// Alleen-lezen: de backend biedt GET /api/users. Uitnodigen/wijzigen/deactiveren
// bestaat (bewust) niet — nieuwe gebruiker via /api/auth/register.
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

// ─── Constants ────────────────────────────────────────────────────
export const ROLE_OPTIONS = [
  { value: "admin", label: "Beheerder", description: "Volledige toegang tot alle functies en instellingen" },
  { value: "advocaat", label: "Advocaat", description: "Dossiers beheren, documenten genereren, relaties bekijken" },
  { value: "medewerker", label: "Medewerker", description: "Dossiers bekijken, taken uitvoeren, beperkte toegang" },
] as const;
