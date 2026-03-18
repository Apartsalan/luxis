"use client";

import { useState, useRef, useEffect } from "react";
import {
  AlertTriangle,
  ArrowDownLeft,
  ArrowUpRight,
  Ban,
  Calendar,
  CheckCircle2,
  ChevronDown,
  Clock,
  Euro,
  FileText,
  Loader2,
  MoreHorizontal,
  Pencil,
  Plus,
  Receipt,
  Save,
  ShieldCheck,
  Trash2,
  Wallet,
  X,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import {
  useClaims,
  useCreateClaim,
  useUpdateClaim,
  useDeleteClaim,
  usePayments,
  useCreatePayment,
  useCaseInterest,
  useFinancialSummary,
  useDerdengelden,
  useDerdengeldenBalance,
  useCreateDerdengelden,
  useApproveTrustTransaction,
  useRejectTrustTransaction,
  useArrangements,
  useCreateArrangement,
  useRecordInstallmentPayment,
  useDefaultArrangement,
  useCancelArrangement,
  useWaiveInstallment,
} from "@/hooks/use-collections";
import type { Installment, ArrangementWithInstallments } from "@/hooks/use-collections";
import { useCase, useUpdateCase } from "@/hooks/use-cases";
import { useProvisie } from "@/hooks/use-invoices";
import { useCaseFiles } from "@/hooks/use-case-files";
import { formatCurrency, formatDate, formatDateShort } from "@/lib/utils";

// ── Vorderingen Tab ──────────────────────────────────────────────────────────

export function VorderingenTab({ caseId }: { caseId: string }) {
  const { data: claims, isLoading } = useClaims(caseId);
  const { data: interest } = useCaseInterest(caseId);
  const { data: caseFiles } = useCaseFiles(caseId);
  const createClaim = useCreateClaim();
  const updateClaim = useUpdateClaim();
  const deleteClaim = useDeleteClaim();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({
    description: "",
    principal_amount: "",
    default_date: "",
    invoice_number: "",
    invoice_date: "",
    invoice_file_id: "",
    rate_basis: "yearly",
  });
  const [form, setForm] = useState({
    description: "",
    principal_amount: "",
    default_date: "",
    invoice_number: "",
    invoice_date: "",
    rate_basis: "yearly",
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createClaim.mutateAsync({
        caseId,
        data: {
          description: form.description,
          principal_amount: parseFloat(form.principal_amount),
          default_date: form.default_date,
          ...(form.invoice_number && { invoice_number: form.invoice_number }),
          ...(form.invoice_date && { invoice_date: form.invoice_date }),
          rate_basis: form.rate_basis,
        },
      });
      toast.success("Vordering toegevoegd");
      setShowForm(false);
      setForm({
        description: "",
        principal_amount: "",
        default_date: "",
        invoice_number: "",
        invoice_date: "",
        rate_basis: "yearly",
      });
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleDelete = async (claimId: string) => {
    if (!confirm("Vordering verwijderen?")) return;
    try {
      await deleteClaim.mutateAsync({ caseId, claimId });
      toast.success("Vordering verwijderd");
    } catch {
      toast.error("Kon niet verwijderen");
    }
  };

  const startEdit = (claim: { id: string; description: string; principal_amount: number; default_date: string; invoice_number: string | null; invoice_date: string | null; invoice_file_id: string | null; rate_basis?: string }) => {
    setEditingId(claim.id);
    setEditForm({
      description: claim.description,
      principal_amount: String(claim.principal_amount),
      default_date: claim.default_date,
      invoice_number: claim.invoice_number || "",
      invoice_date: claim.invoice_date || "",
      invoice_file_id: claim.invoice_file_id || "",
      rate_basis: claim.rate_basis || "yearly",
    });
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingId) return;
    try {
      await updateClaim.mutateAsync({
        caseId,
        claimId: editingId,
        data: {
          description: editForm.description,
          principal_amount: parseFloat(editForm.principal_amount),
          default_date: editForm.default_date,
          ...(editForm.invoice_number ? { invoice_number: editForm.invoice_number } : { invoice_number: null }),
          ...(editForm.invoice_date ? { invoice_date: editForm.invoice_date } : { invoice_date: null }),
          ...(editForm.invoice_file_id ? { invoice_file_id: editForm.invoice_file_id } : { invoice_file_id: null }),
          rate_basis: editForm.rate_basis,
        },
      });
      toast.success("Vordering bijgewerkt");
      setEditingId(null);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">
          Vorderingen
        </h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          Vordering toevoegen
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-3"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-foreground">
                Beschrijving *
              </label>
              <input
                type="text"
                required
                value={form.description}
                onChange={(e) =>
                  setForm((f) => ({ ...f, description: e.target.value }))
                }
                className={inputClass}
                placeholder="Factuur nr. 2025-001"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Hoofdsom *
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={form.principal_amount}
                onChange={(e) =>
                  setForm((f) => ({ ...f, principal_amount: e.target.value }))
                }
                className={inputClass}
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Verzuimdatum *
              </label>
              <input
                type="date"
                required
                value={form.default_date}
                onChange={(e) =>
                  setForm((f) => ({ ...f, default_date: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Factuurnummer
              </label>
              <input
                type="text"
                value={form.invoice_number}
                onChange={(e) =>
                  setForm((f) => ({ ...f, invoice_number: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Rentefrequentie
              </label>
              <select
                value={form.rate_basis}
                onChange={(e) =>
                  setForm((f) => ({ ...f, rate_basis: e.target.value }))
                }
                className={inputClass}
              >
                <option value="yearly">Per jaar</option>
                <option value="monthly">Per maand</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createClaim.isPending}
              className="rounded-lg bg-primary px-4 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {createClaim.isPending ? "Opslaan..." : "Opslaan"}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-medium hover:bg-muted"
            >
              Annuleren
            </button>
          </div>
        </form>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg skeleton" />
          ))}
        </div>
      ) : claims && claims.length > 0 ? (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Beschrijving
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Hoofdsom
                </th>
                <th className="hidden sm:table-cell px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Verzuimdatum
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Rente
                </th>
                <th className="px-4 py-3 w-10" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {claims.map((claim) => {
                const claimInterest = interest?.claims.find(
                  (c) => c.claim_id === claim.id
                );
                const isEditing = editingId === claim.id;

                if (isEditing) {
                  return (
                    <tr key={claim.id} className="bg-muted/20">
                      <td className="px-4 py-2">
                        <input
                          type="text"
                          value={editForm.description}
                          onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
                          className={inputClass}
                          placeholder="Beschrijving"
                        />
                        <input
                          type="text"
                          value={editForm.invoice_number}
                          onChange={(e) => setEditForm((f) => ({ ...f, invoice_number: e.target.value }))}
                          className={`${inputClass} mt-1`}
                          placeholder="Factuurnummer (optioneel)"
                        />
                        {caseFiles && caseFiles.length > 0 && (
                          <select
                            value={editForm.invoice_file_id}
                            onChange={(e) => setEditForm((f) => ({ ...f, invoice_file_id: e.target.value }))}
                            className={`${inputClass} mt-1`}
                          >
                            <option value="">Gekoppeld bestand (optioneel)</option>
                            {caseFiles.map((file) => (
                              <option key={file.id} value={file.id}>
                                {file.original_filename}
                              </option>
                            ))}
                          </select>
                        )}
                        <select
                          value={editForm.rate_basis}
                          onChange={(e) => setEditForm((f) => ({ ...f, rate_basis: e.target.value }))}
                          className={`${inputClass} mt-1`}
                        >
                          <option value="yearly">Rente per jaar</option>
                          <option value="monthly">Rente per maand</option>
                        </select>
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          step="0.01"
                          min="0.01"
                          value={editForm.principal_amount}
                          onChange={(e) => setEditForm((f) => ({ ...f, principal_amount: e.target.value }))}
                          className={`${inputClass} text-right`}
                        />
                      </td>
                      <td className="hidden sm:table-cell px-4 py-2">
                        <input
                          type="date"
                          value={editForm.default_date}
                          onChange={(e) => setEditForm((f) => ({ ...f, default_date: e.target.value }))}
                          className={inputClass}
                        />
                      </td>
                      <td className="hidden md:table-cell px-4 py-2" />
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={handleUpdate}
                            disabled={updateClaim.isPending}
                            className="rounded p-1 text-primary hover:bg-primary/10 transition-colors"
                            title="Opslaan"
                          >
                            <Save className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="rounded p-1 text-muted-foreground hover:bg-muted transition-colors"
                            title="Annuleren"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                }

                return (
                  <tr
                    key={claim.id}
                    className="hover:bg-muted/30 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <p className="text-sm font-medium text-foreground">
                        {claim.description}
                      </p>
                      {claim.invoice_number && (
                        <p className="text-xs text-muted-foreground">
                          Factuur: {claim.invoice_number}
                        </p>
                      )}
                      {claim.invoice_file_id && caseFiles && (() => {
                        const linkedFile = caseFiles.find((f) => f.id === claim.invoice_file_id);
                        return linkedFile ? (
                          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                            <FileText className="h-3 w-3" />
                            {linkedFile.original_filename}
                          </p>
                        ) : null;
                      })()}
                    </td>
                    <td className="px-4 py-3 text-right text-sm font-semibold text-foreground tabular-nums">
                      {formatCurrency(claim.principal_amount)}
                    </td>
                    <td className="hidden sm:table-cell px-4 py-3 text-sm text-muted-foreground">
                      {formatDateShort(claim.default_date)}
                    </td>
                    <td className="hidden md:table-cell px-4 py-3 text-right text-sm text-accent font-medium tabular-nums">
                      {claimInterest
                        ? formatCurrency(claimInterest.total_interest)
                        : "-"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => startEdit(claim)}
                          className="rounded p-1 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
                          title="Bewerken"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(claim.id)}
                          className="rounded p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                          title="Verwijderen"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
            {interest && (
              <tfoot>
                <tr className="border-t-2 border-border bg-muted/20">
                  <td className="px-4 py-3 text-sm font-bold text-foreground">
                    Totaal
                  </td>
                  <td className="px-4 py-3 text-right text-sm font-bold text-foreground tabular-nums">
                    {formatCurrency(interest.total_principal)}
                  </td>
                  <td className="hidden sm:table-cell px-4 py-3" />
                  <td className="hidden md:table-cell px-4 py-3 text-right text-sm font-bold text-accent tabular-nums">
                    {formatCurrency(interest.total_interest)}
                  </td>
                  <td className="px-4 py-3" />
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <Euro className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">
            Nog geen vorderingen
          </p>
          <button
            onClick={() => setShowForm(true)}
            className="mt-2 text-sm text-primary hover:underline"
          >
            Voeg de eerste vordering toe
          </button>
        </div>
      )}
    </div>
  );
}

// ── Betalingen Tab ────────────────────────────────────────────────────────────

export function BetalingenTab({ caseId }: { caseId: string }) {
  const { data: payments, isLoading } = usePayments(caseId);
  const createPayment = useCreatePayment();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    amount: "",
    payment_date: new Date().toISOString().split("T")[0],
    description: "",
    payment_method: "",
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createPayment.mutateAsync({
        caseId,
        data: {
          amount: parseFloat(form.amount),
          payment_date: form.payment_date,
          ...(form.description && { description: form.description }),
          ...(form.payment_method && { payment_method: form.payment_method }),
        },
      });
      toast.success("Betaling geregistreerd");
      setShowForm(false);
      setForm({
        amount: "",
        payment_date: new Date().toISOString().split("T")[0],
        description: "",
        payment_method: "",
      });
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">Betalingen</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          Betaling registreren
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-3"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-foreground">
                Bedrag *
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={form.amount}
                onChange={(e) =>
                  setForm((f) => ({ ...f, amount: e.target.value }))
                }
                className={inputClass}
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Datum *
              </label>
              <input
                type="date"
                required
                value={form.payment_date}
                onChange={(e) =>
                  setForm((f) => ({ ...f, payment_date: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Omschrijving
              </label>
              <input
                type="text"
                value={form.description}
                onChange={(e) =>
                  setForm((f) => ({ ...f, description: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Betaalwijze
              </label>
              <select
                value={form.payment_method}
                onChange={(e) =>
                  setForm((f) => ({ ...f, payment_method: e.target.value }))
                }
                className={inputClass}
              >
                <option value="">-</option>
                <option value="bank">Bankoverschrijving</option>
                <option value="cash">Contant</option>
                <option value="derdengelden">Via derdengelden</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createPayment.isPending}
              className="rounded-lg bg-primary px-4 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {createPayment.isPending ? "Opslaan..." : "Registreren"}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-medium hover:bg-muted"
            >
              Annuleren
            </button>
          </div>
        </form>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg skeleton" />
          ))}
        </div>
      ) : payments && payments.length > 0 ? (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Datum
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Bedrag
                </th>
                <th className="hidden sm:table-cell px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Omschrijving
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Kosten
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Rente
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Hoofdsom
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {payments.map((payment) => (
                <tr
                  key={payment.id}
                  className="hover:bg-muted/30 transition-colors"
                >
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {formatDateShort(payment.payment_date)}
                  </td>
                  <td className="px-4 py-3 text-right text-sm font-semibold text-emerald-600 tabular-nums">
                    {formatCurrency(payment.amount)}
                  </td>
                  <td className="hidden sm:table-cell px-4 py-3 text-sm text-muted-foreground">
                    {payment.description || "-"}
                  </td>
                  <td className="hidden md:table-cell px-4 py-3 text-right text-xs text-muted-foreground tabular-nums">
                    {formatCurrency(payment.allocated_to_costs)}
                  </td>
                  <td className="hidden md:table-cell px-4 py-3 text-right text-xs text-muted-foreground tabular-nums">
                    {formatCurrency(payment.allocated_to_interest)}
                  </td>
                  <td className="hidden md:table-cell px-4 py-3 text-right text-xs text-muted-foreground tabular-nums">
                    {formatCurrency(payment.allocated_to_principal)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="border-t border-border bg-muted/20 px-4 py-2.5 text-xs text-muted-foreground">
            Art. 6:44 BW — Betalingen worden automatisch verdeeld: eerst kosten,
            dan rente, dan hoofdsom
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <Receipt className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">
            Nog geen betalingen
          </p>
        </div>
      )}
    </div>
  );
}

// ── Financieel Tab ────────────────────────────────────────────────────────────

export function FinancieelTab({ caseId }: { caseId: string }) {
  const { data: summary, isLoading } = useFinancialSummary(caseId);
  const { data: caseData } = useCase(caseId);
  const updateCase = useUpdateCase();
  const [bikOverride, setBikOverride] = useState<string>("");
  const [bikManual, setBikManual] = useState(false);
  const [bikSaved, setBikSaved] = useState(false);

  // Initialize from persisted bik_override
  useEffect(() => {
    if (caseData?.bik_override != null) {
      setBikManual(true);
      setBikOverride(String(caseData.bik_override));
      setBikSaved(true);
    }
  }, [caseData?.bik_override]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-28 rounded-xl skeleton" />
          ))}
        </div>
        <div className="h-6 rounded-lg skeleton" />
        <div className="h-48 rounded-xl skeleton" />
      </div>
    );
  }

  if (!summary) return null;

  const bikOverrideAmount = bikManual && bikOverride !== "" ? parseFloat(bikOverride) : null;
  const effectiveBik = bikOverrideAmount !== null && !isNaN(bikOverrideAmount) ? bikOverrideAmount : summary.total_bik;
  const bikDiff = effectiveBik - summary.total_bik;
  const effectiveGrandTotal = summary.grand_total + bikDiff;
  const effectiveOutstanding = summary.total_outstanding + bikDiff;
  const effectiveRemainingCosts = summary.remaining_costs + bikDiff;

  const paidPercent = effectiveGrandTotal > 0
    ? Math.min(100, Math.round((summary.total_paid / effectiveGrandTotal) * 100))
    : 0;

  const rows = [
    { label: "Hoofdsom", total: summary.total_principal, paid: summary.total_paid_principal, open: summary.remaining_principal },
    { label: "Rente", total: summary.total_interest, paid: summary.total_paid_interest, open: summary.remaining_interest },
    {
      label: bikOverrideAmount !== null && !isNaN(bikOverrideAmount)
        ? "Incassokosten (handmatig)"
        : summary.bik_btw > 0 ? "BIK incl. BTW" : "BIK (art. 6:96 BW)",
      total: effectiveBik,
      paid: summary.total_paid_costs,
      open: effectiveRemainingCosts,
    },
  ];

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-muted-foreground mb-1">
            <Receipt className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Totale vordering</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-foreground">
            {formatCurrency(effectiveGrandTotal)}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Hoofdsom + rente + kosten
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-emerald-600 mb-1">
            <CheckCircle2 className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Betaald</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-emerald-600">
            {formatCurrency(summary.total_paid)}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {paidPercent}% van totaal
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-amber-600 mb-1">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Openstaand</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-amber-600">
            {formatCurrency(effectiveOutstanding)}
          </p>
          {summary.derdengelden_balance > 0 && (
            <p className="text-xs text-muted-foreground mt-1">
              Derdengelden: {formatCurrency(summary.derdengelden_balance)}
            </p>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-muted-foreground">Betalingsvoortgang</span>
          <span className="text-xs font-semibold text-foreground tabular-nums">{paidPercent}%</span>
        </div>
        <div className="h-2.5 rounded-full bg-muted overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              paidPercent >= 100 ? "bg-emerald-500" : paidPercent >= 50 ? "bg-emerald-500" : "bg-amber-500"
            }`}
            style={{ width: `${paidPercent}%` }}
          />
        </div>
        <div className="flex justify-between mt-1.5">
          <span className="text-[10px] text-emerald-600 tabular-nums">{formatCurrency(summary.total_paid)} betaald</span>
          <span className="text-[10px] text-muted-foreground tabular-nums">{formatCurrency(effectiveGrandTotal)} totaal</span>
        </div>
      </div>

      {/* BIK override */}
      <div className="rounded-xl border border-border bg-card p-5 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Wallet className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Incassokosten</h3>
          </div>
          <div className="flex items-center gap-2">
            {bikManual && !bikSaved && (
              <button
                type="button"
                onClick={async () => {
                  const val = parseFloat(bikOverride);
                  if (isNaN(val) || val < 0) {
                    toast.error("Voer een geldig bedrag in");
                    return;
                  }
                  try {
                    await updateCase.mutateAsync({ id: caseId, data: { bik_override: val } });
                    setBikSaved(true);
                    toast.success("Incassokosten opgeslagen");
                  } catch {
                    toast.error("Opslaan mislukt");
                  }
                }}
                disabled={updateCase.isPending}
                className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
              >
                <Save className="h-3 w-3" />
                Opslaan
              </button>
            )}
            <button
              type="button"
              onClick={async () => {
                if (bikManual) {
                  // Turning off manual mode → clear override on backend
                  try {
                    await updateCase.mutateAsync({ id: caseId, data: { bik_override: null } });
                    setBikManual(false);
                    setBikOverride("");
                    setBikSaved(false);
                    toast.success("Incassokosten teruggezet naar WIK-berekening");
                  } catch {
                    toast.error("Opslaan mislukt");
                  }
                } else {
                  // Turning on manual mode
                  setBikManual(true);
                  setBikOverride(summary.total_bik.toFixed(2));
                  setBikSaved(false);
                }
              }}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                bikManual
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              <Pencil className="h-3 w-3" />
              {bikManual ? "Resetten" : "Aanpassen"}
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex-1">
            <p className="text-xs text-muted-foreground mb-1">
              Berekend (WIK-staffel art. 6:96 BW)
            </p>
            <p className="text-lg font-semibold tabular-nums text-foreground">
              {formatCurrency(summary.total_bik)}
            </p>
            {summary.bik_btw > 0 && (
              <p className="text-xs text-muted-foreground">
                incl. {formatCurrency(summary.bik_btw)} BTW
              </p>
            )}
          </div>

          {bikManual && (
            <div className="flex-1">
              <label className="text-xs text-muted-foreground mb-1 block">
                Handmatig bedrag
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">€</span>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={bikOverride}
                  onChange={(e) => { setBikOverride(e.target.value); setBikSaved(false); }}
                  className="w-full rounded-lg border border-input bg-background pl-7 pr-3 py-2 text-sm font-medium tabular-nums focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                  placeholder={summary.total_bik.toFixed(2)}
                />
              </div>
              {bikOverrideAmount !== null && !isNaN(bikOverrideAmount) && bikDiff !== 0 && (
                <p className={`text-xs mt-1 ${bikDiff > 0 ? "text-amber-600" : "text-emerald-600"}`}>
                  {bikDiff > 0 ? "+" : ""}{formatCurrency(bikDiff)} t.o.v. WIK-berekening
                </p>
              )}
            </div>
          )}
        </div>

        {bikManual && (
          <p className="text-xs text-muted-foreground bg-amber-50 dark:bg-amber-950/20 rounded-lg px-3 py-2 border border-amber-200 dark:border-amber-800">
            Let op: bij een handmatig bedrag is dit technisch geen WIK meer. Het berekende bedrag (WIK-staffel) blijft zichtbaar ter referentie.
          </p>
        )}
      </div>

      {/* Breakdown table */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-2 px-5 py-3.5 border-b border-border bg-muted/30">
          <Euro className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Specificatie</h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Post</th>
              <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Totaal</th>
              <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Betaald</th>
              <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Openstaand</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((row) => {
              const rowPaid = row.total > 0 ? Math.round((row.paid / row.total) * 100) : 0;
              return (
                <tr key={row.label} className="hover:bg-muted/30 transition-colors">
                  <td className="px-5 py-3.5">
                    <p className="text-sm text-foreground">{row.label}</p>
                    <div className="mt-1 h-1 w-20 rounded-full bg-muted overflow-hidden">
                      <div className="h-full rounded-full bg-emerald-500" style={{ width: `${rowPaid}%` }} />
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-right text-sm font-medium tabular-nums">{formatCurrency(row.total)}</td>
                  <td className="px-5 py-3.5 text-right text-sm text-emerald-600 tabular-nums">{formatCurrency(row.paid)}</td>
                  <td className="px-5 py-3.5 text-right text-sm font-medium tabular-nums">
                    {row.open > 0 ? (
                      <span className="text-amber-600">{formatCurrency(row.open)}</span>
                    ) : (
                      <span className="text-emerald-600">{formatCurrency(0)}</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-border bg-muted/30">
              <td className="px-5 py-3.5 text-sm font-bold text-foreground">Totaal</td>
              <td className="px-5 py-3.5 text-right text-sm font-bold text-foreground tabular-nums">{formatCurrency(effectiveGrandTotal)}</td>
              <td className="px-5 py-3.5 text-right text-sm font-bold text-emerald-600 tabular-nums">{formatCurrency(summary.total_paid)}</td>
              <td className="px-5 py-3.5 text-right text-sm font-bold text-amber-600 tabular-nums">{formatCurrency(effectiveOutstanding)}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <p className="text-xs text-muted-foreground">
        Berekening op {formatDate(summary.calculation_date)}. Rente wordt dagelijks bijgewerkt.
      </p>
    </div>
  );
}

// ── Derdengelden Tab ──────────────────────────────────────────────────────────

export function DerdengeldenTab({ caseId }: { caseId: string }) {
  const { data: txData, isLoading } = useDerdengelden(caseId);
  const { data: balance } = useDerdengeldenBalance(caseId);
  const createTx = useCreateDerdengelden();
  const approveTx = useApproveTrustTransaction();
  const rejectTx = useRejectTrustTransaction();
  const [showForm, setShowForm] = useState<"deposit" | "disbursement" | null>(null);
  const [form, setForm] = useState({
    amount: "",
    description: "",
    payment_method: "",
    reference: "",
    beneficiary_name: "",
    beneficiary_iban: "",
  });

  const transactions = txData?.items || [];

  const resetForm = () => {
    setForm({ amount: "", description: "", payment_method: "", reference: "", beneficiary_name: "", beneficiary_iban: "" });
    setShowForm(null);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showForm) return;
    try {
      await createTx.mutateAsync({
        caseId,
        data: {
          transaction_type: showForm,
          amount: parseFloat(form.amount),
          description: form.description,
          ...(form.payment_method && { payment_method: form.payment_method }),
          ...(form.reference && { reference: form.reference }),
          ...(showForm === "disbursement" && form.beneficiary_name && { beneficiary_name: form.beneficiary_name }),
          ...(showForm === "disbursement" && form.beneficiary_iban && { beneficiary_iban: form.beneficiary_iban }),
        },
      });
      toast.success(showForm === "deposit" ? "Storting geregistreerd" : "Uitbetaling ingediend ter goedkeuring");
      resetForm();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleApprove = async (txId: string) => {
    try {
      await approveTx.mutateAsync({ transactionId: txId, caseId });
      toast.success("Transactie goedgekeurd");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleReject = async (txId: string) => {
    try {
      await rejectTx.mutateAsync({ transactionId: txId, caseId });
      toast.success("Transactie afgewezen");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  const STATUS_BADGE: Record<string, { label: string; className: string }> = {
    approved: { label: "Goedgekeurd", className: "bg-emerald-50 text-emerald-700 ring-emerald-600/20" },
    pending_approval: { label: "Wacht op goedkeuring", className: "bg-amber-50 text-amber-700 ring-amber-600/20" },
    rejected: { label: "Afgewezen", className: "bg-red-50 text-red-700 ring-red-600/20" },
  };

  const pendingCount = transactions.filter((t) => t.status === "pending_approval").length;

  return (
    <div className="space-y-6">
      {/* Balance cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-muted-foreground mb-1">
            <Wallet className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Totaal saldo</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-foreground">
            {balance ? formatCurrency(balance.total_balance) : "\u20AC 0,00"}
          </p>
          {balance && balance.total_deposits > 0 && (
            <p className="text-xs text-muted-foreground mt-1">
              {formatCurrency(balance.total_deposits)} ontvangen — {formatCurrency(balance.total_disbursements)} uitbetaald
            </p>
          )}
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-muted-foreground mb-1">
            <Clock className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wider">In afwachting</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-amber-600">
            {balance ? formatCurrency(balance.pending_disbursements) : "\u20AC 0,00"}
          </p>
          {pendingCount > 0 && (
            <p className="text-xs text-amber-600 mt-1">
              {pendingCount} transactie{pendingCount > 1 ? "s" : ""} wacht{pendingCount === 1 ? "" : "en"} op goedkeuring
            </p>
          )}
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-muted-foreground mb-1">
            <CheckCircle2 className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Beschikbaar</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-emerald-600">
            {balance ? formatCurrency(balance.available) : "\u20AC 0,00"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">Saldo minus openstaande uitbetalingen</p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setShowForm(showForm === "deposit" ? null : "deposit")}
          className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 transition-colors"
        >
          <ArrowDownLeft className="h-3.5 w-3.5" />
          Storting
        </button>
        <button
          onClick={() => setShowForm(showForm === "disbursement" ? null : "disbursement")}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <ArrowUpRight className="h-3.5 w-3.5" />
          Uitbetaling
        </button>
      </div>

      {/* Transaction form */}
      {showForm && (
        <form
          onSubmit={handleCreate}
          className={`rounded-xl border p-5 space-y-3 ${
            showForm === "deposit"
              ? "border-emerald-200 bg-emerald-50/50"
              : "border-primary/20 bg-primary/5"
          }`}
        >
          <h3 className="text-sm font-semibold text-foreground">
            {showForm === "deposit" ? "Storting registreren" : "Uitbetaling indienen"}
          </h3>
          {showForm === "disbursement" && (
            <div className="flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-200 p-3">
              <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
              <p className="text-xs text-amber-800">
                Uitbetalingen vereisen goedkeuring van twee directeuren (vier-ogenprincipe).
              </p>
            </div>
          )}
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-foreground">Bedrag *</label>
              <div className="relative mt-1.5">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">&euro;</span>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  value={form.amount}
                  onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
                  className="w-full rounded-lg border border-input bg-background pl-7 pr-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                  placeholder="0,00"
                />
              </div>
              {showForm === "disbursement" && balance && parseFloat(form.amount || "0") > balance.available && (
                <p className="text-xs text-red-600 mt-1">Onvoldoende beschikbaar saldo</p>
              )}
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">Omschrijving *</label>
              <input
                type="text"
                required
                minLength={3}
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                className={inputClass}
                placeholder="Bijv. Storting advocaatkosten"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">Betalingsmethode</label>
              <select
                value={form.payment_method}
                onChange={(e) => setForm((f) => ({ ...f, payment_method: e.target.value }))}
                className={inputClass}
              >
                <option value="">— Kies —</option>
                <option value="bank">Bankoverschrijving</option>
                <option value="ideal">iDEAL</option>
                <option value="cash">Contant</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">Referentie</label>
              <input
                type="text"
                value={form.reference}
                onChange={(e) => setForm((f) => ({ ...f, reference: e.target.value }))}
                className={inputClass}
                placeholder="Bankreferentie / kenmerk"
              />
            </div>
            {showForm === "disbursement" && (
              <>
                <div>
                  <label className="block text-xs font-medium text-foreground">Begunstigde</label>
                  <input
                    type="text"
                    value={form.beneficiary_name}
                    onChange={(e) => setForm((f) => ({ ...f, beneficiary_name: e.target.value }))}
                    className={inputClass}
                    placeholder="Naam ontvanger"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-foreground">IBAN begunstigde</label>
                  <input
                    type="text"
                    value={form.beneficiary_iban}
                    onChange={(e) => setForm((f) => ({ ...f, beneficiary_iban: e.target.value }))}
                    className={inputClass}
                    placeholder="NL00 BANK 0000 0000 00"
                  />
                </div>
              </>
            )}
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createTx.isPending}
              className={`rounded-lg px-4 py-2 text-xs font-medium text-white disabled:opacity-50 transition-colors ${
                showForm === "deposit" ? "bg-emerald-600 hover:bg-emerald-700" : "bg-primary hover:bg-primary/90"
              }`}
            >
              {createTx.isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : showForm === "deposit" ? (
                "Storting registreren"
              ) : (
                "Uitbetaling indienen"
              )}
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="rounded-lg border border-border px-4 py-2 text-xs font-medium hover:bg-muted transition-colors"
            >
              Annuleren
            </button>
          </div>
        </form>
      )}

      {/* Transaction list */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg skeleton" />
          ))}
        </div>
      ) : transactions.length > 0 ? (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Datum
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Type
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Bedrag
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Omschrijving
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Status
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Acties
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {transactions.map((tx) => {
                const badge = STATUS_BADGE[tx.status] || STATUS_BADGE.pending_approval;
                const isDeposit = tx.transaction_type === "deposit";
                return (
                  <tr key={tx.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 text-sm text-muted-foreground whitespace-nowrap">
                      {formatDateShort(tx.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
                          isDeposit
                            ? "bg-emerald-50 text-emerald-700 ring-emerald-600/20"
                            : "bg-blue-50 text-blue-700 ring-blue-600/20"
                        }`}
                      >
                        {isDeposit ? (
                          <ArrowDownLeft className="h-3 w-3" />
                        ) : (
                          <ArrowUpRight className="h-3 w-3" />
                        )}
                        {isDeposit ? "Storting" : "Uitbetaling"}
                      </span>
                    </td>
                    <td
                      className={`px-4 py-3 text-right text-sm font-semibold tabular-nums ${
                        isDeposit ? "text-emerald-600" : "text-foreground"
                      }`}
                    >
                      {isDeposit ? "+" : "-"}
                      {formatCurrency(tx.amount)}
                    </td>
                    <td className="hidden md:table-cell px-4 py-3">
                      <p className="text-sm text-foreground truncate max-w-[200px]" title={tx.description}>
                        {tx.description}
                      </p>
                      {tx.beneficiary_name && (
                        <p className="text-xs text-muted-foreground">&rarr; {tx.beneficiary_name}</p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${badge.className}`}
                      >
                        {badge.label}
                      </span>
                      {tx.status === "pending_approval" && tx.approved_by_1 && !tx.approved_by_2 && (
                        <p className="text-[10px] text-muted-foreground mt-0.5">
                          1/2 goedgekeurd{tx.approver_1 ? ` door ${tx.approver_1.full_name}` : ""}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {tx.status === "pending_approval" && (
                        <div className="inline-flex items-center gap-1">
                          <button
                            onClick={() => handleApprove(tx.id)}
                            disabled={approveTx.isPending}
                            className="inline-flex items-center gap-1 rounded-md bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-200 transition-colors disabled:opacity-50"
                            title="Goedkeuren"
                          >
                            <ShieldCheck className="h-3 w-3" />
                            <span className="hidden lg:inline">Goedkeuren</span>
                          </button>
                          <button
                            onClick={() => handleReject(tx.id)}
                            disabled={rejectTx.isPending}
                            className="inline-flex items-center gap-1 rounded-md bg-red-100 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-200 transition-colors disabled:opacity-50"
                            title="Afwijzen"
                          >
                            <Ban className="h-3 w-3" />
                          </button>
                        </div>
                      )}
                      {tx.status === "approved" && (
                        <span className="text-xs text-emerald-600">
                          <CheckCircle2 className="h-3.5 w-3.5 inline" />
                        </span>
                      )}
                      {tx.status === "rejected" && (
                        <span className="text-xs text-red-500">
                          <XCircle className="h-3.5 w-3.5 inline" />
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <Wallet className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">
            Geen derdengelden transacties
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Registreer een storting of uitbetaling hierboven
          </p>
        </div>
      )}
    </div>
  );
}

// ── Betalingsregeling Section (LF-15) ────────────────────────────────────────

const FREQUENCY_LABELS: Record<string, string> = {
  weekly: "Wekelijks",
  monthly: "Maandelijks",
  quarterly: "Per kwartaal",
};

const FREQUENCY_DAYS: Record<string, number> = {
  weekly: 7,
  monthly: 30,
  quarterly: 91,
};

const STATUS_LABELS: Record<string, string> = {
  active: "Actief",
  completed: "Afgerond",
  defaulted: "Wanprestatie",
  cancelled: "Geannuleerd",
};

const INSTALLMENT_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  paid: { bg: "bg-emerald-100", text: "text-emerald-700", label: "Betaald" },
  partial: { bg: "bg-blue-100", text: "text-blue-700", label: "Deels betaald" },
  pending: { bg: "bg-amber-100", text: "text-amber-700", label: "Open" },
  overdue: { bg: "bg-orange-100", text: "text-orange-700", label: "Achterstallig" },
  missed: { bg: "bg-red-100", text: "text-red-700", label: "Gemist" },
  waived: { bg: "bg-gray-100", text: "text-gray-500", label: "Kwijtgescholden" },
};

function computePreview(totalAmount: number, installmentAmount: number, frequency: string, startDate: string) {
  if (!totalAmount || !installmentAmount || !startDate || installmentAmount <= 0) return null;
  const count = Math.ceil(totalAmount / installmentAmount);
  const days = FREQUENCY_DAYS[frequency] || 30;
  const start = new Date(startDate);
  const endMs = start.getTime() + (count - 1) * days * 86400000;
  const end = new Date(endMs);
  return { count, endDate: end };
}

export function BetalingsregelingSection({ caseId }: { caseId: string }) {
  const { data: arrangements, isLoading } = useArrangements(caseId);
  const { data: financial } = useFinancialSummary(caseId);
  const createArrangement = useCreateArrangement();
  const recordPayment = useRecordInstallmentPayment();
  const defaultArrangement = useDefaultArrangement();
  const cancelArrangement = useCancelArrangement();
  const waiveInstallment = useWaiveInstallment();

  const [showCreate, setShowCreate] = useState(false);
  const [showPayment, setShowPayment] = useState<{ arrangementId: string; installment: Installment } | null>(null);
  const [actionsOpen, setActionsOpen] = useState<string | null>(null);

  // Create form state
  const [form, setForm] = useState({
    total_amount: "",
    installment_amount: "",
    num_installments: "",
    frequency: "monthly",
    start_date: "",
    notes: "",
  });

  // Payment form state
  const [payForm, setPayForm] = useState({
    amount: "",
    payment_date: new Date().toISOString().split("T")[0],
    payment_method: "",
    notes: "",
  });

  const activeArrangement = arrangements?.find((a) => a.status === "active");
  const historicalArrangements = arrangements?.filter((a) => a.status !== "active") || [];

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createArrangement.mutateAsync({
        caseId,
        data: {
          total_amount: parseFloat(form.total_amount),
          installment_amount: parseFloat(form.installment_amount),
          frequency: form.frequency,
          start_date: form.start_date,
          ...(form.notes && { notes: form.notes }),
        },
      });
      toast.success("Betalingsregeling aangemaakt");
      setShowCreate(false);
      setForm({ total_amount: "", installment_amount: "", num_installments: "", frequency: "monthly", start_date: "", notes: "" });
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showPayment) return;
    try {
      await recordPayment.mutateAsync({
        caseId,
        arrangementId: showPayment.arrangementId,
        installmentId: showPayment.installment.id,
        data: {
          amount: parseFloat(payForm.amount),
          payment_date: payForm.payment_date,
          ...(payForm.payment_method && { payment_method: payForm.payment_method }),
          ...(payForm.notes && { notes: payForm.notes }),
        },
      });
      toast.success("Betaling geregistreerd");
      setShowPayment(null);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleDefault = async (arrangementId: string) => {
    if (!confirm("Wanprestatie constateren? Alle openstaande termijnen worden als gemist gemarkeerd.")) return;
    try {
      await defaultArrangement.mutateAsync({ caseId, arrangementId });
      toast.success("Wanprestatie geconstateerd");
      setActionsOpen(null);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleCancel = async (arrangementId: string) => {
    if (!confirm("Betalingsregeling annuleren? Alle openstaande termijnen worden kwijtgescholden.")) return;
    try {
      await cancelArrangement.mutateAsync({ caseId, arrangementId });
      toast.success("Betalingsregeling geannuleerd");
      setActionsOpen(null);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleWaive = async (arrangementId: string, installmentId: string) => {
    if (!confirm("Termijn kwijtschelden?")) return;
    try {
      await waiveInstallment.mutateAsync({ caseId, arrangementId, installmentId });
      toast.success("Termijn kwijtgescholden");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const preview = computePreview(
    parseFloat(form.total_amount) || 0,
    parseFloat(form.installment_amount) || 0,
    form.frequency,
    form.start_date
  );

  if (isLoading) {
    return (
      <div className="py-12 text-center">
        <Loader2 className="mx-auto h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">Betalingsregeling</h3>
        </div>
        {!activeArrangement && !showCreate && (
          <button
            onClick={() => {
              setForm({
                total_amount: financial?.total_outstanding?.toString() || "",
                installment_amount: "",
                num_installments: "",
                frequency: "monthly",
                start_date: new Date().toISOString().split("T")[0],
                notes: "",
              });
              setShowCreate(true);
            }}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Betalingsregeling instellen
          </button>
        )}
      </div>

      {/* Create Dialog */}
      {showCreate && (
        <form onSubmit={handleCreate} className="rounded-xl border border-border bg-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-medium">Nieuwe betalingsregeling</h4>
            <button type="button" onClick={() => setShowCreate(false)} className="text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium">Totaalbedrag</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                value={form.total_amount}
                onChange={(e) => {
                  const total = e.target.value;
                  const numInst = parseInt(form.num_installments) || 0;
                  const autoAmount = numInst > 0 && parseFloat(total) > 0
                    ? (parseFloat(total) / numInst).toFixed(2)
                    : form.installment_amount;
                  setForm({ ...form, total_amount: total, installment_amount: autoAmount });
                }}
                placeholder="0,00"
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Aantal termijnen</label>
              <input
                type="number"
                step="1"
                min="1"
                value={form.num_installments}
                onChange={(e) => {
                  const num = e.target.value;
                  const total = parseFloat(form.total_amount) || 0;
                  const count = parseInt(num) || 0;
                  const autoAmount = count > 0 && total > 0
                    ? (total / count).toFixed(2)
                    : form.installment_amount;
                  setForm({ ...form, num_installments: num, installment_amount: autoAmount });
                }}
                placeholder="Bijv. 6"
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Termijnbedrag</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                required
                value={form.installment_amount}
                onChange={(e) => setForm({ ...form, installment_amount: e.target.value })}
                placeholder="0,00"
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
              />
              {form.num_installments && parseFloat(form.total_amount) > 0 && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Auto-berekend op basis van {form.num_installments} termijnen
                </p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Frequentie</label>
              <select
                value={form.frequency}
                onChange={(e) => setForm({ ...form, frequency: e.target.value })}
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="weekly">Wekelijks</option>
                <option value="monthly">Maandelijks</option>
                <option value="quarterly">Per kwartaal</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Startdatum</label>
              <input
                type="date"
                required
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Notities</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              placeholder="Optionele notities..."
              rows={2}
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm resize-none"
            />
          </div>

          {/* Live Preview */}
          {preview && (
            <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3">
              <p className="text-sm text-blue-800">
                <span className="font-medium">{preview.count} termijnen</span>
                {" van "}
                {formatCurrency(parseFloat(form.installment_amount))}
                {", einddatum: "}
                <span className="font-medium">{formatDate(preview.endDate)}</span>
              </p>
            </div>
          )}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowCreate(false)}
              className="rounded-lg border border-input px-4 py-2 text-sm font-medium hover:bg-accent transition-colors"
            >
              Annuleren
            </button>
            <button
              type="submit"
              disabled={createArrangement.isPending}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {createArrangement.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Aanmaken
            </button>
          </div>
        </form>
      )}

      {/* Active Arrangement */}
      {activeArrangement && (
        <ArrangementCard
          arrangement={activeArrangement}
          caseId={caseId}
          onRecordPayment={(inst) => {
            setPayForm({
              amount: inst.amount.toString(),
              payment_date: new Date().toISOString().split("T")[0],
              payment_method: "",
              notes: "",
            });
            setShowPayment({ arrangementId: activeArrangement.id, installment: inst });
          }}
          onDefault={() => handleDefault(activeArrangement.id)}
          onCancel={() => handleCancel(activeArrangement.id)}
          onWaive={(instId) => handleWaive(activeArrangement.id, instId)}
          actionsOpen={actionsOpen === activeArrangement.id}
          onToggleActions={() => setActionsOpen(actionsOpen === activeArrangement.id ? null : activeArrangement.id)}
        />
      )}

      {/* Empty state */}
      {!activeArrangement && !showCreate && historicalArrangements.length === 0 && (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <Calendar className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">Geen betalingsregeling</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Stel een betalingsregeling in om termijnbetalingen te volgen
          </p>
        </div>
      )}

      {/* Historical Arrangements */}
      {historicalArrangements.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-muted-foreground">Eerdere regelingen</h4>
          {historicalArrangements.map((arr) => (
            <ArrangementCard
              key={arr.id}
              arrangement={arr}
              caseId={caseId}
              onRecordPayment={() => {}}
              onDefault={() => {}}
              onCancel={() => {}}
              onWaive={() => {}}
              actionsOpen={false}
              onToggleActions={() => {}}
              collapsed
            />
          ))}
        </div>
      )}

      {/* Record Payment Dialog (overlay) */}
      {showPayment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowPayment(null)}>
          <form
            onSubmit={handleRecordPayment}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md rounded-xl bg-card border border-border p-6 shadow-lg space-y-4"
          >
            <div className="flex items-center justify-between">
              <h4 className="font-medium">
                Betaling registreren — Termijn {showPayment.installment.installment_number}
              </h4>
              <button type="button" onClick={() => setShowPayment(null)} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="grid gap-4">
              <div>
                <label className="mb-1 block text-sm font-medium">Bedrag</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  value={payForm.amount}
                  onChange={(e) => setPayForm({ ...payForm, amount: e.target.value })}
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Datum</label>
                <input
                  type="date"
                  required
                  value={payForm.payment_date}
                  onChange={(e) => setPayForm({ ...payForm, payment_date: e.target.value })}
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Betaalmethode</label>
                <select
                  value={payForm.payment_method}
                  onChange={(e) => setPayForm({ ...payForm, payment_method: e.target.value })}
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="">— Kies —</option>
                  <option value="bank">Bankoverschrijving</option>
                  <option value="ideal">iDEAL</option>
                  <option value="cash">Contant</option>
                  <option value="other">Anders</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Notities</label>
                <textarea
                  value={payForm.notes}
                  onChange={(e) => setPayForm({ ...payForm, notes: e.target.value })}
                  placeholder="Optioneel..."
                  rows={2}
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm resize-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowPayment(null)}
                className="rounded-lg border border-input px-4 py-2 text-sm font-medium hover:bg-accent transition-colors"
              >
                Annuleren
              </button>
              <button
                type="submit"
                disabled={recordPayment.isPending}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {recordPayment.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Registreren
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function ArrangementCard({
  arrangement,
  caseId,
  onRecordPayment,
  onDefault,
  onCancel,
  onWaive,
  actionsOpen,
  onToggleActions,
  collapsed = false,
}: {
  arrangement: ArrangementWithInstallments;
  caseId: string;
  onRecordPayment: (inst: Installment) => void;
  onDefault: () => void;
  onCancel: () => void;
  onWaive: (instId: string) => void;
  actionsOpen: boolean;
  onToggleActions: () => void;
  collapsed?: boolean;
}) {
  const [isExpanded, setIsExpanded] = useState(!collapsed);
  const totalInstallments = arrangement.installments.length;
  const paidCount = arrangement.paid_count;
  const progressPct = totalInstallments > 0 ? (paidCount / totalInstallments) * 100 : 0;

  const statusColor: Record<string, string> = {
    active: "bg-emerald-100 text-emerald-700",
    completed: "bg-blue-100 text-blue-700",
    defaulted: "bg-red-100 text-red-700",
    cancelled: "bg-gray-100 text-gray-500",
  };

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-accent/50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${isExpanded ? "" : "-rotate-90"}`} />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium">
                {formatCurrency(arrangement.total_amount)}
              </span>
              <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusColor[arrangement.status] || ""}`}>
                {STATUS_LABELS[arrangement.status]}
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              {FREQUENCY_LABELS[arrangement.frequency]} · {totalInstallments} termijnen ·
              Start {formatDateShort(arrangement.start_date)}
              {arrangement.end_date && ` · Eind ${formatDateShort(arrangement.end_date)}`}
            </p>
          </div>
        </div>

        {arrangement.status === "active" && (
          <div className="relative" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={onToggleActions}
              className="rounded-lg p-2 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
            >
              <MoreHorizontal className="h-4 w-4" />
            </button>
            {actionsOpen && (
              <div className="absolute right-0 top-10 z-10 w-52 rounded-lg border border-border bg-card shadow-lg py-1">
                <button
                  onClick={onDefault}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                >
                  <AlertTriangle className="h-4 w-4" />
                  Wanprestatie constateren
                </button>
                <button
                  onClick={onCancel}
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:bg-accent transition-colors"
                >
                  <Ban className="h-4 w-4" />
                  Annuleren
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {isExpanded && (
        <div className="border-t border-border px-5 py-4 space-y-4">
          {/* Progress */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">
                {paidCount}/{totalInstallments} termijnen betaald
              </span>
              <span className="font-medium">
                {formatCurrency(arrangement.total_paid_amount)} / {formatCurrency(arrangement.total_amount)}
              </span>
            </div>
            <div className="h-2 rounded-full bg-muted overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  arrangement.status === "defaulted" ? "bg-red-500" :
                  arrangement.status === "completed" ? "bg-emerald-500" :
                  "bg-primary"
                }`}
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>

          {/* Installments Table */}
          <div className="rounded-lg border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">#</th>
                  <th className="px-3 py-2 text-left font-medium text-muted-foreground">Vervaldatum</th>
                  <th className="px-3 py-2 text-right font-medium text-muted-foreground">Bedrag</th>
                  <th className="px-3 py-2 text-right font-medium text-muted-foreground">Betaald</th>
                  <th className="px-3 py-2 text-center font-medium text-muted-foreground">Status</th>
                  {arrangement.status === "active" && (
                    <th className="px-3 py-2 text-right font-medium text-muted-foreground">Actie</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {arrangement.installments.map((inst) => {
                  const style = INSTALLMENT_STYLES[inst.status] || INSTALLMENT_STYLES.pending;
                  return (
                    <tr key={inst.id} className="border-b border-border last:border-0 hover:bg-accent/30 transition-colors">
                      <td className="px-3 py-2 text-muted-foreground">{inst.installment_number}</td>
                      <td className="px-3 py-2">{formatDateShort(inst.due_date)}</td>
                      <td className="px-3 py-2 text-right font-medium">{formatCurrency(inst.amount)}</td>
                      <td className="px-3 py-2 text-right">
                        {inst.paid_amount > 0 ? formatCurrency(inst.paid_amount) : "—"}
                      </td>
                      <td className="px-3 py-2 text-center">
                        <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${style.bg} ${style.text}`}>
                          {style.label}
                        </span>
                      </td>
                      {arrangement.status === "active" && (
                        <td className="px-3 py-2 text-right">
                          {(inst.status === "pending" || inst.status === "overdue" || inst.status === "partial") && (
                            <div className="flex items-center justify-end gap-1">
                              <button
                                onClick={() => onRecordPayment(inst)}
                                className="inline-flex items-center gap-1 rounded-md bg-primary/10 px-2 py-1 text-xs font-medium text-primary hover:bg-primary/20 transition-colors"
                              >
                                <Euro className="h-3 w-3" />
                                Registreer
                              </button>
                              <button
                                onClick={() => onWaive(inst.id)}
                                className="rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
                                title="Kwijtschelden"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </div>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Notes */}
          {arrangement.notes && (
            <p className="text-xs text-muted-foreground italic">{arrangement.notes}</p>
          )}
        </div>
      )}
    </div>
  );
}

// ── LF-20: Provisie-instellingen ────────────────────────────────────────────

function ProvisieSettingsSection({ caseId }: { caseId: string }) {
  const { data: zaak } = useCase(caseId);
  const updateCase = useUpdateCase();
  const { data: provisie } = useProvisie(caseId);
  const [editing, setEditing] = useState(false);
  const [provPerc, setProvPerc] = useState(
    zaak?.provisie_percentage?.toString() || ""
  );
  const [fixedCosts, setFixedCosts] = useState(
    zaak?.fixed_case_costs?.toString() || ""
  );
  const [minFee, setMinFee] = useState(
    zaak?.minimum_fee?.toString() || ""
  );

  // Sync state when zaak data changes
  const zaakRef = useRef(zaak);
  if (zaak && zaak !== zaakRef.current) {
    zaakRef.current = zaak;
    if (!editing) {
      setProvPerc(zaak.provisie_percentage?.toString() || "");
      setFixedCosts(zaak.fixed_case_costs?.toString() || "");
      setMinFee(zaak.minimum_fee?.toString() || "");
    }
  }

  const handleSave = async () => {
    try {
      await updateCase.mutateAsync({
        id: caseId,
        data: {
          provisie_percentage: parseFloat(provPerc) || null,
          fixed_case_costs: parseFloat(fixedCosts) || null,
          minimum_fee: parseFloat(minFee) || null,
        },
      });
      toast.success("Provisie-instellingen opgeslagen");
      setEditing(false);
    } catch (err: any) {
      toast.error(err.message || "Opslaan mislukt");
    }
  };

  const inputClass =
    "w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
          <Euro className="h-5 w-5 text-primary" />
          Facturatie-instellingen
        </h2>
        {!editing && (
          <button
            onClick={() => setEditing(true)}
            className="text-xs font-medium text-primary hover:text-primary/80 transition-colors"
          >
            Wijzigen
          </button>
        )}
      </div>

      {editing ? (
        <div className="rounded-xl border border-primary/20 bg-card p-5 space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Provisiepercentage (%)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={provPerc}
                onChange={(e) => setProvPerc(e.target.value)}
                placeholder="bijv. 15"
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Vaste dossierkosten (€)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={fixedCosts}
                onChange={(e) => setFixedCosts(e.target.value)}
                placeholder="0.00"
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Minimumkosten (€)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={minFee}
                onChange={(e) => setMinFee(e.target.value)}
                placeholder="0.00"
                className={inputClass}
              />
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={updateCase.isPending}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {updateCase.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Opslaan
            </button>
            <button
              onClick={() => {
                setEditing(false);
                setProvPerc(zaak?.provisie_percentage?.toString() || "");
                setFixedCosts(zaak?.fixed_case_costs?.toString() || "");
                setMinFee(zaak?.minimum_fee?.toString() || "");
              }}
              className="rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-muted transition-colors"
            >
              Annuleren
            </button>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card p-5">
          <dl className="grid grid-cols-3 gap-4">
            <div>
              <dt className="text-xs text-muted-foreground">Provisie</dt>
              <dd className="text-sm font-medium text-foreground mt-0.5">
                {zaak?.provisie_percentage != null ? `${zaak.provisie_percentage}%` : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Vaste dossierkosten</dt>
              <dd className="text-sm font-medium text-foreground mt-0.5">
                {zaak?.fixed_case_costs != null ? formatCurrency(zaak.fixed_case_costs) : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Minimumkosten</dt>
              <dd className="text-sm font-medium text-foreground mt-0.5">
                {zaak?.minimum_fee != null ? formatCurrency(zaak.minimum_fee) : "—"}
              </dd>
            </div>
          </dl>

          {/* Berekend provisie bedrag */}
          {provisie && provisie.collected_amount > 0 && (
            <div className="mt-4 pt-4 border-t border-border">
              <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">
                Berekend honorarium
              </p>
              <dl className="grid grid-cols-2 gap-3">
                <div>
                  <dt className="text-xs text-muted-foreground">Geïnd bedrag</dt>
                  <dd className="text-sm font-medium text-foreground">
                    {formatCurrency(provisie.collected_amount)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Provisie ({provisie.provisie_percentage}%)</dt>
                  <dd className="text-sm font-medium text-foreground">
                    {formatCurrency(provisie.provisie_amount)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Dossierkosten</dt>
                  <dd className="text-sm font-medium text-foreground">
                    {formatCurrency(provisie.fixed_case_costs)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground font-semibold">Totaal honorarium</dt>
                  <dd className="text-sm font-bold text-primary">
                    {formatCurrency(provisie.total_fee)}
                  </dd>
                </div>
              </dl>
              {provisie.minimum_fee > 0 && provisie.total_fee <= provisie.minimum_fee && (
                <p className="mt-2 text-xs text-amber-600">
                  Minimumkosten van {formatCurrency(provisie.minimum_fee)} zijn van toepassing
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Combined: Vorderingen + Financieel (LF-13) ──────────────────────────────

export function VorderingenFinancieelTab({ caseId }: { caseId: string }) {
  return (
    <div className="space-y-8">
      <VorderingenTab caseId={caseId} />
      <div className="border-t border-border" />
      <FinancieelTab caseId={caseId} />
      <div className="border-t border-border" />
      <ProvisieSettingsSection caseId={caseId} />
    </div>
  );
}

// ── Combined: Betalingen + Derdengelden (LF-14) ─────────────────────────────

export function BetalingenDerdengeldenTab({ caseId }: { caseId: string }) {
  return (
    <div className="space-y-8">
      <BetalingenTab caseId={caseId} />
      <div className="border-t border-border" />
      <BetalingsregelingSection caseId={caseId} />
      <div className="border-t border-border" />
      <DerdengeldenTab caseId={caseId} />
    </div>
  );
}
