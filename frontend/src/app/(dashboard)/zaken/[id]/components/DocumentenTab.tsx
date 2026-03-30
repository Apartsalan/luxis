"use client";

import { useState, useCallback, useEffect } from "react";
import { useConfirm } from "@/components/confirm-dialog";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowRight,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Clock,
  CreditCard,
  Download,
  Eye,
  File,
  FileSpreadsheet,
  FileText,
  Filter,
  Image,
  Loader2,
  Mail,
  Pencil,
  Plus,
  Receipt,
  Save,
  Send,
  Star,
  Trash2,
  Upload,
  X,
  XCircle,
} from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { toast } from "sonner";
import {
  useDocxTemplates,
  useGenerateDocx,
  useCaseDocuments,
  useDeleteDocument,
  useSendDocument,
  getTemplateLabel,
  getTemplateDescription,
  getTemplatesForStatus,
  triggerDownload,
  useSendCaseEmail,
  useEmailLogs,
  type GeneratedDocumentSummary,
} from "@/hooks/use-documents";
import { EmailComposeDialog, type EmailComposeData } from "@/components/email-compose-dialog";
import {
  useInvoices,
  useCreateInvoice,
  useDeleteInvoice,
  INVOICE_STATUS_LABELS,
  INVOICE_STATUS_COLORS,
} from "@/hooks/use-invoices";
import { useUnbilledTimeEntries } from "@/hooks/use-time-entries";
import { useExpenses, useCreateExpense, useDeleteExpense, EXPENSE_CATEGORY_LABELS } from "@/hooks/use-expenses";
import {
  useCaseFiles,
  useUploadCaseFile,
  useDeleteCaseFile,
  useRenameCaseFile,
  downloadCaseFile,
  formatFileSize,
  getFileIcon,
  isPreviewable,
  useCaseEmailAttachments,
  downloadEmailAttachment,
} from "@/hooks/use-case-files";
import { useSaveAttachmentToCase } from "@/hooks/use-email-sync";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import { tokenStore } from "@/lib/token-store";

