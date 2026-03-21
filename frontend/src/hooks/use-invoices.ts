"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

// ── Types ────────────────────────────────────────────────────────────────

export interface InvoiceSummary {
  id: string;
  invoice_number: string;
  invoice_type: string; // "invoice" | "credit_note"
  status: string;
  contact_id: string;
  contact_name: string | null;
  case_id: string | null;
  case_number: string | null;
  linked_invoice_id: string | null;
  linked_invoice_number: string | null;
  invoice_date: string;
  due_date: string;
  subtotal: number;
  btw_amount: number;
  total: number;
  created_at: string;
}

export interface InvoiceLine {
  id: string;
  invoice_id: string;
  line_number: number;
  description: string;
  quantity: number;
  unit_price: number;
  line_total: number;
  time_entry_id: string | null;
  expense_id: string | null;
}

export interface CreditNoteBrief {
  id: string;
  invoice_number: string;
  status: string;
  total: number;
  invoice_date: string;
}

export interface InvoiceDetail {
  id: string;
  invoice_number: string;
  invoice_type: string; // "invoice" | "credit_note"
  status: string;
  contact_id: string;
  case_id: string | null;
  linked_invoice_id: string | null;
  invoice_date: string;
  due_date: string;
  paid_date: string | null;
  subtotal: number;
  btw_percentage: number;
  btw_amount: number;
  total: number;
  reference: string | null;
  notes: string | null;
  settlement_type: string | null;  // DF-13: tussentijds | bij_sluiting
  is_active: boolean;
  created_at: string;
  updated_at: string;
  contact: { id: string; name: string } | null;
  case: { id: string; case_number: string } | null;
  lines: InvoiceLine[];
  credit_notes: CreditNoteBrief[];
}

interface PaginatedInvoices {
  items: InvoiceSummary[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

interface InvoiceLineInput {
  description: string;
  quantity?: string | number;
  unit_price: string | number;
  time_entry_id?: string | null;
  expense_id?: string | null;
}

interface InvoiceCreateInput {
  contact_id: string;
  case_id?: string | null;
  invoice_date: string;
  due_date: string;
  btw_percentage?: string | number;
  reference?: string | null;
  notes?: string | null;
  lines: InvoiceLineInput[];
}

interface InvoiceUpdateInput {
  contact_id?: string;
  case_id?: string | null;
  invoice_date?: string;
  due_date?: string;
  btw_percentage?: string | number;
  reference?: string | null;
  notes?: string | null;
}

// ── Status labels ────────────────────────────────────────────────────────

export const INVOICE_STATUS_LABELS: Record<string, string> = {
  concept: "Concept",
  approved: "Goedgekeurd",
  sent: "Verzonden",
  partially_paid: "Deels betaald",
  paid: "Betaald",
  overdue: "Achterstallig",
  cancelled: "Geannuleerd",
};

export const INVOICE_STATUS_COLORS: Record<string, string> = {
  concept: "bg-gray-50 text-gray-700 ring-1 ring-inset ring-gray-600/20",
  approved: "bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-600/20",
  sent: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/20",
  partially_paid: "bg-cyan-50 text-cyan-700 ring-1 ring-inset ring-cyan-600/20",
  paid: "bg-green-50 text-green-700 ring-1 ring-inset ring-green-600/20",
  overdue: "bg-red-50 text-red-700 ring-1 ring-inset ring-red-600/20",
  cancelled: "bg-gray-50 text-gray-400 ring-1 ring-inset ring-gray-400/20",
};

// ── Hooks ────────────────────────────────────────────────────────────────

export function useInvoices(params?: {
  page?: number;
  per_page?: number;
  status?: string;
  search?: string;
  case_id?: string;
}) {
  const page = params?.page ?? 1;
  const per_page = params?.per_page ?? 20;
  const status = params?.status ?? "";
  const search = params?.search ?? "";
  const case_id = params?.case_id ?? "";

  return useQuery<PaginatedInvoices>({
    queryKey: ["invoices", { page, per_page, status, search, case_id }],
    queryFn: async () => {
      const qp = new URLSearchParams({
        page: String(page),
        per_page: String(per_page),
      });
      if (status) qp.set("status", status);
      if (search) qp.set("search", search);
      if (case_id) qp.set("case_id", case_id);
      const res = await api(`/api/invoices?${qp}`);
      if (!res.ok) throw new Error("Kan facturen niet laden");
      return res.json();
    },
  });
}

export function useInvoice(id: string | undefined) {
  return useQuery<InvoiceDetail>({
    queryKey: ["invoices", id],
    queryFn: async () => {
      const res = await api(`/api/invoices/${id}`);
      if (!res.ok) throw new Error("Kan factuur niet laden");
      return res.json();
    },
    enabled: !!id,
  });
}

export function useCreateInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: InvoiceCreateInput) => {
      const res = await api("/api/invoices", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Aanmaken mislukt");
      }
      return res.json();
    },
    onSuccess: (data) => {
      if (data?.id) {
        qc.setQueryData(["invoices", data.id], data);
      }
      qc.invalidateQueries({ queryKey: ["invoices"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useUpdateInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: InvoiceUpdateInput;
    }) => {
      const res = await api(`/api/invoices/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Bijwerken mislukt");
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ["invoices"] });
      qc.invalidateQueries({ queryKey: ["invoices", variables.id] });
    },
  });
}

export function useDeleteInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/invoices/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Verwijderen mislukt");
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["invoices"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

// ── Credit Notes ────────────────────────────────────────────────────────

interface CreditNoteCreateInput {
  linked_invoice_id: string;
  invoice_date: string;
  due_date: string;
  btw_percentage?: number;
  reference?: string;
  notes?: string;
  lines: InvoiceLineInput[];
}

export function useCreateCreditNote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: CreditNoteCreateInput) => {
      const res = await api("/api/invoices/credit-note", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Credit nota aanmaken mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["invoices"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

// ── Status Transitions ──────────────────────────────────────────────────

export function useApproveInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/invoices/${id}/approve`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Goedkeuren mislukt");
      }
      return res.json();
    },
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ["invoices"] });
      qc.invalidateQueries({ queryKey: ["invoices", id] });
    },
  });
}

