"use client";

import { useState } from "react";
import {
  AlertTriangle,
  Ban,
  Calendar,
  ChevronDown,
  Euro,
  Loader2,
  MoreHorizontal,
  Plus,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { useConfirm } from "@/components/confirm-dialog";
import {
  useArrangements,
  useCreateArrangement,
  useRecordInstallmentPayment,
  useDefaultArrangement,
  useCancelArrangement,
  useWaiveInstallment,
  useFinancialSummary,
} from "@/hooks/use-collections";
import type { Installment, ArrangementWithInstallments } from "@/hooks/use-collections";
import { formatCurrency, formatDate, formatDateShort } from "@/lib/utils";

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
  const { confirm, ConfirmDialog: ConfirmDialogEl } = useConfirm();

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
          total_amount: form.total_amount,
          installment_amount: form.installment_amount,
          frequency: form.frequency,
          start_date: form.start_date,
          ...(form.notes && { notes: form.notes }),
        },
      });
      toast.success("Betalingsregeling aangemaakt");
      setShowCreate(false);
      setForm({ total_amount: "", installment_amount: "", num_installments: "", frequency: "monthly", start_date: "", notes: "" });
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Er ging iets mis");
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
          amount: payForm.amount,
          payment_date: payForm.payment_date,
          ...(payForm.payment_method && { payment_method: payForm.payment_method }),
          ...(payForm.notes && { notes: payForm.notes }),
        },
      });
      toast.success("Betaling geregistreerd");
      setShowPayment(null);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Er ging iets mis");
    }
  };

  const handleDefault = async (arrangementId: string) => {
    if (!await confirm({ title: "Wanprestatie constateren", description: "Alle openstaande termijnen worden als gemist gemarkeerd.", variant: "destructive", confirmText: "Bevestigen" })) return;
    try {
      await defaultArrangement.mutateAsync({ caseId, arrangementId });
      toast.success("Wanprestatie geconstateerd");
      setActionsOpen(null);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Er ging iets mis");
    }
  };

  const handleCancel = async (arrangementId: string) => {
    if (!await confirm({ title: "Betalingsregeling annuleren", description: "Alle openstaande termijnen worden kwijtgescholden.", variant: "destructive", confirmText: "Annuleren" })) return;
    try {
      await cancelArrangement.mutateAsync({ caseId, arrangementId });
      toast.success("Betalingsregeling geannuleerd");
      setActionsOpen(null);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Er ging iets mis");
    }
  };

  const handleWaive = async (arrangementId: string, installmentId: string) => {
    if (!await confirm({ title: "Termijn kwijtschelden", description: "Weet je zeker dat je deze termijn wilt kwijtschelden?", variant: "destructive", confirmText: "Kwijtschelden" })) return;
    try {
      await waiveInstallment.mutateAsync({ caseId, arrangementId, installmentId });
      toast.success("Termijn kwijtgescholden");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Er ging iets mis");
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
      {ConfirmDialogEl}
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
                  setForm({ ...form, total_amount: e.target.value });
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
                  setForm({ ...form, num_installments: e.target.value });
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
