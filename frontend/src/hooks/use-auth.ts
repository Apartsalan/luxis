"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

// ─── Types ────────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "advocaat" | "medewerker";
  tenant_id: string;
}

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

// ─── Context ──────────────────────────────────────────────────────
export const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  logout: () => {},
  refreshUser: async () => {},
});

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

// ─── Provider logic (used in AuthProvider component) ──────────────
export function useAuthProvider() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const fetchUser = useCallback(async () => {
    const token = localStorage.getItem("luxis_access_token");
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const res = await api("/api/auth/me");
      if (!res.ok) throw new Error("Unauthorized");
      const data = await res.json();
      setUser(data);
    } catch {
      localStorage.removeItem("luxis_access_token");
      localStorage.removeItem("luxis_refresh_token");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const logout = useCallback(() => {
    localStorage.removeItem("luxis_access_token");
    localStorage.removeItem("luxis_refresh_token");
    setUser(null);
    router.push("/login");
  }, [router]);

  return { user, loading, logout, refreshUser: fetchUser };
}

// ─── Role helpers ─────────────────────────────────────────────────
export function useRequireRole(allowedRoles: User["role"][]) {
  const { user } = useAuth();
  return user ? allowedRoles.includes(user.role) : false;
}

export const ROLE_LABELS: Record<User["role"], string> = {
  admin: "Beheerder",
  advocaat: "Advocaat",
  medewerker: "Medewerker",
};
