"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  FileText,
  Plus,
  Trash2,
  CheckCircle2,
  Send,
  Ban,
  Euro,
  CalendarDays,
  Pencil,
  Loader2,
  X,
  Briefcase,
  User,
} from "lucide-react";
import { toast } from "sonner";
import {
  useInvoice,
  useUpdateInvoice,
  useDeleteInvoice,
  useApproveInvoice,
  useSendInvoice,
  useMarkInvoicePaid,
  useCancelInvoice,
  useAddInvoiceLine,
  useRemoveInvoiceLine,
  INVOICE_STATUS_LABELS,
  INVOICE_STATUS_COLORS,
} from "@/hooks/use-invoices";
import { formatCurrency, formatDate, formatDateShort } from "@/lib/utils";
import { QueryError } from "@/components/query-error";
import { useBreadcrumbs } from "@/components/layout/breadcrumb-context";

// ── Status transition map ────────────────────────────────────────────────

const STATUS_ACTIONS: Record<
  string,
  { label: string; next: string; icon: typeof CheckCircle2; color: string }[]
> = {
  concept: [
    {
      label: "Goedkeuren",
      next: "approved",
      icon: CheckCircle2,
      color:
        "bg-blue-600 text-white hover:bg-blue-700",
    },
  ],
  approved: [
    {
      label: "Verzenden",
      next: "sent",
      icon: Send,
      color:
        "bg-amber-600 text-white hover:bg-amber-700",
    },
  ],
  sent: [
    {
      label: "Betaald markeren",
      next: "paid",
      icon: Euro,
      color:
        "bg-emerald-600 text-white hover:bg-emerald-700",
    },
  ],
};

