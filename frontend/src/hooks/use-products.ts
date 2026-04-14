"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface Product {
  id: string;
  code: string;
  name: string;
  description: string | null;
  default_price: number | null;
  gl_account_code: string;
  gl_account_name: string;
  vat_type: string;
  vat_percentage: number;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  code: string;
  name: string;
  description?: string;
  default_price?: number;
  gl_account_code: string;
  gl_account_name: string;
  vat_type?: string;
  vat_percentage?: number;
  is_active?: boolean;
  sort_order?: number;
}

export function useProducts(activeOnly = true) {
  return useQuery<Product[]>({
    queryKey: ["products", { activeOnly }],
    queryFn: async () => {
      const qp = new URLSearchParams();
      qp.set("active_only", String(activeOnly));
      const res = await api(`/api/products?${qp}`);
      if (!res.ok) throw new Error("Kan producten niet laden");
      return res.json();
    },
  });
}

export function useProduct(id: string | undefined) {
  return useQuery<Product>({
    queryKey: ["products", id],
    queryFn: async () => {
      const res = await api(`/api/products/${id}`);
      if (!res.ok) throw new Error("Product niet gevonden");
      return res.json();
    },
    enabled: !!id,
  });
}

export function useCreateProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: ProductCreate) => {
      const res = await api("/api/products", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Aanmaken mislukt");
      }
      return res.json() as Promise<Product>;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  });
}

export function useUpdateProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      ...data
    }: Partial<ProductCreate> & { id: string }) => {
      const res = await api(`/api/products/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Bijwerken mislukt");
      }
      return res.json() as Promise<Product>;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  });
}

export function useDeleteProduct() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/products/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Verwijderen mislukt");
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  });
}

export function useSeedProducts() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const res = await api("/api/products/seed", {
        method: "POST",
      });
      if (!res.ok) throw new Error("Importeren mislukt");
      return res.json() as Promise<{ created: number; message: string }>;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["products"] }),
  });
}
