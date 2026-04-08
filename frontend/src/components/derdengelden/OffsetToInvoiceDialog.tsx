"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Loader2, Scale, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  useCreateTrustOffset,
  useEligibleInvoicesForOffset,
} from "@/hooks/use-collections";
import { formatCurrency, formatDateShort } from "@/lib/utils";

type ConsentMethod = "email" | "document" | "mondeling" | "anders";

interface Props {
  caseId: string;
  open: boolean;
  onClose: () => void;
  availableBalance: number;
}

export function OffsetToInvoiceDialog({ caseId, open, onClose, availableBalance }: Props) {
  const { data: invoices, isLoading } = useEligibleInvoicesForOffset(open ? caseId : undefined);
  const createOffset = useCreateTrustOffset();

  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string>("");
  const [amount, setAmount] = useState<string>("");
  const [description, setDescription] = useState<string>("");
  const [consentDate, setConsentDate] = useState<string>(
    new Date().toISOString().slice(0, 10),
  );
  const [consentMethod, setConsentMethod] = useState<ConsentMethod>("email");
  const [consentNote, setConsentNote] = useState<string>("");

  const selectedInvoice = useMemo(
    () => invoices?.find((inv) => inv.id === selectedInvoiceId),
    [invoices, selectedInvoiceId],
  );

  // Auto-select first invoice and pre-fill amount
  useEffect(() => {
    if (!open) return;
    if (invoices && invoices.length > 0 && !selectedInvoiceId) {
      const first = invoices[0];
      setSelectedInvoiceId(first.id);
      const max = Math.min(first.outstanding, availableBalance);
      setAmount(max.toFixed(2));
      setDescription(`Verrekening met factuur ${first.invoice_number}`);
    }
  }, [open, invoices, selectedInvoiceId, availableBalance]);

  // When invoice changes, refresh default amount + description
  useEffect(() => {
    if (selectedInvoice) {
      const max = Math.min(selectedInvoice.outstanding, availableBalance);
      setAmount(max.toFixed(2));
      setDescription(`Verrekening met factuur ${selectedInvoice.invoice_number}`);
    }
  }, [selectedInvoiceId, availableBalance]); // eslint-disable-line react-hooks/exhaustive-deps

  const reset = () => {
    setSelectedInvoiceId("");
    setAmount("");
    setDescription("");
    setConsentDate(new Date().toISOString().slice(0, 10));
    setConsentMethod("email");
    setConsentNote("");
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const numericAmount = parseFloat(amount || "0");
  const balanceAfter = availableBalance - numericAmount;
  const invoiceAfter = selectedInvoice ? selectedInvoice.outstanding - numericAmount : 0;

  const validationError = (() => {
    if (!selectedInvoice) return "Kies een factuur";
    if (numericAmount <= 0) return "Bedrag moet groter zijn dan 0";
    if (numericAmount > availableBalance)
      return `Bedrag overschrijdt beschikbaar saldo (€${availableBalance.toFixed(2)})`;
    if (numericAmount > selectedInvoice.outstanding)
      return `Bedrag overschrijdt openstaand factuurbedrag (€${selectedInvoice.outstanding.toFixed(2)})`;
    if (description.trim().length < 3) return "Omschrijving is te kort";
    if (!consentDate) return "Datum toestemming is verplicht";
    if (consentNote.trim().length < 3) return "Toelichting op de toestemming is verplicht";
    return null;
  })();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (validationError || !selectedInvoice) return;
    try {
      await createOffset.mutateAsync({
        caseId,
        data: {
          amount: numericAmount.toFixed(2),
          transaction_date: consentDate,
          description: description.trim(),
          target_invoice_id: selectedInvoice.id,
          consent_received_at: consentDate,
          consent_method: consentMethod,
          consent_note: consentNote.trim(),
        },
      });
      toast.success("Verrekening ingediend ter goedkeuring");
      handleClose();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Er ging iets mis");
    }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => (!o ? handleClose() : null)}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Scale className="h-5 w-5 text-violet-600" />
            Derdengelden verrekenen met factuur
          </DialogTitle>
          <DialogDescription>
            Verreken een deel van het derdengelden-saldo met een openstaande factuur van dezelfde
            cliënt.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : !invoices || invoices.length === 0 ? (
          <div className="rounded-lg border border-dashed py-10 text-center text-sm text-muted-foreground">
            Er zijn geen openstaande facturen voor deze cliënt om mee te verrekenen.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* SECTIE 1: Wat verrekenen */}
            <section className="space-y-3">
              <h3 className="text-sm font-semibold text-foreground">1. Wat verrekenen?</h3>

              <div>
                <label className="block text-xs font-medium text-foreground mb-1.5">
                  Openstaande factuur *
                </label>
                <select
                  value={selectedInvoiceId}
                  onChange={(e) => setSelectedInvoiceId(e.target.value)}
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                >
                  {invoices.map((inv) => (
                    <option key={inv.id} value={inv.id}>
                      {inv.invoice_number} — openstaand €{inv.outstanding.toFixed(2)} (vervaldatum{" "}
                      {formatDateShort(inv.due_date)})
                      {inv.case_number ? ` — dossier ${inv.case_number}` : ""}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-foreground mb-1.5">
                    Te verrekenen bedrag *
                  </label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                      €
                    </span>
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      required
                      value={amount}
                      onChange={(e) => setAmount(e.target.value)}
                      className="w-full rounded-lg border border-input bg-background pl-7 pr-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-foreground mb-1.5">
                    Omschrijving *
                  </label>
                  <input
                    type="text"
                    required
                    minLength={3}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              </div>

              {selectedInvoice && numericAmount > 0 && (
                <div className="rounded-lg bg-violet-50 border border-violet-200 p-3 text-xs space-y-1">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Derdengelden-saldo na verrekening:</span>
                    <span className="font-semibold tabular-nums">
                      {formatCurrency(balanceAfter)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">
                      Openstaand op factuur {selectedInvoice.invoice_number} na verrekening:
                    </span>
                    <span className="font-semibold tabular-nums">
                      {formatCurrency(invoiceAfter)}
                    </span>
                  </div>
                </div>
              )}
            </section>

            {/* SECTIE 2: Toestemming cliënt */}
            <section className="space-y-3">
              <h3 className="text-sm font-semibold text-foreground">2. Toestemming cliënt</h3>

              <div className="flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-200 p-3">
                <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
                <p className="text-xs text-amber-800 leading-relaxed">
                  Verrekening met eigen honorarium vereist <strong>per uitbetaling</strong>{" "}
                  schriftelijke, specifieke en uitdrukkelijke toestemming van de cliënt
                  (Voda art. 6.19 lid 5). Een algemene clausule in de opdrachtbevestiging is{" "}
                  <strong>niet voldoende</strong>. Leg hieronder vast wanneer en hoe de
                  toestemming is ontvangen.
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-foreground mb-1.5">
                    Datum toestemming ontvangen *
                  </label>
                  <input
                    type="date"
                    required
                    value={consentDate}
                    onChange={(e) => setConsentDate(e.target.value)}
                    className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-foreground mb-1.5">
                    Methode *
                  </label>
                  <select
                    required
                    value={consentMethod}
                    onChange={(e) => setConsentMethod(e.target.value as ConsentMethod)}
                    className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  >
                    <option value="email">Per e-mail</option>
                    <option value="document">Ondertekend document</option>
                    <option value="mondeling">Mondeling (bevestigd)</option>
                    <option value="anders">Anders</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-foreground mb-1.5">
                  Toelichting *
                </label>
                <textarea
                  required
                  minLength={3}
                  rows={3}
                  value={consentNote}
                  onChange={(e) => setConsentNote(e.target.value)}
                  placeholder="Bijv. 'Bevestigd per e-mail van Jan Jansen op 7 april 2026' of 'Telefonisch akkoord op 7 april, gemaild ter bevestiging'"
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 resize-y"
                />
              </div>
            </section>

            {validationError && (
              <div className="rounded-lg bg-red-50 border border-red-200 p-2 text-xs text-red-700">
                {validationError}
              </div>
            )}

            <DialogFooter>
              <button
                type="button"
                onClick={handleClose}
                className="rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
              >
                Annuleren
              </button>
              <button
                type="submit"
                disabled={!!validationError || createOffset.isPending}
                className="inline-flex items-center gap-1.5 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {createOffset.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ShieldCheck className="h-4 w-4" />
                )}
                Verrekening indienen
              </button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