export default function FactuurDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const { data: factuur, isLoading, isError, error, refetch } = useInvoice(id);

  // Mutations
  const updateInvoice = useUpdateInvoice();
  const deleteInvoice = useDeleteInvoice();
  const approveMutation = useApproveInvoice();
  const sendMutation = useSendInvoice();
  const markPaidMutation = useMarkInvoicePaid();
  const cancelMutation = useCancelInvoice();
  const addLineMutation = useAddInvoiceLine();
  const removeLineMutation = useRemoveInvoiceLine();

  // Edit mode (only for concept)
  const [editing, setEditing] = useState(false);
  const [editDate, setEditDate] = useState("");
  const [editDueDate, setEditDueDate] = useState("");
  const [editBtw, setEditBtw] = useState("");
  const [editReference, setEditReference] = useState("");
  const [editNotes, setEditNotes] = useState("");

  // Set breadcrumb label to invoice number
  useBreadcrumbs(factuur ? [{ segment: id, label: factuur.invoice_number }] : []);

  // New line form
  const [showLineForm, setShowLineForm] = useState(false);
  const [lineDescription, setLineDescription] = useState("");
  const [lineQuantity, setLineQuantity] = useState("1");
  const [lineUnitPrice, setLineUnitPrice] = useState("");

  // ── Handlers ─────────────────────────────────────────────────────────

  const startEdit = () => {
    if (!factuur) return;
    setEditDate(factuur.invoice_date);
    setEditDueDate(factuur.due_date);
    setEditBtw(String(factuur.btw_percentage));
    setEditReference(factuur.reference ?? "");
    setEditNotes(factuur.notes ?? "");
    setEditing(true);
  };

  const saveEdit = async () => {
    try {
      await updateInvoice.mutateAsync({
        id,
        data: {
          invoice_date: editDate,
          due_date: editDueDate,
          btw_percentage: parseFloat(editBtw),
          reference: editReference || undefined,
          notes: editNotes || undefined,
        },
      });
      toast.success("Factuur bijgewerkt");
      setEditing(false);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Weet je zeker dat je deze factuur wilt verwijderen?")) return;
    try {
      await deleteInvoice.mutateAsync(id);
      toast.success("Factuur verwijderd");
      router.push("/facturen");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleStatusAction = async (next: string) => {
    try {
      if (next === "approved") {
        await approveMutation.mutateAsync(id);
        toast.success("Factuur goedgekeurd");
      } else if (next === "sent") {
        await sendMutation.mutateAsync(id);
        toast.success("Factuur gemarkeerd als verzonden");
      } else if (next === "paid") {
        await markPaidMutation.mutateAsync({ id });
        toast.success("Factuur gemarkeerd als betaald");
      }
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleCancel = async () => {
    if (!confirm("Weet je zeker dat je deze factuur wilt annuleren?")) return;
    try {
      await cancelMutation.mutateAsync(id);
      toast.success("Factuur geannuleerd");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleAddLine = async () => {
    if (!lineDescription || !lineUnitPrice) {
      toast.error("Vul omschrijving en bedrag in");
      return;
    }
    try {
      await addLineMutation.mutateAsync({
        invoiceId: id,
        data: {
          description: lineDescription,
          quantity: parseFloat(lineQuantity) || 1,
          unit_price: parseFloat(lineUnitPrice),
        },
      });
      toast.success("Regel toegevoegd");
      setLineDescription("");
      setLineQuantity("1");
      setLineUnitPrice("");
      setShowLineForm(false);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleRemoveLine = async (lineId: string) => {
    try {
      await removeLineMutation.mutateAsync({ invoiceId: id, lineId });
      toast.success("Regel verwijderd");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  // ── Loading / Error / Not found ────────────────────────────────────

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="h-8 w-48 rounded-md skeleton" />
        <div className="h-14 rounded-xl skeleton" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 rounded-xl skeleton" />
          ))}
        </div>
        <div className="h-64 rounded-xl skeleton" />
      </div>
    );
  }

  if (isError) {
    return <QueryError message={error?.message} onRetry={() => refetch()} />;
  }

  if (!factuur) {
    return (
      <div className="py-20 text-center">
        <FileText className="mx-auto h-12 w-12 text-muted-foreground/30" />
        <p className="mt-4 text-base font-medium text-foreground">
          Factuur niet gevonden
        </p>
        <Link
          href="/facturen"
          className="mt-2 inline-block text-sm text-primary hover:underline"
        >
          &larr; Terug naar facturen
        </Link>
      </div>
    );
  }

  const isConcept = factuur.status === "concept";
  const isMutating =
    approveMutation.isPending ||
    sendMutation.isPending ||
    markPaidMutation.isPending ||
    cancelMutation.isPending;
  const canCancel = !["paid", "cancelled"].includes(factuur.status);
  const actions = STATUS_ACTIONS[factuur.status] ?? [];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <Link
            href="/facturen"
            className="mt-1 rounded-lg p-2 hover:bg-muted transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-muted-foreground" />
          </Link>
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold text-foreground font-mono">
                {factuur.invoice_number}
              </h1>
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  INVOICE_STATUS_COLORS[factuur.status] ??
                  "bg-gray-100 text-gray-700"
                }`}
              >
                {INVOICE_STATUS_LABELS[factuur.status] ?? factuur.status}
              </span>
            </div>
            <p className="text-sm text-muted-foreground mt-0.5">
              Aangemaakt op {formatDate(factuur.created_at)}
              {factuur.paid_date && ` · Betaald op ${formatDate(factuur.paid_date)}`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {isConcept && (
            <button
              onClick={editing ? saveEdit : startEdit}
              disabled={updateInvoice.isPending}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-sm font-medium text-foreground hover:bg-muted transition-colors"
            >
              {editing ? (
                updateInvoice.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Opslaan"
                )
              ) : (
                <>
                  <Pencil className="h-4 w-4" />
                  Bewerken
                </>
              )}
            </button>
          )}
          {editing && (
            <button
              onClick={() => setEditing(false)}
              className="rounded-lg border border-border p-2 text-muted-foreground hover:bg-muted transition-colors"
              title="Annuleren"
            >
              <X className="h-4 w-4" />
            </button>
          )}
          {isConcept && !editing && (
            <button
              onClick={handleDelete}
              className="rounded-lg border border-destructive/20 p-2 text-destructive hover:bg-destructive/10 transition-colors"
              title="Verwijderen"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Status action buttons */}
      {(actions.length > 0 || canCancel) && !editing && (
        <div className="flex items-center gap-2">
          {actions.map((action) => (
            <button
              key={action.next}
              onClick={() => handleStatusAction(action.next)}
              disabled={isMutating}
              className={`inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium shadow-sm transition-colors disabled:opacity-50 ${action.color}`}
            >
              {isMutating ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <action.icon className="h-4 w-4" />
              )}
              {action.label}
            </button>
          ))}
          {canCancel && (
            <button
              onClick={handleCancel}
              disabled={isMutating}
              className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2.5 text-sm font-medium text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
            >
              <Ban className="h-4 w-4" />
              Annuleren
            </button>
          )}
        </div>
      )}

      {/* Info cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Contact */}
        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground mb-2">
            <User className="h-4 w-4" />
            Relatie
          </div>
          {factuur.contact ? (
            <Link
              href={`/relaties/${factuur.contact.id}`}
              className="text-sm font-semibold text-foreground hover:text-primary transition-colors"
            >
              {factuur.contact.name}
            </Link>
          ) : (
            <p className="text-sm text-muted-foreground">-</p>
          )}
        </div>

        {/* Case */}
        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground mb-2">
            <Briefcase className="h-4 w-4" />
            Zaak
          </div>
          {factuur.case ? (
            <Link
              href={`/zaken/${factuur.case.id}`}
              className="text-sm font-semibold text-foreground font-mono hover:text-primary transition-colors"
            >
              {factuur.case.case_number}
            </Link>
          ) : (
            <p className="text-sm text-muted-foreground">-</p>
          )}
        </div>

        {/* Dates */}
        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground mb-2">
            <CalendarDays className="h-4 w-4" />
            Data
          </div>
          {editing ? (
            <div className="space-y-1.5">
              <input
                type="date"
                value={editDate}
                onChange={(e) => setEditDate(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
              />
              <input
                type="date"
                value={editDueDate}
                onChange={(e) => setEditDueDate(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm"
              />
            </div>
          ) : (
            <div className="space-y-0.5">
              <p className="text-sm text-foreground">
                {formatDateShort(factuur.invoice_date)}
              </p>
              <p className="text-xs text-muted-foreground">
                Vervalt {formatDateShort(factuur.due_date)}
              </p>
            </div>
          )}
        </div>

        {/* Total */}
        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground mb-2">
            <Euro className="h-4 w-4" />
            Totaal
          </div>
          <p className="text-xl font-bold text-foreground tabular-nums">
            {formatCurrency(factuur.total)}
          </p>
          <p className="text-xs text-muted-foreground">
            incl. {factuur.btw_percentage}% BTW
          </p>
        </div>
      </div>

      {/* Edit fields for reference/notes/btw */}
      {editing && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-foreground mb-3">
            Factuurgegevens bewerken
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">
                BTW-percentage
              </label>
              <input
                type="number"
                step="0.01"
                value={editBtw}
                onChange={(e) => setEditBtw(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">
                Referentie
              </label>
              <input
                type="text"
                value={editReference}
                onChange={(e) => setEditReference(e.target.value)}
                placeholder="Optioneel"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">
                Notities
              </label>
              <input
                type="text"
                value={editNotes}
                onChange={(e) => setEditNotes(e.target.value)}
                placeholder="Optioneel"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
          </div>
        </div>
      )}

      {/* Reference & Notes display (when not editing) */}
      {!editing && (factuur.reference || factuur.notes) && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          {factuur.reference && (
            <p className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">Referentie:</span>{" "}
              {factuur.reference}
            </p>
          )}
          {factuur.notes && (
            <p className="text-sm text-muted-foreground mt-1">
              <span className="font-medium text-foreground">Notities:</span>{" "}
              {factuur.notes}
            </p>
          )}
        </div>
      )}

      {/* Lines table */}
      <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-foreground">
            Factuurregels ({factuur.lines.length})
          </h3>
          {isConcept && !editing && (
            <button
              onClick={() => setShowLineForm(!showLineForm)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
              Regel toevoegen
            </button>
          )}
        </div>

        {/* Add line form */}
        {showLineForm && (
          <div className="border-b border-border bg-muted/30 px-5 py-3">
            <div className="grid grid-cols-[1fr_80px_120px_auto] gap-2 items-end">
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Omschrijving
                </label>
                <input
                  type="text"
                  value={lineDescription}
                  onChange={(e) => setLineDescription(e.target.value)}
                  placeholder="Omschrijving van de regel"
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Aantal
                </label>
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={lineQuantity}
                  onChange={(e) => setLineQuantity(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Prijs
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={lineUnitPrice}
                  onChange={(e) => setLineUnitPrice(e.target.value)}
                  placeholder="0,00"
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div className="flex gap-1">
                <button
                  onClick={handleAddLine}
                  disabled={addLineMutation.isPending}
                  className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
                >
                  {addLineMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    "Toevoegen"
                  )}
                </button>
                <button
                  onClick={() => setShowLineForm(false)}
                  className="rounded-md border border-border px-2 py-2 text-muted-foreground hover:bg-muted transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Lines */}
        {factuur.lines.length > 0 ? (
          <>
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-5 py-2.5 text-left text-xs font-medium text-muted-foreground w-10">
                    #
                  </th>
                  <th className="px-5 py-2.5 text-left text-xs font-medium text-muted-foreground">
                    Omschrijving
                  </th>
                  <th className="px-5 py-2.5 text-right text-xs font-medium text-muted-foreground w-20">
                    Aantal
                  </th>
                  <th className="px-5 py-2.5 text-right text-xs font-medium text-muted-foreground w-28">
                    Prijs
                  </th>
                  <th className="px-5 py-2.5 text-right text-xs font-medium text-muted-foreground w-28">
                    Totaal
                  </th>
                  {isConcept && !editing && (
                    <th className="px-5 py-2.5 w-10" />
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {factuur.lines.map((line) => (
                  <tr
                    key={line.id}
                    className="group hover:bg-muted/30 transition-colors"
                  >
                    <td className="px-5 py-3 text-sm text-muted-foreground tabular-nums">
                      {line.line_number}
                    </td>
                    <td className="px-5 py-3 text-sm text-foreground">
                      {line.description}
                    </td>
                    <td className="px-5 py-3 text-sm text-foreground text-right tabular-nums">
                      {line.quantity}
                    </td>
                    <td className="px-5 py-3 text-sm text-foreground text-right tabular-nums">
                      {formatCurrency(line.unit_price)}
                    </td>
                    <td className="px-5 py-3 text-sm font-semibold text-foreground text-right tabular-nums">
                      {formatCurrency(line.line_total)}
                    </td>
                    {isConcept && !editing && (
                      <td className="px-5 py-3">
                        <button
                          onClick={() => handleRemoveLine(line.id)}
                          disabled={removeLineMutation.isPending}
                          className="rounded p-1 text-muted-foreground opacity-0 group-hover:opacity-100 hover:bg-destructive/10 hover:text-destructive transition-all disabled:opacity-50"
                          title="Verwijderen"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Totals */}
            <div className="border-t border-border px-5 py-4">
              <div className="flex flex-col items-end gap-1.5">
                <div className="flex items-center justify-between w-56">
                  <span className="text-sm text-muted-foreground">
                    Subtotaal
                  </span>
                  <span className="text-sm font-medium text-foreground tabular-nums">
                    {formatCurrency(factuur.subtotal)}
                  </span>
                </div>
                <div className="flex items-center justify-between w-56">
                  <span className="text-sm text-muted-foreground">
                    BTW ({factuur.btw_percentage}%)
                  </span>
                  <span className="text-sm font-medium text-foreground tabular-nums">
                    {formatCurrency(factuur.btw_amount)}
                  </span>
                </div>
                <div className="flex items-center justify-between w-56 pt-1.5 border-t border-border">
                  <span className="text-sm font-semibold text-foreground">
                    Totaal
                  </span>
                  <span className="text-base font-bold text-foreground tabular-nums">
                    {formatCurrency(factuur.total)}
                  </span>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="px-5 py-12 text-center">
            <FileText className="mx-auto h-8 w-8 text-muted-foreground/30" />
            <p className="mt-2 text-sm text-muted-foreground">
              Nog geen regels
            </p>
            {isConcept && (
              <button
                onClick={() => setShowLineForm(true)}
                className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                <Plus className="h-3.5 w-3.5" />
                Eerste regel toevoegen
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