export function useSendInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/invoices/${id}/send`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Verzenden mislukt");
      }
      return res.json();
    },
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ["invoices"] });
      qc.invalidateQueries({ queryKey: ["invoices", id] });
    },
  });
}

export function useMarkInvoicePaid() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, paid_date }: { id: string; paid_date?: string }) => {
      const qp = paid_date ? `?paid_date=${paid_date}` : "";
      const res = await api(`/api/invoices/${id}/mark-paid${qp}`, {
        method: "POST",
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Markeren als betaald mislukt");
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ["invoices"] });
      qc.invalidateQueries({ queryKey: ["invoices", variables.id] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useCancelInvoice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api(`/api/invoices/${id}/cancel`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Annuleren mislukt");
      }
      return res.json();
    },
    onSuccess: (_, id) => {
      qc.invalidateQueries({ queryKey: ["invoices"] });
      qc.invalidateQueries({ queryKey: ["invoices", id] });
    },
  });
}

// ── Invoice Lines ───────────────────────────────────────────────────────

export function useAddInvoiceLine() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      invoiceId,
      data,
    }: {
      invoiceId: string;
      data: InvoiceLineInput;
    }) => {
      const res = await api(`/api/invoices/${invoiceId}/lines`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Regel toevoegen mislukt");
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ["invoices", variables.invoiceId] });
    },
  });
}

// ── Invoice Payments ────────────────────────────────────────────────────

export interface InvoicePayment {
  id: string;
  invoice_id: string;
  amount: number;
  payment_date: string;
  payment_method: string;
  reference: string | null;
  description: string | null;
  created_by: string;
  created_at: string;
  creator: { id: string; full_name: string; email: string };
}

export interface InvoicePaymentSummary {
  invoice_id: string;
  invoice_total: number;
  total_paid: number;
  outstanding: number;
  payment_count: number;
  is_fully_paid: boolean;
}

export function useInvoicePayments(invoiceId: string | undefined) {
  return useQuery<InvoicePayment[]>({
    queryKey: ["invoices", invoiceId, "payments"],
    queryFn: async () => {
      const res = await api(`/api/invoices/${invoiceId}/payments`);
      if (!res.ok) throw new Error("Kan betalingen niet laden");
      return res.json();
    },
    enabled: !!invoiceId,
  });
}

export function useInvoicePaymentSummary(invoiceId: string | undefined) {
  return useQuery<InvoicePaymentSummary>({
    queryKey: ["invoices", invoiceId, "payment-summary"],
    queryFn: async () => {
      const res = await api(`/api/invoices/${invoiceId}/payment-summary`);
      if (!res.ok) throw new Error("Kan betalingsoverzicht niet laden");
      return res.json();
    },
    enabled: !!invoiceId,
  });
}

export function useCreateInvoicePayment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      invoiceId,
      data,
    }: {
      invoiceId: string;
      data: {
        amount: string;
        payment_date: string;
        payment_method: string;
        reference?: string;
        description?: string;
      };
    }) => {
      const res = await api(`/api/invoices/${invoiceId}/payments`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Betaling registreren mislukt");
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ["invoices", variables.invoiceId] });
      qc.invalidateQueries({ queryKey: ["invoices"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDeleteInvoicePayment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      invoiceId,
      paymentId,
    }: {
      invoiceId: string;
      paymentId: string;
    }) => {
      const res = await api(`/api/invoices/${invoiceId}/payments/${paymentId}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Betaling verwijderen mislukt");
      }
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ["invoices", variables.invoiceId] });
      qc.invalidateQueries({ queryKey: ["invoices"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useRemoveInvoiceLine() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      invoiceId,
      lineId,
    }: {
      invoiceId: string;
      lineId: string;
    }) => {
      const res = await api(`/api/invoices/${invoiceId}/lines/${lineId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Regel verwijderen mislukt");
    },
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ["invoices", variables.invoiceId] });
    },
  });
}

// ── Receivables / Aging ─────────────────────────────────────────────────

export interface AgingBucket {
  count: number;
  total: number;
}

export interface ContactReceivable {
  contact_id: string;
  contact_name: string;
  invoice_count: number;
  total_outstanding: number;
  current: AgingBucket;
  days_31_60: AgingBucket;
  days_61_90: AgingBucket;
  days_90_plus: AgingBucket;
  oldest_due_date: string;
}

export interface ReceivablesSummary {
  total_outstanding: number;
  total_overdue: number;
  current: AgingBucket;
  days_31_60: AgingBucket;
  days_61_90: AgingBucket;
  days_90_plus: AgingBucket;
  contacts: ContactReceivable[];
}

export function useReceivables() {
  return useQuery<ReceivablesSummary>({
    queryKey: ["invoices", "receivables"],
    queryFn: async () => {
      const res = await api("/api/invoices/receivables");
      if (!res.ok) throw new Error("Kan debiteurenoverzicht niet laden");
      return res.json();
    },
  });
}

// ── LF-20/LF-21: Voorschotnota, Budget, Provisie ───────────────────────────

export interface VoorschotnotaInput {
  case_id: string;
  contact_id: string;
  amount: number;
  description?: string;
  invoice_date: string;
  due_date: string;
  btw_percentage: number;
  settlement_type?: "tussentijds" | "bij_sluiting";  // DF-13
}

export function useCreateVoorschotnota() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: VoorschotnotaInput) => {
      const res = await api("/api/invoices/voorschotnota", {
        method: "POST",
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Voorschotnota aanmaken mislukt");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["invoices"] });
      qc.invalidateQueries({ queryKey: ["advance-balance"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export interface AdvanceBalance {
  case_id: string;
  total_advance: number;
  total_offset: number;
  available_balance: number;
}

export function useAdvanceBalance(caseId: string | undefined) {
  return useQuery<AdvanceBalance>({
    queryKey: ["advance-balance", caseId],
    queryFn: async () => {
      const res = await api(`/api/cases/${caseId}/advance-balance`);
      if (!res.ok) throw new Error("Kan voorschotsaldo niet laden");
      return res.json();
    },
    enabled: !!caseId,
  });
}

export interface BudgetStatus {
  used_amount: number;
  used_hours: number;
  budget_amount: number;
  budget_hours: number;
  percentage_amount: number;
  percentage_hours: number;
  status: "green" | "orange" | "red";
}

export function useBudgetStatus(caseId: string | undefined) {
  return useQuery<BudgetStatus>({
    queryKey: ["budget-status", caseId],
    queryFn: async () => {
      const res = await api(`/api/cases/${caseId}/budget-status`);
      if (!res.ok) throw new Error("Kan budgetstatus niet laden");
      return res.json();
    },
    enabled: !!caseId,
  });
}

export interface ProvisieData {
  collected_amount: number;
  provisie_percentage: number;
  provisie_amount: number;
  fixed_case_costs: number;
  minimum_fee: number;
  total_fee: number;
}

export function useProvisie(caseId: string | undefined) {
  return useQuery<ProvisieData>({
    queryKey: ["provisie", caseId],
    queryFn: async () => {
      const res = await api(`/api/cases/${caseId}/provisie`);
      if (!res.ok) throw new Error("Kan provisie niet laden");
      return res.json();
    },
    enabled: !!caseId,
  });
}
