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
  invoice_file_id: string | null;
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

export interface TrustTransactionUser {
  id: string;
  full_name: string;
  email: string;
}

export interface DerdengeldenTransaction {
  id: string;
  tenant_id: string;
  case_id: string;
  contact_id: string;
  transaction_type: "deposit" | "disbursement";
  amount: number;
  description: string;
  payment_method: string | null;
  reference: string | null;
  beneficiary_name: string | null;
  beneficiary_iban: string | null;
  status: "pending_approval" | "approved" | "rejected";
  approved_by_1: string | null;
  approved_at_1: string | null;
  approved_by_2: string | null;
  approved_at_2: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  creator: TrustTransactionUser;
  approver_1: TrustTransactionUser | null;
  approver_2: TrustTransactionUser | null;
}

export interface DerdengeldenBalance {
  case_id: string;
  total_deposits: number;
  total_disbursements: number;
  total_balance: number;
  pending_disbursements: number;
  available: number;
}

// ── Payment Arrangements ─────────────────────────────────────────────────────

export interface Installment {
  id: string;
  arrangement_id: string;
  installment_number: number;
  due_date: string;
  amount: number;
  paid_amount: number;
  paid_date: string | null;
  payment_id: string | null;
  status: "pending" | "paid" | "overdue" | "missed" | "waived" | "partial";
  notes: string | null;
  created_at: string;
}

export interface Arrangement {
  id: string;
  case_id: string;
  total_amount: number;
  installment_amount: number;
  frequency: "weekly" | "monthly" | "quarterly";
  start_date: string;
  end_date: string | null;
  status: "active" | "completed" | "defaulted" | "cancelled";
  notes: string | null;
  created_at: string;
}

export interface ArrangementWithInstallments extends Arrangement {
  installments: Installment[];
  paid_count: number;
  total_paid_amount: number;
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
        principal_amount: string;
        default_date: string;
        invoice_number?: string;
        invoice_date?: string;
        rate_basis?: string;
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

export function useUpdateClaim() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      caseId,
      claimId,
      data,
    }: {
      caseId: string;
      claimId: string;
      data: {
        description?: string;
        principal_amount?: string;
        default_date?: string;
        invoice_number?: string | null;
        invoice_date?: string | null;
        invoice_file_id?: string | null;
        rate_basis?: string;
      };
    }) => {
      const res = await api(`/api/cases/${caseId}/claims/${claimId}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to update claim");
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
        amount: string;
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
  return useQuery<{ items: DerdengeldenTransaction[]; total: number }>({
    queryKey: ["trust-funds", caseId, "transactions"],
    queryFn: async () => {
      const res = await api(`/api/trust-funds/cases/${caseId}/transactions?per_page=100`);
      if (!res.ok) throw new Error("Failed to fetch derdengelden");
      return res.json();
    },
    enabled: !!caseId,
  });
}

export function useDerdengeldenBalance(caseId: string | undefined) {
  return useQuery<DerdengeldenBalance>({
    queryKey: ["trust-funds", caseId, "balance"],
    queryFn: async () => {
      const res = await api(`/api/trust-funds/cases/${caseId}/balance`);
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
        transaction_type: "deposit" | "disbursement";
        amount: string;
        description: string;
        payment_method?: string;
        reference?: string;
        beneficiary_name?: string;
        beneficiary_iban?: string;
      };
    }) => {
      const res = await api(`/api/trust-funds/cases/${caseId}/transactions`, {
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
      qc.invalidateQueries({ queryKey: ["trust-funds", vars.caseId] });
    },
  });
}

export function useApproveTrustTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ transactionId }: { transactionId: string; caseId: string }) => {
      const res = await api(`/api/trust-funds/transactions/${transactionId}/approve`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Goedkeuring mislukt");
      }
      return res.json();
    },
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["trust-funds", vars.caseId] });
    },
  });
}

export function useRejectTrustTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ transactionId }: { transactionId: string; caseId: string }) => {
      const res = await api(`/api/trust-funds/transactions/${transactionId}/reject`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Afwijzing mislukt");
      }
      return res.json();
    },
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["trust-funds", vars.caseId] });
    },
  });
}

// ── Payment Arrangements Hooks ──────────────────────────────────────────────

export function useArrangements(caseId: string | undefined) {
  return useQuery<ArrangementWithInstallments[]>({
    queryKey: ["cases", caseId, "arrangements"],
    queryFn: async () => {
      const res = await api(`/api/cases/${caseId}/arrangements`);
      if (!res.ok) throw new Error("Failed to fetch arrangements");
      return res.json();
    },
    enabled: !!caseId,
  });
}

export function useCreateArrangement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      caseId,
      data,
    }: {
      caseId: string;
      data: {
        total_amount: string;
        installment_amount: string;
        frequency: string;
        start_date: string;
        notes?: string;
      };
    }) => {
      const res = await api(`/api/cases/${caseId}/arrangements`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Betalingsregeling aanmaken mislukt");
      }
      return res.json();
    },
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["cases", vars.caseId] });
    },
  });
}

export function useRecordInstallmentPayment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      caseId,
      arrangementId,
      installmentId,
      data,
    }: {
      caseId: string;
      arrangementId: string;
      installmentId: string;
      data: {
        amount: string;
        payment_date: string;
        payment_method?: string;
        notes?: string;
      };
    }) => {
      const res = await api(
        `/api/cases/${caseId}/arrangements/${arrangementId}/installments/${installmentId}/record-payment`,
        { method: "POST", body: JSON.stringify(data) }
      );
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Betaling registreren mislukt");
      }
      return res.json();
    },
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["cases", vars.caseId] });
    },
  });
}

export function useDefaultArrangement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      caseId,
      arrangementId,
    }: {
      caseId: string;
      arrangementId: string;
    }) => {
      const res = await api(
        `/api/cases/${caseId}/arrangements/${arrangementId}/default`,
        { method: "PATCH" }
      );
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Wanprestatie markeren mislukt");
      }
      return res.json();
    },
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["cases", vars.caseId] });
    },
  });
}

export function useCancelArrangement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      caseId,
      arrangementId,
    }: {
      caseId: string;
      arrangementId: string;
    }) => {
      const res = await api(
        `/api/cases/${caseId}/arrangements/${arrangementId}/cancel`,
        { method: "PATCH" }
      );
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Annuleren mislukt");
      }
      return res.json();
    },
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["cases", vars.caseId] });
    },
  });
}

export function useWaiveInstallment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      caseId,
      arrangementId,
      installmentId,
    }: {
      caseId: string;
      arrangementId: string;
      installmentId: string;
    }) => {
      const res = await api(
        `/api/cases/${caseId}/arrangements/${arrangementId}/installments/${installmentId}/waive`,
        { method: "PATCH" }
      );
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Kwijtschelden mislukt");
      }
      return res.json();
    },
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["cases", vars.caseId] });
    },
  });
}
