"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────────

export interface Claim {
  id: string;
  case_id: string;
  description: string;
  principal_amount: number;
  default_date: string;
  invoice_number: string | null;
  invoice_date: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Payment {
  id: string;
  case_id: string;
  amount: number;
  payment_date: string;
  description: string | null;
  payment_method: string | null;
  allocated_to_costs: number;
  allocated_to_interest: number;
  allocated_to_principal: number;
  is_active: boolean;
  created_at: string;
}

export interface InterestPeriod {
  start_date: string;
  end_date: string;
  days: number;
  rate: number;
  principal: number;
  interest: number;
}

export interface ClaimInterest {
  claim_id: string;
  description: string;
  principal_amount: number;
  default_date: string;
  total_interest: number;
  periods: InterestPeriod[];
}

export interface CaseInterestSummary {
  case_id: string;
  calculation_date: string;
  interest_type: string;
  total_principal: number;
  total_interest: number;
  total_outstanding: number;
  claims: ClaimInterest[];
}

export interface BIKResult {
  principal: number;
  bik_amount: number;
  bik_btw: number;
  total_bik: number;
  include_btw: boolean;
}

export interface FinancialSummary {
  case_id: string;
  calculation_date: string;
  total_principal: number;
  total_paid_principal: number;
  remaining_principal: number;
  total_interest: number;
  total_paid_interest: number;
  remaining_interest: number;
  bik_amount: number;
  bik_btw: number;
  total_bik: number;
  total_paid_costs: number;
  remaining_costs: number;
  grand_total: number;
  total_paid: number;
  total_outstanding: number;
  derdengelden_balance: number;
}

export interface DerdengeldenTransaction {
  id: string;
  case_id: string;
  transaction_type: "deposit" | "withdrawal";
  amount: number;
  transaction_date: string;
  description: string | null;
  counterparty: string | null;
  created_at: string;
}

export interface DerdengeldenBalance {
  total_deposits: number;
  total_withdrawals: number;
  balance: number;
}

// ── Claims ───────────────────────────────────────────────────────────────────

export function useClaims(caseId: string | undefined) {
  return useQuery<Claim[]>({
    queryKey: ["cases", caseId, "claims"],
    queryFn: async () => {
      const res = await api(`/api/cases/${caseId}/claims`);
      if (!res.ok) throw new Error("Failed to fetch claims");
      return res.json();
    },
    enabled: !!caseId,
  });
}

export function useCreateClaim() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      caseId,
      data,
    }: {
      caseId: string;
      data: {
        description: string;
        principal_amount: number;
        default_date: string;
        invoice_number?: string;
        invoice_date?: string;
      };
    }) => {
      const res = await api(`/api/cases/${caseId}/claims`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to create claim");
      }
      return res.json();
    },
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["cases", vars.caseId] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDeleteClaim() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      caseId,
      claimId,
    }: {
      caseId: string;
      claimId: string;
    }) => {
      const res = await api(`/api/cases/${caseId}/claims/${claimId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete claim");
    },
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["cases", vars.caseId] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

// ── Interest ─────────────────────────────────────────────────────────────────

export function useCaseInterest(caseId: string | undefined, asOf?: string) {
  return useQuery<CaseInterestSummary>({
    queryKey: ["cases", caseId, "interest", asOf],
    queryFn: async () => {
      const params = asOf ? `?as_of=${asOf}` : "";
      const res = await api(`/api/cases/${caseId}/interest${params}`);
      if (!res.ok) throw new Error("Failed to fetch interest");
      return res.json();
    },
    enabled: !!caseId,
  });
}

// ── BIK ──────────────────────────────────────────────────────────────────────

export function useCaseBIK(caseId: string | undefined) {
  return useQuery<BIKResult>({
    queryKey: ["cases", caseId, "bik"],
    queryFn: async () => {
      const res = await api(`/api/cases/${caseId}/bik`);
      if (!res.ok) throw new Error("Failed to fetch BIK");
      return res.json();
    },
    enabled: !!caseId,
  });
}

// ── Payments ─────────────────────────────────────────────────────────────────

export function usePayments(caseId: string | undefined) {
  return useQuery<Payment[]>({
    queryKey: ["cases", caseId, "payments"],
    queryFn: async () => {
      const res = await api(`/api/cases/${caseId}/payments`);
      if (!res.ok) throw new Error("Failed to fetch payments");
      return res.json();
    },
    enabled: !!caseId,
  });
}

export function useCreatePayment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      caseId,
      data,
    }: {
      caseId: string;
      data: {
        amount: number;
        payment_date: string;
        description?: string;
        payment_method?: string;
      };
    }) => {
      const res = await api(`/api/cases/${caseId}/payments`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to register payment");
      }
      return res.json();
    },
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["cases", vars.caseId] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

// ── Financial Summary ────────────────────────────────────────────────────────

export function useFinancialSummary(caseId: string | undefined) {
  return useQuery<FinancialSummary>({
    queryKey: ["cases", caseId, "financial-summary"],
    queryFn: async () => {
      const res = await api(`/api/cases/${caseId}/financial-summary`);
      if (!res.ok) throw new Error("Failed to fetch financial summary");
      return res.json();
    },
    enabled: !!caseId,
  });
}

// ── Derdengelden ─────────────────────────────────────────────────────────────

export function useDerdengelden(caseId: string | undefined) {
  return useQuery<DerdengeldenTransaction[]>({
    queryKey: ["cases", caseId, "derdengelden"],
    queryFn: async () => {
      const res = await api(`/api/cases/${caseId}/derdengelden`);
      if (!res.ok) throw new Error("Failed to fetch derdengelden");
      return res.json();
    },
    enabled: !!caseId,
  });
}

export function useDerdengeldenBalance(caseId: string | undefined) {
  return useQuery<DerdengeldenBalance>({
    queryKey: ["cases", caseId, "derdengelden", "balance"],
    queryFn: async () => {
      const res = await api(`/api/cases/${caseId}/derdengelden/balance`);
      if (!res.ok) throw new Error("Failed to fetch balance");
      return res.json();
    },
    enabled: !!caseId,
  });
}

export function useCreateDerdengelden() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      caseId,
      data,
    }: {
      caseId: string;
      data: {
        transaction_type: "deposit" | "withdrawal";
        amount: number;
        transaction_date: string;
        description?: string;
        counterparty?: string;
      };
    }) => {
      const res = await api(`/api/cases/${caseId}/derdengelden`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to create transaction");
      }
      return res.json();
    },
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["cases", vars.caseId] });
    },
  });
}
