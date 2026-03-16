"use client";

import { useState } from "react";
import {
  AlertTriangle,
  ArrowDownLeft,
  ArrowUpRight,
  Ban,
  CheckCircle2,
  Clock,
  Euro,
  Loader2,
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
} from "@/hooks/use-collections";
import { formatCurrency, formatDate, formatDateShort } from "@/lib/utils";

// ── Vorderingen Tab ──────────────────────────────────────────────────────────

export function VorderingenTab({ caseId }: { caseId: string }) {
  const { data: claims, isLoading } = useClaims(caseId);
  const { data: interest } = useCaseInterest(caseId);
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
  });
  const [form, setForm] = useState({
    description: "",
    principal_amount: "",
    default_date: "",
    invoice_number: "",
    invoice_date: "",
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

  const startEdit = (claim: { id: string; description: string; principal_amount: number; default_date: string; invoice_number: string | null; invoice_date: string | null }) => {
    setEditingId(claim.id);
    setEditForm({
      description: claim.description,
      principal_amount: String(claim.principal_amount),
      default_date: claim.default_date,
      invoice_number: claim.invoice_number || "",
      invoice_date: claim.invoice_date || "",
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
  const [bikOverride, setBikOverride] = useState<string>("");
  const [bikManual, setBikManual] = useState(false);

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
          <button
            type="button"
            onClick={() => {
              setBikManual(!bikManual);
              if (!bikManual) setBikOverride(summary.total_bik.toFixed(2));
            }}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              bikManual
                ? "bg-primary/10 text-primary border border-primary/20"
                : "bg-muted text-muted-foreground hover:bg-muted/80"
            }`}
          >
            <Pencil className="h-3 w-3" />
            {bikManual ? "Handmatig" : "Aanpassen"}
          </button>
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
                  onChange={(e) => setBikOverride(e.target.value)}
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

// ── Combined: Vorderingen + Financieel (LF-13) ──────────────────────────────

export function VorderingenFinancieelTab({ caseId }: { caseId: string }) {
  return (
    <div className="space-y-8">
      <VorderingenTab caseId={caseId} />
      <div className="border-t border-border" />
      <FinancieelTab caseId={caseId} />
    </div>
  );
}

// ── Combined: Betalingen + Derdengelden (LF-14) ─────────────────────────────

export function BetalingenDerdengeldenTab({ caseId }: { caseId: string }) {
  return (
    <div className="space-y-8">
      <BetalingenTab caseId={caseId} />
      <div className="border-t border-border" />
      <DerdengeldenTab caseId={caseId} />
    </div>
  );
}
