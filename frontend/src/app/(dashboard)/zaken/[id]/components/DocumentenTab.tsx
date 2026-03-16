"use client";

import { useState, useCallback, useEffect } from "react";
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
  FileText,
  Loader2,
  Plus,
  Receipt,
  Send,
  Star,
  Trash2,
  Upload,
  X,
  XCircle,
} from "lucide-react";
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
  INVOICE_STATUS_LABELS,
  INVOICE_STATUS_COLORS,
} from "@/hooks/use-invoices";
import { useUnbilledTimeEntries } from "@/hooks/use-time-entries";
import {
  useCaseFiles,
  useUploadCaseFile,
  useDeleteCaseFile,
  downloadCaseFile,
  formatFileSize,
  getFileIcon,
  isPreviewable,
} from "@/hooks/use-case-files";
import { formatCurrency, formatDateShort } from "@/lib/utils";

export function FacturenTab({ caseId, clientId }: { caseId: string; clientId?: string }) {
  const router = useRouter();
  const { data, isLoading } = useInvoices({ case_id: caseId, per_page: 100 });
  const invoices = data?.items ?? [];
  const createInvoice = useCreateInvoice();

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
    } catch (err: any) {
      toast.error(err.message || "Factuur aanmaken mislukt");
    }
  };

  return (
    <div className="space-y-6">
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
          <div className="rounded-lg border border-dashed border-border py-8 text-center">
            <CreditCard className="mx-auto h-8 w-8 text-muted-foreground/30" />
            <p className="mt-2 text-sm text-muted-foreground">
              Nog geen facturen voor dit dossier
            </p>
            <Link
              href={`/facturen/nieuw?case_id=${caseId}`}
              className="mt-3 inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              <Plus className="h-3.5 w-3.5" />
              Eerste factuur aanmaken
            </Link>
          </div>
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
  const [isDragOver, setIsDragOver] = useState(false);

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
      const token = localStorage.getItem("luxis_access_token");
      const apiUrl = "";
      const res = await fetch(`${apiUrl}/api/documents/${docId}/preview`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Preview laden mislukt");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
    } catch (err: any) {
      toast.error(err.message || "Preview laden mislukt");
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
      const token = localStorage.getItem("luxis_access_token");
      const apiUrl = "";
      const res = await fetch(
        `${apiUrl}/api/cases/${caseId}/files/${fileId}/preview`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error("Preview laden mislukt");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
    } catch (err: any) {
      toast.error(err.message || "Preview laden mislukt");
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
    } catch (err: any) {
      toast.error(err.message || "Fout bij genereren document");
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm("Weet je zeker dat je dit document wilt verwijderen?")) return;
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
    } catch (err: any) {
      toast.error(err.message || "Fout bij verzenden e-mail");
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

        {/* File list */}
        {filesLoading ? (
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
        ) : !caseFiles?.length ? (
          <div className="rounded-lg border border-dashed border-border py-6 text-center">
            <File className="mx-auto h-6 w-6 text-muted-foreground/30" />
            <p className="mt-1.5 text-sm text-muted-foreground">
              Nog geen bestanden geüpload
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {caseFiles.map((f) => {
              const icon = getFileIcon(f.content_type);
              return (
                <div
                  key={f.id}
                  className="flex items-center justify-between rounded-lg border border-border p-3 hover:bg-muted/30 transition-colors group"
                >
                  <button
                    onClick={() => downloadCaseFile(caseId, f.id, f.original_filename)}
                    className="flex items-center gap-3 min-w-0 flex-1 text-left"
                  >
                    <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${icon.color}`}>
                      <span className="text-[10px] font-bold">{icon.label}</span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-foreground truncate group-hover:text-primary transition-colors">
                        {f.original_filename}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(f.file_size)} · {formatDateShort(f.created_at)}
                        {f.document_direction && (
                          <span className="ml-1.5">
                            · {f.document_direction === "inkomend" ? "↙ Inkomend" : "↗ Uitgaand"}
                          </span>
                        )}
                      </p>
                    </div>
                  </button>
                  <div className="flex items-center gap-1">
                    {isPreviewable(f.content_type) && (
                      <button
                        onClick={() => handlePreviewFile(f.id, f.original_filename)}
                        className="shrink-0 rounded-lg p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors opacity-0 group-hover:opacity-100"
                        title="Preview"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    )}
                    <button
                      onClick={() => { if (confirm("Weet je zeker dat je dit bestand wilt verwijderen?")) deleteCaseFile.mutate(f.id); }}
                      className="shrink-0 rounded-lg p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors opacity-0 group-hover:opacity-100"
                      title="Verwijderen"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
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
          <div className="rounded-lg border border-dashed border-border py-8 text-center">
            <File className="mx-auto h-8 w-8 text-muted-foreground/30" />
            <p className="mt-2 text-sm text-muted-foreground">
              Nog geen documenten gegenereerd voor dit dossier
            </p>
          </div>
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
