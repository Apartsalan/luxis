"use client";

import { useState } from "react";
import { useUnsavedWarning } from "@/hooks/use-unsaved-warning";
import { Loader2, Plus, Receipt } from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { toast } from "sonner";
import { usePayments, useCreatePayment } from "@/hooks/use-collections";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import { QueryError } from "@/components/query-error";

export function BetalingenTab({ caseId }: { caseId: string }) {
  const { data: payments, isLoading, isError, error, refetch } = usePayments(caseId);
  const createPayment = useCreatePayment();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    amount: "",
    payment_date: new Date().toISOString().split("T")[0],
    description: "",
    payment_method: "",
  });
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useUnsavedWarning(showForm && (!!form.amount || !!form.description));

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const errors: Record<string, string> = {};
    const amount = parseFloat(form.amount);
    if (!form.amount || isNaN(amount) || amount <= 0) {
      errors.amount = "Voer een geldig bedrag in";
    }
    if (!form.payment_date) {
      errors.payment_date = "Datum is verplicht";
    }
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }
    try {
      await createPayment.mutateAsync({
        caseId,
        data: {
          amount: form.amount,
          payment_date: form.payment_date,
          ...(form.description && { description: form.description }),
          ...(form.payment_method && { payment_method: form.payment_method }),
        },
      });
      toast.success("Betaling geregistreerd");
      setShowForm(false);
      setFieldErrors({});
      setForm({
        amount: "",
        payment_date: new Date().toISOString().split("T")[0],
        description: "",
        payment_method: "",
      });
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Er ging iets mis");
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
                onChange={(e) => {
                  setForm((f) => ({ ...f, amount: e.target.value }));
                  if (fieldErrors.amount) setFieldErrors((p) => { const n = { ...p }; delete n.amount; return n; });
                }}
                className={`${inputClass} ${fieldErrors.amount ? "border-destructive ring-1 ring-destructive/30" : ""}`}
                placeholder="0.00"
              />
              {fieldErrors.amount && (
                <p className="mt-1 text-xs text-destructive">{fieldErrors.amount}</p>
              )}
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Datum *
              </label>
              <input
                type="date"
                required
                value={form.payment_date}
                onChange={(e) => {
                  setForm((f) => ({ ...f, payment_date: e.target.value }));
                  if (fieldErrors.payment_date) setFieldErrors((p) => { const n = { ...p }; delete n.payment_date; return n; });
                }}
                className={`${inputClass} ${fieldErrors.payment_date ? "border-destructive ring-1 ring-destructive/30" : ""}`}
              />
              {fieldErrors.payment_date && (
                <p className="mt-1 text-xs text-destructive">{fieldErrors.payment_date}</p>
              )}
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
      ) : isError ? (
        <QueryError message={error?.message} onRetry={refetch} />
      ) : payments && payments.length > 0 ? (
        <div className="rounded-xl border border-border bg-card overflow-x-auto">
          <table className="w-full min-w-[500px]">
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
        <EmptyState
          icon={Receipt}
          title="Nog geen betalingen"
          description="Betalingen worden hier getoond zodra ze zijn geregistreerd of automatisch gematcht via bankafschriften."
          action={{ label: "Betaling registreren", onClick: () => setShowForm(true) }}
        />
      )}
    </div>
  );
}
