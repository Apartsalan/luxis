"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("luxis_access_token");
    if (!token) {
      setLoading(false);
      router.push("/login");
      return;
    }

    // Fetch current user
    api("/auth/me")
      .then((res) => {
        if (!res.ok) throw new Error("Unauthorized");
        return res.json();
      })
      .then((data) => {
        setUser(data);
        setLoading(false);
      })
      .catch(() => {
        localStorage.removeItem("luxis_access_token");
        localStorage.removeItem("luxis_refresh_token");
        setLoading(false);
        router.push("/login");
      });
  }, [router]);

  const logout = () => {
    localStorage.removeItem("luxis_access_token");
    localStorage.removeItem("luxis_refresh_token");
    setUser(null);
    router.push("/login");
  };

  return { user, loading, logout };
}