export function FacturenTab({ caseId, clientId }: { caseId: string; clientId?: string }) {
  const router = useRouter();
  const { data, isLoading } = useInvoices({ case_id: caseId, per_page: 100 });
  const invoices = data?.items ?? [];
  const createInvoice = useCreateInvoice();
  const deleteInvoice = useDeleteInvoice();
  const { confirm: confirmDelete, ConfirmDialog: ConfirmDialogEl1 } = useConfirm();

  // Quick Bill state
  const [showQuickBill, setShowQuickBill] = useState(false);
  const [quickBillStep, setQuickBillStep] = useState<"select" | "preview">("select");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const { data: unbilledEntries, isLoading: entriesLoading } = useUnbilledTimeEntries(caseId);
  const available = unbilledEntries ?? [];

  const toggleEntry = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedIds.size === available.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(available.map((e) => e.id)));
    }
  };

  const selectedEntries = available.filter((e) => selectedIds.has(e.id));
  const selectedSubtotal = selectedEntries.reduce((sum, e) => {
    const hours = e.duration_minutes / 60;
    return sum + hours * (e.hourly_rate ?? 0);
  }, 0);
  const btwAmount = selectedSubtotal * 0.21;
  const selectedTotal = selectedSubtotal + btwAmount;

  const handleQuickBill = async () => {
    if (!clientId || selectedEntries.length === 0) return;
    try {
      const result = await createInvoice.mutateAsync({
        contact_id: clientId,
        case_id: caseId,
        invoice_date: new Date().toISOString().split("T")[0],
        due_date: new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
        btw_percentage: 21,
        lines: selectedEntries.map((e) => ({
          description: e.description || "Juridische werkzaamheden",
          quantity: +(e.duration_minutes / 60).toFixed(2),
          unit_price: e.hourly_rate ?? 0,
          time_entry_id: e.id,
        })),
      });
      toast.success("Factuur aangemaakt");
      setShowQuickBill(false);
      setSelectedIds(new Set());
      setQuickBillStep("select");
      router.push(`/facturen/${result.id}`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Factuur aanmaken mislukt");
    }
  };

  return (
    <div className="space-y-6">
      {ConfirmDialogEl1}
      {/* Quick Bill Dialog */}
      {showQuickBill && (
        <div className="rounded-xl border-2 border-primary/30 bg-card p-6 space-y-4">
          {quickBillStep === "select" ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-foreground">
                    Factureer uren
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    Selecteer onbefactureerde uren om te factureren
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setShowQuickBill(false);
                    setSelectedIds(new Set());
                  }}
                  className="rounded-md p-1 text-muted-foreground hover:text-foreground transition-colors"
                >
                  <XCircle className="h-5 w-5" />
                </button>
              </div>

              {entriesLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : available.length === 0 ? (
                <div className="rounded-lg border border-dashed border-border py-8 text-center">
                  <Clock className="mx-auto h-8 w-8 text-muted-foreground/30" />
                  <p className="mt-2 text-sm text-muted-foreground">
                    Geen onbefactureerde uren voor dit dossier
                  </p>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between">
                    <button
                      type="button"
                      onClick={toggleAll}
                      className="text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                    >
                      {selectedIds.size === available.length ? "Deselecteer alles" : "Alles selecteren"}
                    </button>
                    <span className="text-xs text-muted-foreground">
                      {available.length} uur{available.length !== 1 ? "" : ""} beschikbaar
                    </span>
                  </div>

                  <div className="max-h-80 overflow-y-auto space-y-1 rounded-lg border border-border p-2">
                    {available.map((entry) => {
                      const hours = entry.duration_minutes / 60;
                      const amount = hours * (entry.hourly_rate ?? 0);
                      const isSelected = selectedIds.has(entry.id);

                      return (
                        <label
                          key={entry.id}
                          className={`flex w-full cursor-pointer items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors ${
                            isSelected ? "bg-primary/5 ring-1 ring-primary/20" : "hover:bg-muted"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleEntry(entry.id)}
                            className="h-4 w-4 rounded border-input text-primary focus:ring-primary/20"
                          />
                          <div className="flex flex-1 items-center justify-between min-w-0">
                            <div className="min-w-0 flex-1">
                              <span className="truncate block font-medium">
                                {entry.description || "Werkzaamheden"}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {formatDateShort(entry.date)} · {hours.toFixed(1)}u
                                {entry.user?.full_name && ` · ${entry.user.full_name}`}
                              </span>
                            </div>
                            <span className="ml-3 font-medium tabular-nums">
                              {entry.hourly_rate ? formatCurrency(amount) : "-"}
                            </span>
                          </div>
                        </label>
                      );
                    })}
                  </div>

                  <div className="flex items-center justify-between border-t border-border pt-3">
                    <div className="text-sm text-muted-foreground">
                      {selectedIds.size > 0 ? (
                        <>
                          <span className="font-medium text-foreground">{selectedIds.size}</span>{" "}
                          geselecteerd · subtotaal{" "}
                          <span className="font-medium text-foreground tabular-nums">
                            {formatCurrency(selectedSubtotal)}
                          </span>
                        </>
                      ) : (
                        "Selecteer uren om te factureren"
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => setQuickBillStep("preview")}
                      disabled={selectedIds.size === 0}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      Bekijk factuur
                      <ArrowRight className="h-4 w-4" />
                    </button>
                  </div>
                </>
              )}
            </>
          ) : (
            /* Preview step */
            <>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-foreground">
                    Factuur preview
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    Controleer de factuur voor aanmaak
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setQuickBillStep("select")}
                  className="inline-flex items-center gap-1 text-sm text-primary hover:text-primary/80 transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Terug
                </button>
              </div>

              <div className="rounded-lg border border-border divide-y divide-border">
                <div className="grid grid-cols-12 gap-2 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  <div className="col-span-5">Omschrijving</div>
                  <div className="col-span-2">Datum</div>
                  <div className="col-span-2 text-right">Uren</div>
                  <div className="col-span-3 text-right">Bedrag</div>
                </div>
                {selectedEntries.map((entry) => {
                  const hours = entry.duration_minutes / 60;
                  const amount = hours * (entry.hourly_rate ?? 0);
                  return (
                    <div key={entry.id} className="grid grid-cols-12 gap-2 px-4 py-2.5 text-sm">
                      <div className="col-span-5 truncate">
                        {entry.description || "Juridische werkzaamheden"}
                      </div>
                      <div className="col-span-2 text-muted-foreground">
                        {formatDateShort(entry.date)}
                      </div>
                      <div className="col-span-2 text-right tabular-nums">
                        {hours.toFixed(2)}
                      </div>
                      <div className="col-span-3 text-right font-medium tabular-nums">
                        {formatCurrency(amount)}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="space-y-2 pt-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Subtotaal</span>
                  <span className="font-medium tabular-nums">{formatCurrency(selectedSubtotal)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">BTW (21%)</span>
                  <span className="font-medium tabular-nums">{formatCurrency(btwAmount)}</span>
                </div>
                <div className="flex justify-between text-base font-semibold border-t border-border pt-2">
                  <span>Totaal</span>
                  <span className="tabular-nums">{formatCurrency(selectedTotal)}</span>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowQuickBill(false);
                    setSelectedIds(new Set());
                    setQuickBillStep("select");
                  }}
                  className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-muted transition-colors"
                >
                  Annuleren
                </button>
                <button
                  type="button"
                  onClick={handleQuickBill}
                  disabled={createInvoice.isPending}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-5 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  {createInvoice.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Aanmaken...
                    </>
                  ) : (
                    <>
                      <Receipt className="h-4 w-4" />
                      Factuur aanmaken
                    </>
                  )}
                </button>
              </div>
            </>
          )}
        </div>
      )}

      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-foreground">Facturen</h2>
            <p className="text-sm text-muted-foreground">
              Alle facturen gekoppeld aan dit dossier
            </p>
          </div>
          <div className="flex items-center gap-2">
            {clientId && !showQuickBill && (
              <button
                type="button"
                onClick={() => {
                  setShowQuickBill(true);
                  setQuickBillStep("select");
                  setSelectedIds(new Set());
                }}
                className="inline-flex items-center gap-1.5 rounded-lg border border-primary/30 bg-primary/5 px-3 py-2 text-sm font-medium text-primary hover:bg-primary/10 transition-colors"
              >
                <Clock className="h-4 w-4" />
                Factureer uren
              </button>
            )}
            <Link
              href={`/facturen/nieuw?case_id=${caseId}`}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <Plus className="h-4 w-4" />
              Nieuwe factuur
            </Link>
          </div>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center justify-between rounded-lg border border-border p-4">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-lg skeleton" />
                  <div className="space-y-2">
                    <div className="h-4 w-28 rounded skeleton" />
                    <div className="h-3 w-20 rounded skeleton" />
                  </div>
                </div>
                <div className="h-4 w-20 rounded skeleton" />
              </div>
            ))}
          </div>
        ) : !invoices.length ? (
          <EmptyState
            icon={CreditCard}
            title="Nog geen facturen"
            description="Maak een factuur aan op basis van geregistreerde uren en verschotten."
            action={{ label: "Factuur aanmaken", onClick: () => router.push(`/facturen/nieuw?case_id=${caseId}`) }}
          />
        ) : (
          <div className="space-y-2">
            {invoices.map((inv) => (
              <Link
                key={inv.id}
                href={`/facturen/${inv.id}?from_case=1`}
                className="flex items-center justify-between rounded-lg border border-border p-4 hover:border-primary/30 hover:bg-muted/30 transition-all group"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                    <CreditCard className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground group-hover:text-primary transition-colors">
                      {inv.invoice_number}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDateShort(inv.invoice_date)}
                      {inv.contact_name && ` · ${inv.contact_name}`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                      INVOICE_STATUS_COLORS[inv.status] ?? "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {INVOICE_STATUS_LABELS[inv.status] ?? inv.status}
                  </span>
                  <span className="text-sm font-semibold text-foreground tabular-nums">
                    {formatCurrency(inv.total)}
                  </span>
                  <button
                    type="button"
                    onClick={async (e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      const ok = await confirmDelete({ title: "Factuur verwijderen", description: "Weet je zeker dat je deze factuur wilt verwijderen?", variant: "destructive", confirmText: "Verwijderen" });
                      if (ok) {
                        deleteInvoice.mutate(inv.id, {
                          onSuccess: () => toast.success("Factuur verwijderd"),
                          onError: () => toast.error("Fout bij verwijderen factuur"),
                        });
                      }
                    }}
                    className="rounded-md p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors opacity-0 group-hover:opacity-100"
                    title="Verwijderen"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                  <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </Link>
            ))}
          </div>
        )}

        {invoices.length > 0 && (
          <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
            <p className="text-sm text-muted-foreground">
              {invoices.length} factuur{invoices.length !== 1 ? "en" : ""}
            </p>
            <p className="text-sm font-semibold text-foreground tabular-nums">
              Totaal: {formatCurrency(invoices.reduce((sum, inv) => sum + inv.total, 0))}
            </p>
          </div>
        )}
      </div>

      {/* DF-12: Verschotten sectie */}
      <VerschottenSection caseId={caseId} />
    </div>
  );
}

// ── DF-12: Verschotten Section ──────────────────────────────────────────────

const TAX_TYPE_LABELS: Record<string, string> = {
  belast: "Belast",
  onbelast: "Onbelast",
  vrijgesteld: "Vrijgesteld",
};

function VerschottenSection({ caseId }: { caseId: string }) {
  const { data: expenses, isLoading } = useExpenses({ case_id: caseId });
  const { data: caseFiles } = useCaseFiles(caseId);
  const createExpense = useCreateExpense();
  const deleteExpense = useDeleteExpense();
  const { confirm: confirmDelete, ConfirmDialog: ConfirmDialogEl2 } = useConfirm();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    description: "",
    amount: "",
    expense_date: new Date().toISOString().split("T")[0],
    category: "overig",
    billable: true,
    tax_type: "belast",
    file_id: "",
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createExpense.mutateAsync({
        case_id: caseId,
        description: form.description,
        amount: form.amount,
        expense_date: form.expense_date,
        category: form.category,
        billable: form.billable,
        tax_type: form.tax_type,
        ...(form.file_id && { file_id: form.file_id }),
      });
      toast.success("Verschot toegevoegd");
      setShowForm(false);
      setForm({
        description: "",
        amount: "",
        expense_date: new Date().toISOString().split("T")[0],
        category: "overig",
        billable: true,
        tax_type: "belast",
        file_id: "",
      });
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Aanmaken mislukt");
    }
  };

  const handleDelete = async (id: string) => {
    if (!await confirmDelete({ title: "Verschot verwijderen", description: "Weet je zeker dat je dit verschot wilt verwijderen?", variant: "destructive", confirmText: "Verwijderen" })) return;
    try {
      await deleteExpense.mutateAsync(id);
      toast.success("Verschot verwijderd");
    } catch {
      toast.error("Verwijderen mislukt");
    }
  };

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="rounded-xl border border-border bg-card">
      {ConfirmDialogEl2}
      <div className="flex items-center justify-between border-b border-border px-5 py-4">
        <div className="flex items-center gap-2">
          <Receipt className="h-5 w-5 text-primary" />
          <h2 className="text-base font-semibold text-foreground">Verschotten</h2>
        </div>
        <button
          type="button"
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          Verschot toevoegen
        </button>
      </div>

      <div className="p-5 space-y-4">
        {/* Create form */}
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
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  className={inputClass}
                  placeholder="Bijv. Griffierecht kantonrechter"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-foreground">
                  Bedrag *
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  value={form.amount}
                  onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
                  className={inputClass}
                  placeholder="0,00"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-foreground">
                  Datum *
                </label>
                <input
                  type="date"
                  required
                  value={form.expense_date}
                  onChange={(e) => setForm((f) => ({ ...f, expense_date: e.target.value }))}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-foreground">
                  Categorie
                </label>
                <select
                  value={form.category}
                  onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
                  className={inputClass}
                >
                  {Object.entries(EXPENSE_CATEGORY_LABELS).map(([val, label]) => (
                    <option key={val} value={val}>{label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-foreground">
                  BTW-type
                </label>
                <select
                  value={form.tax_type}
                  onChange={(e) => setForm((f) => ({ ...f, tax_type: e.target.value }))}
                  className={inputClass}
                >
                  <option value="belast">Belast (BTW)</option>
                  <option value="onbelast">Onbelast (geen BTW)</option>
                  <option value="vrijgesteld">Vrijgesteld</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-foreground">
                  Bestand (optioneel)
                </label>
                <select
                  value={form.file_id}
                  onChange={(e) => setForm((f) => ({ ...f, file_id: e.target.value }))}
                  className={inputClass}
                >
                  <option value="">Geen bestand</option>
                  {caseFiles?.map((file) => (
                    <option key={file.id} value={file.id}>
                      {file.original_filename}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.billable}
                  onChange={(e) => setForm((f) => ({ ...f, billable: e.target.checked }))}
                  className="h-4 w-4 rounded border-input text-primary focus:ring-primary/20"
                />
                <span className="text-sm font-medium text-foreground">Doorbelastbaar</span>
              </label>
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={createExpense.isPending}
                className="rounded-lg bg-primary px-4 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {createExpense.isPending ? "Opslaan..." : "Opslaan"}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="rounded-lg border border-border px-4 py-2 text-xs font-medium text-muted-foreground hover:bg-muted"
              >
                Annuleren
              </button>
            </div>
          </form>
        )}

        {/* Expenses list */}
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : !expenses || expenses.length === 0 ? (
          <EmptyState
            icon={Receipt}
            title="Nog geen verschotten"
            description="Registreer kosten zoals griffierecht of deurwaarderskosten die doorbelast worden aan de client."
          />
        ) : (
          <div className="divide-y divide-border">
            {expenses.map((expense) => (
              <div key={expense.id} className="flex items-center justify-between py-3 px-1 group">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground truncate">
                      {expense.description}
                    </span>
                    <span className="inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium bg-muted text-muted-foreground">
                      {EXPENSE_CATEGORY_LABELS[expense.category] || expense.category}
                    </span>
                    {expense.tax_type !== "belast" && (
                      <span className="inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium bg-amber-100 text-amber-700">
                        {TAX_TYPE_LABELS[expense.tax_type] || expense.tax_type}
                      </span>
                    )}
                    {expense.invoiced && (
                      <span className="inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium bg-green-100 text-green-700">
                        Gefactureerd
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {formatDateShort(expense.expense_date)}
                    {!expense.billable && " · Niet doorbelastbaar"}
                    {expense.file_id && " · Bestand gekoppeld"}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold tabular-nums text-foreground">
                    {formatCurrency(expense.amount)}
                  </span>
                  {!expense.invoiced && (
                    <button
                      onClick={() => handleDelete(expense.id)}
                      className="rounded p-1 text-muted-foreground hover:text-red-600 hover:bg-red-50 opacity-0 group-hover:opacity-100 transition-all"
                      title="Verwijderen"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {expenses && expenses.length > 0 && (
          <div className="flex items-center justify-between border-t border-border pt-3">
            <p className="text-sm text-muted-foreground">
              {expenses.length} verschot{expenses.length !== 1 ? "ten" : ""}
            </p>
            <p className="text-sm font-semibold text-foreground tabular-nums">
              Totaal: {formatCurrency(expenses.reduce((sum, e) => sum + e.amount, 0))}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export function DocumentenTab({ caseId, caseNumber, caseStatus, debtorType, opposingPartyName }: { caseId: string; caseNumber?: string; caseStatus?: string; debtorType?: string | null; opposingPartyName?: string }) {
  const { data: templates, isLoading: templatesLoading } = useDocxTemplates();
  const { data: documents, isLoading: docsLoading } = useCaseDocuments(caseId);
  const { data: emailLogs } = useEmailLogs(caseId);
  const generateDocx = useGenerateDocx(caseId);
  const deleteDocument = useDeleteDocument(caseId);
  const sendDocument = useSendDocument(caseId);
  const { confirm: confirmDelete, ConfirmDialog: ConfirmDialogEl3 } = useConfirm();

  // Build set of document titles that have been emailed (for "Verzonden" badge)
  const sentDocTitles = new Set(
    (emailLogs ?? [])
      .filter((log) => log.status === "sent")
      .map((log) => log.subject)
  );

  // Email compose dialog state
  const [emailDialogOpen, setEmailDialogOpen] = useState(false);
  const [emailDoc, setEmailDoc] = useState<GeneratedDocumentSummary | null>(null);

  // Template filtering by status (T1)
  const [showAllTemplates, setShowAllTemplates] = useState(false);
  const statusTemplates = getTemplatesForStatus(caseStatus ?? "", debtorType);

  // File uploads (E4)
  const { data: caseFiles, isLoading: filesLoading } = useCaseFiles(caseId);
  const uploadFile = useUploadCaseFile(caseId);
  const deleteCaseFile = useDeleteCaseFile(caseId);
  const renameCaseFile = useRenameCaseFile(caseId);
  const [isDragOver, setIsDragOver] = useState(false);
  const [renamingFileId, setRenamingFileId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  // Email attachments (LF-17)
  const { data: emailAttachments, isLoading: emailAttachmentsLoading } = useCaseEmailAttachments(caseId);
  const saveAttachment = useSaveAttachmentToCase();

  // LF-21: File type filter
  const [fileTypeFilter, setFileTypeFilter] = useState<string>("alle");

  // G11: Inline document preview
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewTitle, setPreviewTitle] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);

  // Cleanup blob URL on close
  const closePreview = useCallback(() => {
    setPreviewOpen(false);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setPreviewTitle("");
  }, [previewUrl]);

  // Close on Escape key
  useEffect(() => {
    if (!previewOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closePreview();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [previewOpen, closePreview]);

  /** Preview a generated document (DOCX → PDF via backend). */
  const handlePreviewDocument = async (docId: string, title: string) => {
    setPreviewTitle(title);
    setPreviewLoading(true);
    setPreviewOpen(true);
    try {
      const token = tokenStore.getAccess();
      const apiUrl = "";
      const res = await fetch(`${apiUrl}/api/documents/${docId}/preview`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Preview laden mislukt");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Preview laden mislukt");
      setPreviewOpen(false);
    } finally {
      setPreviewLoading(false);
    }
  };

  /** Preview an uploaded case file (PDF/image direct, DOCX → PDF). */
  const handlePreviewFile = async (fileId: string, filename: string) => {
    setPreviewTitle(filename);
    setPreviewLoading(true);
    setPreviewOpen(true);
    try {
      const token = tokenStore.getAccess();
      const apiUrl = "";
      const res = await fetch(
        `${apiUrl}/api/cases/${caseId}/files/${fileId}/preview`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error("Preview laden mislukt");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Preview laden mislukt");
      setPreviewOpen(false);
    } finally {
      setPreviewLoading(false);
    }
  };

  /** Preview an email attachment (PDF/image). */
  const handlePreviewEmailAttachment = async (attachmentId: string, filename: string) => {
    setPreviewTitle(filename);
    setPreviewLoading(true);
    setPreviewOpen(true);
    try {
      const token = tokenStore.getAccess();
      const res = await fetch(
        `/api/email/attachments/${attachmentId}/download`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error("Preview laden mislukt");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Preview laden mislukt");
      setPreviewOpen(false);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleGenerate = async (templateType: string) => {
    try {
      const result = await generateDocx.mutateAsync(templateType);
      triggerDownload(result.blob, result.filename);
      toast.success(`${getTemplateLabel(templateType)} gegenereerd`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Fout bij genereren document");
    }
  };

  const handleDelete = async (docId: string) => {
    if (!await confirmDelete({ title: "Document verwijderen", description: "Weet je zeker dat je dit document wilt verwijderen?", variant: "destructive", confirmText: "Verwijderen" })) return;
    try {
      await deleteDocument.mutateAsync(docId);
      toast.success("Document verwijderd");
    } catch {
      toast.error("Fout bij verwijderen document");
    }
  };

  const handleOpenEmailDialog = (doc: GeneratedDocumentSummary) => {
    setEmailDoc(doc);
    setEmailDialogOpen(true);
  };

  const handleSendEmail = async (data: EmailComposeData) => {
    if (!emailDoc) return;
    try {
      await sendDocument.mutateAsync({
        documentId: emailDoc.id,
        data: {
          recipient_email: data.recipient_email,
          recipient_name: data.recipient_name,
          cc: data.cc,
          custom_subject: data.custom_subject,
          custom_body: data.custom_body,
        },
      });
      toast.success("E-mail verzonden");
      setEmailDialogOpen(false);
      setEmailDoc(null);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Fout bij verzenden e-mail");
    }
  };

  const handleFiles = (files: FileList | File[]) => {
    Array.from(files).forEach((file) => {
      uploadFile.mutate({ file });
    });
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  return (
    <div className="space-y-6">
      {ConfirmDialogEl3}
      {/* Generate from templates (T1: status-filtered) */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="mb-1 text-base font-semibold text-foreground">
          Document genereren
        </h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Genereer een Word-document vanuit een template
        </p>

        {templatesLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Templates laden...
          </div>
        ) : (() => {
          const allAvailable = templates?.filter((t) => t.available) ?? [];
          const recommendedTypes = new Set(statusTemplates.recommended);
          const availableTypes = new Set(statusTemplates.available);
          const recommended = allAvailable.filter((t) => recommendedTypes.has(t.template_type));
          const other = allAvailable.filter((t) => !recommendedTypes.has(t.template_type) && availableTypes.has(t.template_type));
          const hidden = allAvailable.filter((t) => !recommendedTypes.has(t.template_type) && !availableTypes.has(t.template_type));

          return (
            <div className="space-y-4">
              {/* Aanbevolen templates */}
              {recommended.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <Star className="h-3.5 w-3.5 text-amber-500" />
                    <span className="text-xs font-medium text-amber-700 dark:text-amber-400">Aanbevolen voor huidige status</span>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {recommended.map((template) => (
                      <button
                        key={template.template_type}
                        onClick={() => handleGenerate(template.template_type)}
                        disabled={generateDocx.isPending}
                        className="flex flex-col items-start gap-2 rounded-lg border-2 border-primary/30 bg-primary/5 p-4 text-left hover:border-primary/50 hover:bg-primary/10 transition-all disabled:opacity-50"
                      >
                        <div className="flex items-center gap-2">
                          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                            <FileText className="h-4 w-4 text-primary" />
                          </div>
                          <span className="text-sm font-medium text-foreground">
                            {getTemplateLabel(template.template_type)}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          {getTemplateDescription(template.template_type)}
                        </p>
                        <div className="mt-auto flex items-center gap-1 text-xs text-primary font-medium">
                          <Download className="h-3 w-3" />
                          {generateDocx.isPending ? "Genereren..." : "Download .docx"}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Overige beschikbare templates */}
              {other.length > 0 && (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {other.map((template) => (
                    <button
                      key={template.template_type}
                      onClick={() => handleGenerate(template.template_type)}
                      disabled={generateDocx.isPending}
                      className="flex flex-col items-start gap-2 rounded-lg border border-border p-4 text-left hover:border-primary/30 hover:bg-muted/50 transition-all disabled:opacity-50"
                    >
                      <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <span className="text-sm font-medium text-foreground">
                          {getTemplateLabel(template.template_type)}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        {getTemplateDescription(template.template_type)}
                      </p>
                      <div className="mt-auto flex items-center gap-1 text-xs text-primary">
                        <Download className="h-3 w-3" />
                        {generateDocx.isPending ? "Genereren..." : "Download .docx"}
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {/* Verborgen templates (Toon alle) */}
              {hidden.length > 0 && (
                <div>
                  <button
                    type="button"
                    onClick={() => setShowAllTemplates(!showAllTemplates)}
                    className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <ChevronDown className={`h-3.5 w-3.5 transition-transform ${showAllTemplates ? "rotate-180" : ""}`} />
                    {showAllTemplates ? "Verberg" : `Toon alle templates (${hidden.length} meer)`}
                  </button>
                  {showAllTemplates && (
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 mt-3">
                      {hidden.map((template) => (
                        <button
                          key={template.template_type}
                          onClick={() => handleGenerate(template.template_type)}
                          disabled={generateDocx.isPending}
                          className="flex flex-col items-start gap-2 rounded-lg border border-dashed border-border p-4 text-left hover:border-primary/30 hover:bg-muted/50 transition-all disabled:opacity-50 opacity-70"
                        >
                          <div className="flex items-center gap-2">
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                              <FileText className="h-4 w-4 text-muted-foreground" />
                            </div>
                            <span className="text-sm font-medium text-foreground">
                              {getTemplateLabel(template.template_type)}
                            </span>
                          </div>
                          <p className="text-xs text-muted-foreground leading-relaxed">
                            {getTemplateDescription(template.template_type)}
                          </p>
                          <div className="mt-auto flex items-center gap-1 text-xs text-muted-foreground">
                            <Download className="h-3 w-3" />
                            {generateDocx.isPending ? "Genereren..." : "Download .docx"}
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Fallback als er geen templates zijn */}
              {recommended.length === 0 && other.length === 0 && hidden.length === 0 && (
                <div className="rounded-lg border border-dashed border-border py-6 text-center">
                  <FileText className="mx-auto h-6 w-6 text-muted-foreground/30" />
                  <p className="mt-1.5 text-sm text-muted-foreground">
                    Geen templates beschikbaar
                  </p>
                </div>
              )}
            </div>
          );
        })()}
      </div>

      {/* File uploads (E4) */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-foreground">Bestanden</h2>
            <p className="text-sm text-muted-foreground">
              Upload documenten zoals contracten, vonnissen en correspondentie
            </p>
          </div>
          {uploadFile.isPending && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Uploaden...
            </div>
          )}
        </div>

        {/* Drag & drop zone */}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={() => setIsDragOver(false)}
          className={`relative mb-4 rounded-lg border-2 border-dashed p-6 text-center transition-colors cursor-pointer ${
            isDragOver
              ? "border-primary bg-primary/5"
              : "border-border hover:border-primary/30 hover:bg-muted/30"
          }`}
          onClick={() => {
            const input = document.createElement("input");
            input.type = "file";
            input.multiple = true;
            input.accept = ".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.txt,.eml,.msg";
            input.onchange = (e) => {
              const files = (e.target as HTMLInputElement).files;
              if (files) handleFiles(files);
            };
            input.click();
          }}
        >
          <Upload className={`mx-auto h-8 w-8 ${isDragOver ? "text-primary" : "text-muted-foreground/40"}`} />
          <p className="mt-2 text-sm text-muted-foreground">
            {isDragOver ? (
              <span className="text-primary font-medium">Laat los om te uploaden</span>
            ) : (
              <>Sleep bestanden hierheen of <span className="text-primary font-medium">klik om te uploaden</span></>
            )}
          </p>
          <p className="mt-1 text-xs text-muted-foreground/60">
            PDF, Word, Excel, afbeeldingen, e-mail · max. 50 MB
          </p>
        </div>

        {/* File list — merged uploaded files + email attachments */}
        {(() => {
          const loading = filesLoading || emailAttachmentsLoading;
          // Build unified list
          type UnifiedFile =
            | { type: "upload"; id: string; filename: string; file_size: number; content_type: string; date: string; direction?: string | null }
            | { type: "email"; id: string; filename: string; file_size: number; content_type: string; date: string; email_subject: string | null; email_from: string | null; synced_email_id: string };

          const allItems: UnifiedFile[] = [
            ...(caseFiles ?? []).map((f) => ({
              type: "upload" as const,
              id: f.id,
              filename: f.original_filename,
              file_size: f.file_size,
              content_type: f.content_type,
              date: f.created_at,
              direction: f.document_direction,
            })),
            ...(emailAttachments ?? []).map((a) => ({
              type: "email" as const,
              id: a.id,
              filename: a.filename,
              file_size: a.file_size,
              content_type: a.content_type,
              date: a.email_date ?? "",
              email_subject: a.email_subject,
              email_from: a.email_from,
              synced_email_id: a.synced_email_id,
            })),
          ].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

          // LF-21: File type categorization & filtering
          const getFileCategory = (contentType: string): string => {
            if (contentType === "application/pdf") return "pdf";
            if (contentType.includes("word") || contentType.includes("msword")) return "word";
            if (contentType.includes("excel") || contentType.includes("spreadsheet")) return "excel";
            if (contentType.startsWith("image/")) return "afbeelding";
            if (contentType.includes("email") || contentType.includes("message")) return "email";
            return "overig";
          };

          const FILE_TYPE_OPTIONS: { value: string; label: string; icon: React.ReactNode }[] = [
            { value: "alle", label: "Alle", icon: <File className="h-3 w-3" /> },
            { value: "pdf", label: "PDF", icon: <FileText className="h-3 w-3" /> },
            { value: "word", label: "Word", icon: <FileText className="h-3 w-3" /> },
            { value: "excel", label: "Excel", icon: <FileSpreadsheet className="h-3 w-3" /> },
            { value: "afbeelding", label: "Afbeeldingen", icon: <Image className="h-3 w-3" /> },
            { value: "email", label: "E-mail", icon: <Mail className="h-3 w-3" /> },
            { value: "overig", label: "Overig", icon: <File className="h-3 w-3" /> },
          ];

          // Count per category
          const categoryCounts: Record<string, number> = {};
          allItems.forEach((item) => {
            const cat = getFileCategory(item.content_type);
            categoryCounts[cat] = (categoryCounts[cat] ?? 0) + 1;
          });

          // Only show filter options that have items
          const visibleOptions = FILE_TYPE_OPTIONS.filter(
            (opt) => opt.value === "alle" || (categoryCounts[opt.value] ?? 0) > 0
          );

          const items = fileTypeFilter === "alle"
            ? allItems
            : allItems.filter((item) => getFileCategory(item.content_type) === fileTypeFilter);

          if (loading) {
            return (
              <div className="space-y-2">
                {[1, 2].map((i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg border border-border p-3">
                    <div className="flex items-center gap-3">
                      <div className="h-9 w-9 rounded-lg skeleton" />
                      <div className="space-y-2">
                        <div className="h-4 w-32 rounded skeleton" />
                        <div className="h-3 w-20 rounded skeleton" />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            );
          }

          if (!allItems.length) {
            return (
              <EmptyState
                icon={File}
                title="Nog geen bestanden"
                description="Upload bestanden via het uploadgebied hierboven, of genereer documenten via sjablonen."
              />
            );
          }

          return (
            <div className="space-y-3">
              {/* LF-21: Bestandstype filter */}
              {visibleOptions.length > 2 && (
                <div className="flex items-center gap-2 flex-wrap">
                  <Filter className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  {visibleOptions.map((opt) => {
                    const isActive = fileTypeFilter === opt.value;
                    const count = opt.value === "alle" ? allItems.length : (categoryCounts[opt.value] ?? 0);
                    return (
                      <button
                        key={opt.value}
                        onClick={() => setFileTypeFilter(opt.value)}
                        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                          isActive
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground"
                        }`}
                      >
                        {opt.icon}
                        {opt.label}
                        <span className={`ml-0.5 ${isActive ? "text-primary-foreground/70" : "text-muted-foreground/60"}`}>
                          {count}
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* Filtered results */}
              {items.length === 0 ? (
                <div className="rounded-lg border border-dashed border-border py-6 text-center">
                  <Filter className="mx-auto h-6 w-6 text-muted-foreground/30" />
                  <p className="mt-1.5 text-sm text-muted-foreground">
                    Geen bestanden van dit type
                  </p>
                  <button
                    onClick={() => setFileTypeFilter("alle")}
                    className="mt-2 text-xs text-primary hover:text-primary/80 font-medium"
                  >
                    Toon alle bestanden
                  </button>
                </div>
              ) : (
              <div className="space-y-2">
              {items.map((item) => {
                const icon = getFileIcon(item.content_type);
                const isEmail = item.type === "email";

                return (
                  <div
                    key={`${item.type}-${item.id}`}
                    className="flex items-center justify-between rounded-lg border border-border p-3 hover:bg-muted/30 transition-colors group"
                  >
                    <button
                      onClick={() =>
                        isEmail
                          ? downloadEmailAttachment(item.id, item.filename)
                          : downloadCaseFile(caseId, item.id, item.filename)
                      }
                      className="flex items-center gap-3 min-w-0 flex-1 text-left"
                    >
                      <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${icon.color}`}>
                        <span className="text-[10px] font-bold">{icon.label}</span>
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          {!isEmail && renamingFileId === item.id ? (
                            <input
                              autoFocus
                              type="text"
                              value={renameValue}
                              onChange={(e) => setRenameValue(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === "Enter" && renameValue.trim()) {
                                  renameCaseFile.mutate(
                                    { fileId: item.id, filename: renameValue.trim() },
                                    { onSuccess: () => setRenamingFileId(null) }
                                  );
                                }
                                if (e.key === "Escape") setRenamingFileId(null);
                              }}
                              onBlur={() => {
                                if (renameValue.trim() && renameValue.trim() !== item.filename) {
                                  renameCaseFile.mutate(
                                    { fileId: item.id, filename: renameValue.trim() },
                                    { onSuccess: () => setRenamingFileId(null) }
                                  );
                                } else {
                                  setRenamingFileId(null);
                                }
                              }}
                              className="text-sm font-medium text-foreground bg-background border border-input rounded px-1.5 py-0.5 outline-none focus:ring-1 focus:ring-ring w-full max-w-xs"
                              onClick={(e) => e.stopPropagation()}
                            />
                          ) : (
                            <p className="text-sm font-medium text-foreground truncate group-hover:text-primary transition-colors">
                              {item.filename}
                            </p>
                          )}
                          {isEmail && (
                            <span className="inline-flex items-center gap-1 shrink-0 rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-medium text-blue-700 ring-1 ring-inset ring-blue-600/20 dark:bg-blue-950 dark:text-blue-300 dark:ring-blue-400/30">
                              <Mail className="h-2.5 w-2.5" />
                              Email bijlage
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground truncate">
                          {formatFileSize(item.file_size)} · {formatDateShort(item.date)}
                          {isEmail && item.email_from && (
                            <span className="ml-1"> · Van: {item.email_from}</span>
                          )}
                          {isEmail && item.email_subject && (
                            <span className="ml-1"> · {item.email_subject}</span>
                          )}
                          {!isEmail && item.direction && (
                            <span className="ml-1.5">
                              · {item.direction === "inkomend" ? "↙ Inkomend" : "↗ Uitgaand"}
                            </span>
                          )}
                        </p>
                      </div>
                    </button>
                    <div className="flex items-center gap-1">
                      {!isEmail && isPreviewable(item.content_type) && (
                        <button
                          onClick={() => handlePreviewFile(item.id, item.filename)}
                          className="shrink-0 rounded-lg p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors opacity-0 group-hover:opacity-100"
                          title="Preview"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      )}
                      {isEmail && isPreviewable(item.content_type) && (
                        <button
                          onClick={() => handlePreviewEmailAttachment(item.id, item.filename)}
                          className="shrink-0 rounded-lg p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors opacity-0 group-hover:opacity-100"
                          title="Preview"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      )}
                      {isEmail && (
                        <button
                          onClick={() => {
                            saveAttachment.mutate(
                              { attachmentId: item.id, caseId },
                              {
                                onSuccess: () => toast.success(`${item.filename} opgeslagen in dossier`),
                              }
                            );
                          }}
                          className="shrink-0 rounded-lg p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors opacity-0 group-hover:opacity-100"
                          title="Opslaan in dossier"
                        >
                          <Save className="h-4 w-4" />
                        </button>
                      )}
                      {!isEmail && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setRenamingFileId(item.id);
                            setRenameValue(item.filename);
                          }}
                          className="shrink-0 rounded-lg p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors opacity-0 group-hover:opacity-100"
                          title="Hernoemen"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                      )}
                      {!isEmail && (
                        <button
                          onClick={async () => { if (await confirmDelete({ title: "Bestand verwijderen", description: "Weet je zeker dat je dit bestand wilt verwijderen?", variant: "destructive", confirmText: "Verwijderen" })) deleteCaseFile.mutate(item.id); }}
                          className="shrink-0 rounded-lg p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors opacity-0 group-hover:opacity-100"
                          title="Verwijderen"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
              )}
            </div>
          );
        })()}
      </div>

      {/* Generated documents list */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="mb-1 text-base font-semibold text-foreground">
          Gegenereerde documenten
        </h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Eerder gegenereerde documenten voor dit dossier
        </p>

        {docsLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Documenten laden...
          </div>
        ) : !documents?.length ? (
          <EmptyState
            icon={FileText}
            title="Nog geen documenten"
            description="Genereer documenten vanuit sjablonen zoals sommaties, dagvaardingen of brieven."
          />
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between rounded-lg border border-border p-3 hover:bg-muted/30 transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-foreground">
                        {doc.title}
                      </p>
                      {sentDocTitles.has(doc.title) && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
                          <Send className="h-2.5 w-2.5" />
                          Verzonden
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {formatDateShort(doc.created_at)}
                      {doc.document_type && (
                        <span className="ml-1.5">· {getTemplateLabel(doc.document_type)}</span>
                      )}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handlePreviewDocument(doc.id, doc.title)}
                    className="rounded-lg p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors opacity-0 group-hover:opacity-100"
                    title="Preview"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleOpenEmailDialog(doc)}
                    className="rounded-lg p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors opacity-0 group-hover:opacity-100"
                    title="Verstuur per e-mail"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    className="rounded-lg p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors opacity-0 group-hover:opacity-100"
                    title="Verwijderen"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Email compose dialog */}
      <EmailComposeDialog
        open={emailDialogOpen}
        onOpenChange={setEmailDialogOpen}
        onSend={handleSendEmail}
        isSending={sendDocument.isPending}
        defaultSubject={emailDoc ? `${emailDoc.title}${caseNumber ? ` — ${caseNumber}` : ""}` : ""}
        defaultBody={emailDoc ? `Geachte heer/mevrouw,\n\nBijgaand treft u het document "${emailDoc.title}" aan${caseNumber ? ` inzake zaak ${caseNumber}` : ""}.\n\nHet document is als bijlage bij deze e-mail gevoegd.\n\nMet vriendelijke groet` : ""}
        defaultToName={opposingPartyName || ""}
        attachmentName={emailDoc ? `${emailDoc.title}.pdf` : undefined}
      />

      {/* G11: Document preview dialog */}
      {previewOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="relative flex h-[90vh] w-[90vw] max-w-5xl flex-col rounded-xl border border-border bg-card shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border px-5 py-3">
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                  <Eye className="h-4 w-4 text-primary" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-sm font-semibold text-foreground truncate">
                    {previewTitle}
                  </h3>
                  <p className="text-xs text-muted-foreground">Document preview</p>
                </div>
              </div>
              <button
                onClick={closePreview}
                className="rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                title="Sluiten (Esc)"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-hidden bg-muted/30">
              {previewLoading ? (
                <div className="flex h-full items-center justify-center">
                  <div className="flex flex-col items-center gap-3">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    <p className="text-sm text-muted-foreground">Preview laden...</p>
                  </div>
                </div>
              ) : previewUrl ? (
                <iframe
                  src={previewUrl}
                  className="h-full w-full border-0"
                  title={`Preview: ${previewTitle}`}
                />
              ) : (
                <div className="flex h-full items-center justify-center">
                  <p className="text-sm text-muted-foreground">Preview niet beschikbaar</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
