"use client";

import { useState } from "react";
import {
  AlertTriangle,
  ArrowDownLeft,
  ArrowUpRight,
  Ban,
  CheckCircle2,
  Clock,
  Loader2,
  ShieldCheck,
  Wallet,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import {
  useDerdengelden,
  useDerdengeldenBalance,
  useCreateDerdengelden,
  useApproveTrustTransaction,
  useRejectTrustTransaction,
} from "@/hooks/use-collections";
import { formatCurrency, formatDateShort } from "@/lib/utils";

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
    } catch {}
  };

  const handleApprove = async (txId: string) => {
    try {
      await approveTx.mutateAsync({ transactionId: txId, caseId });
      toast.success("Transactie goedgekeurd");
    } catch {}
  };

  const handleReject = async (txId: string) => {
    try {
      await rejectTx.mutateAsync({ transactionId: txId, caseId });
      toast.success("Transactie afgewezen");
    } catch {}
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
