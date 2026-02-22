"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface CaseSummary {
  id: string;
  case_number: string;
  case_type: string;
  status: string;
  debtor_type: string | null; // 'b2b' | 'b2c'
  description: string | null;
  reference: string | null;
  interest_type: string;
  date_opened: string;
  date_closed: string | null;
  total_principal: number;
  total_paid: number;
  client: { id: string; name: string; email?: string | null } | null;
  opposing_party: { id: string; name: string; email?: string | null } | null;
  created_at: string;
}

export interface CaseDetail extends CaseSummary {
  court_case_number: string | null;
  court_name: string | null;
  judge_name: string | null;
  chamber: string | null;
  procedure_type: string | null;
  procedure_phase: string | null;
  contractual_rate: number | null;
  contractual_compound: boolean;
  billing_contact: { id: string; name: string } | null;
  assigned_to: { id: string; full_name: string } | null;
  parties: {
    id: string;
    role: string;
    external_reference: string | null;
    contact: { id: string; name: string; email?: string | null };
  }[];
  recent_activities: {
    id: string;
    activity_type: string;
    title: string;
    description: string | null;
    created_at: string;
  }[];
}

interface PaginatedCases {
  items: CaseSummary[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

interface CaseCreateInput {
  case_type: string;
  debtor_type?: string; // 'b2b' | 'b2c'
  description?: string;
  reference?: string;
  interest_type?: string;
  contractual_rate?: number;
  contractual_compound?: boolean;
  court_case_number?: string;
  client_id: string;
  opposing_party_id?: string;
  assigned_to_id?: string;
  date_opened: string;
}

export function useCases(params?: {
  page?: number;
  per_page?: number;
  case_type?: string;
  status?: string;
  search?: string;
  client_id?: string;
  assigned_to_id?: string;
  date_from?: string;
  date_to?: string;
  min_amount?: number;
  max_amount?: number;
}) {
  const page = params?.page ?? 1;
  const per_page = params?.per_page ?? 20;
  const case_type = params?.case_type ?? "";
  const status = params?.status ?? "";
  const search = params?.search ?? "";
  const client_id = params?.client_id ?? "";
  const assigned_to_id = params?.assigned_to_id ?? "";
  const date_from = params?.date_from ?? "";
  const date_to = params?.date_to ?? "";
  const min_amount = params?.min_amount;
  const max_amount = params?.max_amount;

  return useQuery<PaginatedCases>({
    queryKey: ["cases", { page, per_page, case_type, status, search, client_id, assigned_to_id, date_from, date_to, min_amount, max_amount }],
    queryFn: async () => {
      const queryParams = new URLSearchParams({
        page: String(page),
        per_page: String(per_page),
      });
      if (case_type) queryParams.set("case_type", case_type);
      if (status) queryParams.set("status", status);
      if (search) queryParams.set("search", search);
      if (client_id) queryParams.set("client_id", client_id);
      if (assigned_to_id) queryParams.set("assigned_to_id", assigned_to_id);
      if (date_from) queryParams.set("date_from", date_from);
      if (date_to) queryParams.set("date_to", date_to);
      if (min_amount !== undefined) queryParams.set("min_amount", String(min_amount));
      if (max_amount !== undefined) queryParams.set("max_amount", String(max_amount));

      const res = await api(`/api/cases?${queryParams}`);
      if (!res.ok) throw new Error("Failed to fetch cases");
      return res.json();
    },
  });
}

export interface ConflictResult {
  conflicts: {
    case_id: string;
    case_number: string;
    case_type: string;
    status: string;
    role_in_case: string;
    client_name: string | null;
    opposing_party_name: string | null;
  }[];
  has_conflict: boolean;
}

export function useConflictCheck(contactId: string | undefined, role: string) {
  return useQuery<ConflictResult>({
    queryKey: ["conflict-check", contactId, role],
    queryFn: async () => {
      const res = await api(
        `/api/cases/conflict-check?contact_id=${contactId}&role=${role}`
      );
      if (!res.ok) throw new Error("Conflict check failed");
      return res.json();
    },
    enabled: !!contactId,
  });
}

export function useCase(id: string | undefined) {
  return useQuery<CaseDetail>({
    queryKey: ["cases", id],
    queryFn: async () => {
      const res = await api(`/api/cases/${id}`);
      if (!res.ok) throw new Error("Failed to fetch case");
      return res.json();
    },
    enabled: !!id,
  });
}

export function useCreateCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CaseCreateInput) => {
      const res = await api("/api/cases", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to create case");
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useUpdateCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: Record<string, unknown>;
    }) => {
      const res = await api(`/api/cases/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Failed to update case");
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      queryClient.invalidateQueries({ queryKey: ["cases", variables.id] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useUpdateCaseStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      new_status,
      note,
    }: {
      id: string;
      new_status: string;
      note?: string;
    }) => {
      const res = await api(`/api/cases/${id}/status`, {
        method: "POST",
        body: JSON.stringify({ new_status, note }),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Invalid status transition");
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      queryClient.invalidateQueries({ queryKey: ["cases", variables.id] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDeleteCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/cases/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete case");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

// ── Case Parties ────────────────────────────────────────────────────────────

export function useAddCaseParty() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      caseId,
      data,
    }: {
      caseId: string;
      data: { contact_id: string; role: string; external_reference?: string };
    }) => {
      const res = await api(`/api/cases/${caseId}/parties`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Partij toevoegen mislukt");
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["cases", variables.caseId] });
    },
  });
}

export function useRemoveCaseParty() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      caseId,
      partyId,
    }: {
      caseId: string;
      partyId: string;
    }) => {
      const res = await api(`/api/cases/${caseId}/parties/${partyId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Partij verwijderen mislukt");
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["cases", variables.caseId] });
    },
  });
}

// ── Case Activities ──────────────────────────────────────────────────────────

export interface CaseActivity {
  id: string;
  activity_type: string;
  title: string;
  description: string | null;
  old_status: string | null;
  new_status: string | null;
  user: { id: string; full_name: string; email: string } | null;
  created_at: string;
}

interface PaginatedActivities {
  items: CaseActivity[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

/** Paginated activities for a case (newest first) */
export function useCaseActivities(caseId: string | undefined, page = 1) {
  return useQuery<PaginatedActivities>({
    queryKey: ["cases", caseId, "activities", page],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: String(page),
        per_page: "20",
      });
      const res = await api(`/api/cases/${caseId}/activities?${params}`);
      if (!res.ok) throw new Error("Fout bij ophalen activiteiten");
      return res.json();
    },
    enabled: !!caseId,
  });
}

/** Add a note/activity to a case */
export function useAddCaseActivity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      caseId,
      data,
    }: {
      caseId: string;
      data: { activity_type: string; title: string; description?: string };
    }) => {
      const res = await api(`/api/cases/${caseId}/activities`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Activiteit toevoegen mislukt");
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["cases", variables.caseId, "activities"],
      });
      queryClient.invalidateQueries({
        queryKey: ["cases", variables.caseId],
      });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
