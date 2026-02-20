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
  CreditCard,
  Wallet,
  ArrowDownLeft,
  ReceiptText,
  ExternalLink,
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
  useInvoicePayments,
  useInvoicePaymentSummary,
  useCreateInvoicePayment,
  useDeleteInvoicePayment,
  useCreateCreditNote,
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
  sent: [],
  partially_paid: [],
};

export default function FactuurDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const { data: factuur, isLoading, isError, error, refetch } = useInvoice(id);
  const { data: payments } = useInvoicePayments(id);
  const { data: paymentSummary } = useInvoicePaymentSummary(id);

  // Mutations
  const updateInvoice = useUpdateInvoice();
  const deleteInvoice = useDeleteInvoice();
  const approveMutation = useApproveInvoice();
  const sendMutation = useSendInvoice();
  const markPaidMutation = useMarkInvoicePaid();
  const cancelMutation = useCancelInvoice();
  const addLineMutation = useAddInvoiceLine();
  const removeLineMutation = useRemoveInvoiceLine();
  const createPayment = useCreateInvoicePayment();
  const deletePayment = useDeleteInvoicePayment();
  const createCreditNote = useCreateCreditNote();

  // Credit note form
  const [showCreditNoteForm, setShowCreditNoteForm] = useState(false);
  const [cnLines, setCnLines] = useState<{ description: string; quantity: string; unit_price: string }[]>([]);

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

  // Payment form
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [payAmount, setPayAmount] = useState("");
  const [payDate, setPayDate] = useState(new Date().toISOString().split("T")[0]);
  const [payMethod, setPayMethod] = useState("bank");
  const [payReference, setPayReference] = useState("");
  const [payDescription, setPayDescription] = useState("");

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

  const handleAddPayment = async () => {
    if (!payAmount || parseFloat(payAmount) <= 0) {
      toast.error("Vul een geldig bedrag in");
      return;
    }
    try {
      await createPayment.mutateAsync({
        invoiceId: id,
        data: {
          amount: parseFloat(payAmount),
          payment_date: payDate,
          payment_method: payMethod,
          ...(payReference && { reference: payReference }),
          ...(payDescription && { description: payDescription }),
        },
      });
      toast.success("Betaling geregistreerd");
      setShowPaymentForm(false);
      setPayAmount("");
      setPayDate(new Date().toISOString().split("T")[0]);
      setPayMethod("bank");
      setPayReference("");
      setPayDescription("");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleDeletePayment = async (paymentId: string) => {
    if (!confirm("Weet je zeker dat je deze betaling wilt verwijderen?")) return;
    try {
      await deletePayment.mutateAsync({ invoiceId: id, paymentId });
      toast.success("Betaling verwijderd");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  // ── Credit note handlers ───────────────────────────────────────────

  const startCreditNote = () => {
    if (!factuur) return;
    // Pre-fill lines from original invoice
    setCnLines(
      factuur.lines.map((l) => ({
        description: l.description,
        quantity: String(l.quantity),
        unit_price: String(l.unit_price),
      }))
    );
    setShowCreditNoteForm(true);
  };

  const handleCreateCreditNote = async () => {
    if (!factuur) return;
    const lines = cnLines
      .filter((l) => l.description && l.unit_price)
      .map((l) => ({
        description: l.description,
        quantity: parseFloat(l.quantity) || 1,
        unit_price: parseFloat(l.unit_price),
      }));
    if (lines.length === 0) {
      toast.error("Voeg minstens één regel toe");
      return;
    }
    try {
      const result = await createCreditNote.mutateAsync({
        linked_invoice_id: factuur.id,
        invoice_date: new Date().toISOString().split("T")[0],
        due_date: new Date().toISOString().split("T")[0],
        btw_percentage: factuur.btw_percentage,
        lines,
      });
      toast.success("Credit nota aangemaakt");
      setShowCreditNoteForm(false);
      router.push(`/facturen/${result.id}`);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const addCnLine = () => {
    setCnLines([...cnLines, { description: "", quantity: "1", unit_price: "" }]);
  };

  const removeCnLine = (idx: number) => {
    setCnLines(cnLines.filter((_, i) => i !== idx));
  };

  const updateCnLine = (idx: number, field: string, value: string) => {
    setCnLines(cnLines.map((l, i) => (i === idx ? { ...l, [field]: value } : l)));
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
  const isCreditNote = factuur.invoice_type === "credit_note";
  const canCreateCreditNote =
    !isCreditNote &&
    !["concept", "cancelled"].includes(factuur.status) &&
    factuur.lines.length > 0;

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
              {isCreditNote && (
                <span className="inline-flex items-center gap-1 rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-700">
                  <ReceiptText className="h-3 w-3" />
                  Credit nota
                </span>
              )}
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
              {isCreditNote && factuur.linked_invoice_id && (
                <>
                  {" · "}
                  <Link
                    href={`/facturen/${factuur.linked_invoice_id}`}
                    className="text-primary hover:underline inline-flex items-center gap-0.5"
                  >
                    Originele factuur <ExternalLink className="h-3 w-3" />
                  </Link>
                </>
              )}
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
      {(actions.length > 0 || canCancel || canCreateCreditNote) && !editing && (
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
          {canCreateCreditNote && (
            <button
              onClick={startCreditNote}
              className="inline-flex items-center gap-2 rounded-lg border border-purple-200 bg-purple-50 px-4 py-2.5 text-sm font-medium text-purple-700 hover:bg-purple-100 transition-colors"
            >
              <ReceiptText className="h-4 w-4" />
              Credit nota
            </button>
          )}
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
            Dossier
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

      {/* Credit note creation form */}
      {showCreditNoteForm && (
        <div className="rounded-xl border-2 border-purple-200 bg-purple-50/30 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3 border-b border-purple-200 bg-purple-50">
            <div className="flex items-center gap-2">
              <ReceiptText className="h-4 w-4 text-purple-600" />
              <h3 className="text-sm font-semibold text-purple-900">
                Credit nota aanmaken
              </h3>
            </div>
            <button
              onClick={() => setShowCreditNoteForm(false)}
              className="rounded-lg p-1.5 text-purple-400 hover:bg-purple-100 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="px-5 py-4 space-y-3">
            <p className="text-xs text-muted-foreground">
              De regels zijn overgenomen van de originele factuur. Pas bedragen aan indien nodig (bijv. voor een gedeeltelijke credit nota).
            </p>

            {/* Lines */}
            <div className="space-y-2">
              {cnLines.map((line, idx) => (
                <div
                  key={idx}
                  className="grid grid-cols-[1fr_80px_120px_auto] gap-2 items-end"
                >
                  <div>
                    {idx === 0 && (
                      <label className="block text-xs font-medium text-muted-foreground mb-1">
                        Omschrijving
                      </label>
                    )}
                    <input
                      type="text"
                      value={line.description}
                      onChange={(e) =>
                        updateCnLine(idx, "description", e.target.value)
                      }
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    />
                  </div>
                  <div>
                    {idx === 0 && (
                      <label className="block text-xs font-medium text-muted-foreground mb-1">
                        Aantal
                      </label>
                    )}
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={line.quantity}
                      onChange={(e) =>
                        updateCnLine(idx, "quantity", e.target.value)
                      }
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    />
                  </div>
                  <div>
                    {idx === 0 && (
                      <label className="block text-xs font-medium text-muted-foreground mb-1">
                        Prijs
                      </label>
                    )}
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={line.unit_price}
                      onChange={(e) =>
                        updateCnLine(idx, "unit_price", e.target.value)
                      }
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    />
                  </div>
                  <button
                    onClick={() => removeCnLine(idx)}
                    className="rounded-md border border-border p-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                    title="Verwijderen"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>

            <button
              onClick={addCnLine}
              className="inline-flex items-center gap-1 text-xs font-medium text-purple-600 hover:text-purple-800 transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
              Regel toevoegen
            </button>
          </div>

          <div className="flex items-center gap-2 px-5 py-3 border-t border-purple-200 bg-purple-50/50">
            <button
              onClick={handleCreateCreditNote}
              disabled={createCreditNote.isPending}
              className="inline-flex items-center gap-2 rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 transition-colors disabled:opacity-50"
            >
              {createCreditNote.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ReceiptText className="h-4 w-4" />
              )}
              Credit nota aanmaken
            </button>
            <button
              onClick={() => setShowCreditNoteForm(false)}
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted transition-colors"
            >
              Annuleren
            </button>
          </div>
        </div>
      )}

      {/* Linked credit notes */}
      {!isCreditNote && factuur.credit_notes && factuur.credit_notes.length > 0 && (
        <div className="rounded-xl border border-purple-200 bg-card shadow-sm overflow-hidden">
          <div className="flex items-center gap-2 px-5 py-3 border-b border-purple-100 bg-purple-50/50">
            <ReceiptText className="h-4 w-4 text-purple-600" />
            <h3 className="text-sm font-semibold text-foreground">
              Credit nota&apos;s ({factuur.credit_notes.length})
            </h3>
          </div>
          <div className="divide-y divide-border">
            {factuur.credit_notes.map((cn) => (
              <Link
                key={cn.id}
                href={`/facturen/${cn.id}`}
                className="flex items-center justify-between px-5 py-3 hover:bg-muted/40 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-mono font-semibold text-purple-700">
                    {cn.invoice_number}
                  </span>
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      INVOICE_STATUS_COLORS[cn.status] ?? "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {INVOICE_STATUS_LABELS[cn.status] ?? cn.status}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {formatDateShort(cn.invoice_date)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-red-600 tabular-nums">
                    -{formatCurrency(cn.total)}
                  </span>
                  <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Payment tracking section — only for sent/partially_paid/paid invoices */}
      {factuur && ["sent", "partially_paid", "paid"].includes(factuur.status) && (
        <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3 border-b border-border">
            <div className="flex items-center gap-2">
              <CreditCard className="h-4 w-4 text-muted-foreground" />
              <h3 className="text-sm font-semibold text-foreground">
                Betalingen
              </h3>
              {paymentSummary && (
                <span className="text-xs text-muted-foreground">
                  ({paymentSummary.payment_count} betaling{paymentSummary.payment_count !== 1 ? "en" : ""})
                </span>
              )}
            </div>
            {!paymentSummary?.is_fully_paid && (
              <button
                onClick={() => setShowPaymentForm(!showPaymentForm)}
                className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 transition-colors"
              >
                <ArrowDownLeft className="h-3.5 w-3.5" />
                Betaling registreren
              </button>
            )}
          </div>

          {/* Payment summary bar */}
          {paymentSummary && (
            <div className="px-5 py-3 border-b border-border bg-muted/20">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-medium text-muted-foreground">
                  {paymentSummary.is_fully_paid ? "Volledig betaald" : "Betalingsvoortgang"}
                </span>
                <span className="text-xs font-semibold text-foreground tabular-nums">
                  {formatCurrency(paymentSummary.total_paid)} / {formatCurrency(paymentSummary.invoice_total)}
                </span>
              </div>
              <div className="h-2 rounded-full bg-muted overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    paymentSummary.is_fully_paid ? "bg-emerald-500" : "bg-amber-500"
                  }`}
                  style={{ width: `${Math.min(100, paymentSummary.invoice_total > 0 ? (paymentSummary.total_paid / paymentSummary.invoice_total) * 100 : 0)}%` }}
                />
              </div>
              {paymentSummary.outstanding > 0 && (
                <p className="text-xs text-amber-600 mt-1 tabular-nums">
                  Nog openstaand: {formatCurrency(paymentSummary.outstanding)}
                </p>
              )}
            </div>
          )}

          {/* Payment form */}
          {showPaymentForm && (
            <div className="border-b border-border bg-emerald-50/50 px-5 py-4">
              <h4 className="text-sm font-semibold text-foreground mb-3">Betaling registreren</h4>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                <div>
                  <label className="block text-xs font-medium text-foreground mb-1">Bedrag *</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">€</span>
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      value={payAmount}
                      onChange={(e) => setPayAmount(e.target.value)}
                      placeholder={paymentSummary ? String(paymentSummary.outstanding) : "0,00"}
                      className="w-full rounded-md border border-input bg-background pl-7 pr-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-foreground mb-1">Datum *</label>
                  <input
                    type="date"
                    value={payDate}
                    onChange={(e) => setPayDate(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-foreground mb-1">Methode *</label>
                  <select
                    value={payMethod}
                    onChange={(e) => setPayMethod(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  >
                    <option value="bank">Bankoverschrijving</option>
                    <option value="ideal">iDEAL</option>
                    <option value="cash">Contant</option>
                    <option value="verrekening">Verrekening</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-foreground mb-1">Referentie</label>
                  <input
                    type="text"
                    value={payReference}
                    onChange={(e) => setPayReference(e.target.value)}
                    placeholder="Bankreferentie"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>
                <div className="sm:col-span-2 lg:col-span-2">
                  <label className="block text-xs font-medium text-foreground mb-1">Omschrijving</label>
                  <input
                    type="text"
                    value={payDescription}
                    onChange={(e) => setPayDescription(e.target.value)}
                    placeholder="Optioneel"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                </div>
              </div>
              <div className="flex gap-2 mt-3">
                <button
                  onClick={handleAddPayment}
                  disabled={createPayment.isPending}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-medium text-white hover:bg-emerald-700 transition-colors disabled:opacity-50"
                >
                  {createPayment.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <ArrowDownLeft className="h-3.5 w-3.5" />
                  )}
                  Betaling registreren
                </button>
                <button
                  onClick={() => setShowPaymentForm(false)}
                  className="rounded-lg border border-border px-4 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors"
                >
                  Annuleren
                </button>
              </div>
            </div>
          )}

          {/* Payment list */}
          {payments && payments.length > 0 ? (
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/30">
                  <th className="px-5 py-2.5 text-left text-xs font-medium text-muted-foreground">Datum</th>
                  <th className="px-5 py-2.5 text-right text-xs font-medium text-muted-foreground">Bedrag</th>
                  <th className="px-5 py-2.5 text-left text-xs font-medium text-muted-foreground">Methode</th>
                  <th className="hidden sm:table-cell px-5 py-2.5 text-left text-xs font-medium text-muted-foreground">Referentie</th>
                  <th className="px-5 py-2.5 w-10" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {payments.map((payment) => (
                  <tr key={payment.id} className="group hover:bg-muted/30 transition-colors">
                    <td className="px-5 py-3 text-sm text-muted-foreground">
                      {formatDateShort(payment.payment_date)}
                    </td>
                    <td className="px-5 py-3 text-right text-sm font-semibold text-emerald-600 tabular-nums">
                      +{formatCurrency(payment.amount)}
                    </td>
                    <td className="px-5 py-3">
                      <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                        {{ bank: "Bank", ideal: "iDEAL", cash: "Contant", verrekening: "Verrekening" }[payment.payment_method] || payment.payment_method}
                      </span>
                    </td>
                    <td className="hidden sm:table-cell px-5 py-3 text-sm text-muted-foreground">
                      {payment.reference || "-"}
                    </td>
                    <td className="px-5 py-3">
                      <button
                        onClick={() => handleDeletePayment(payment.id)}
                        disabled={deletePayment.isPending}
                        className="rounded p-1 text-muted-foreground opacity-0 group-hover:opacity-100 hover:bg-destructive/10 hover:text-destructive transition-all disabled:opacity-50"
                        title="Verwijderen"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="px-5 py-8 text-center">
              <Wallet className="mx-auto h-8 w-8 text-muted-foreground/30" />
              <p className="mt-2 text-sm text-muted-foreground">Nog geen betalingen geregistreerd</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
