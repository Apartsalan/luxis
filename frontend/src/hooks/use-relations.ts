"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface ContactSummary {
  id: string;
  contact_type: "company" | "person";
  name: string;
  email: string | null;
  phone: string | null;
  kvk_number: string | null;
  is_active: boolean;
}

export interface LinkedContactInfo {
  link_id: string;
  role_at_company: string | null;
  contact: ContactSummary;
}

export interface Contact {
  id: string;
  contact_type: "company" | "person";
  name: string;
  first_name: string | null;
  last_name: string | null;
  date_of_birth: string | null;
  email: string | null;
  phone: string | null;
  kvk_number: string | null;
  btw_number: string | null;
  visit_address: string | null;
  visit_postcode: string | null;
  visit_city: string | null;
  postal_address: string | null;
  postal_postcode: string | null;
  postal_city: string | null;
  default_hourly_rate: number | null;
  payment_term_days: number | null;
  billing_email: string | null;
  iban: string | null;
  default_interest_type: string | null;
  default_contractual_rate: number | null;
  default_rate_basis: string | null;
  default_bik_override: number | null;
  default_bik_override_percentage: number | null;
  default_minimum_fee: number | null;
  is_btw_plichtig: boolean;
  terms_file_name: string | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  linked_companies?: LinkedContactInfo[];
  linked_persons?: LinkedContactInfo[];
}

interface PaginatedContacts {
  items: Contact[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

interface ContactCreateInput {
  contact_type: "company" | "person";
  name: string;
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  email?: string;
  phone?: string;
  kvk_number?: string;
  btw_number?: string;
  visit_address?: string;
  visit_postcode?: string;
  visit_city?: string;
  postal_address?: string;
  postal_postcode?: string;
  postal_city?: string;
  default_hourly_rate?: number;
  payment_term_days?: number;
  billing_email?: string;
  iban?: string;
  default_interest_type?: string;
  default_contractual_rate?: string | number;
  default_rate_basis?: string;
  default_bik_override?: string | number;
  default_bik_override_percentage?: string | number;
  default_minimum_fee?: string | number;
  is_btw_plichtig?: boolean;
  notes?: string;
}

export function useRelations(params?: {
  page?: number;
  per_page?: number;
  search?: string;
  contact_type?: string;
}) {
  const page = params?.page ?? 1;
  const per_page = params?.per_page ?? 20;
  const search = params?.search ?? "";
  const contact_type = params?.contact_type ?? "";

  return useQuery<PaginatedContacts>({
    queryKey: ["relations", { page, per_page, search, contact_type }],
    queryFn: async () => {
      const queryParams = new URLSearchParams({
        page: String(page),
        per_page: String(per_page),
      });
      if (search) queryParams.set("search", search);
      if (contact_type) queryParams.set("contact_type", contact_type);

      const res = await api(`/api/relations?${queryParams}`);
      if (!res.ok) throw new Error("Failed to fetch relations");
      return res.json();
    },
  });
}

export function useRelation(id: string | undefined) {
  return useQuery<Contact>({
    queryKey: ["relations", id],
    queryFn: async () => {
      const res = await api(`/api/relations/${id}`);
      if (!res.ok) throw new Error("Failed to fetch relation");
      return res.json();
    },
    enabled: !!id,
  });
}

export function useCreateRelation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ContactCreateInput) => {
      const res = await api("/api/relations", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to create relation");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["relations"] });
    },
  });
}

export function useUpdateRelation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: Partial<ContactCreateInput>;
    }) => {
      const res = await api(`/api/relations/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to update relation");
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["relations"] });
      queryClient.invalidateQueries({
        queryKey: ["relations", variables.id],
      });
    },
  });
}

export function useDeleteRelation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/relations/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete relation");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["relations"] });
    },
  });
}

// ── Contact Links ────────────────────────────────────────────────────────────

export function useSearchRelations(search: string, contactType?: "company" | "person") {
  return useQuery<PaginatedContacts>({
    queryKey: ["relations", "search", { search, contactType }],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: "1",
        per_page: "10",
        search,
      });
      if (contactType) params.set("contact_type", contactType);

      const res = await api(`/api/relations?${params}`);
      if (!res.ok) throw new Error("Failed to search relations");
      return res.json();
    },
    enabled: search.length >= 2,
  });
}

export function useCreateContactLink() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      person_id: string;
      company_id: string;
      role_at_company?: string | null;
    }) => {
      const res = await api("/api/relations/links", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Koppeling aanmaken mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["relations"] });
    },
  });
}

export function useDeleteContactLink() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (linkId: string) => {
      const res = await api(`/api/relations/links/${linkId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Koppeling verwijderen mislukt");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["relations"] });
    },
  });
}
