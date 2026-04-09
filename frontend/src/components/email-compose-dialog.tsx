"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useUnsavedWarning } from "@/hooks/use-unsaved-warning";
import {
  Mail, Paperclip, Loader2, X, Plus,
  ExternalLink, FileText, Upload, FolderSearch, BookMarked,
} from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { useRenderTemplate, type ComposeInlineAttachment } from "@/hooks/use-email-sync";

// ── Types ────────────────────────────────────────────────────────────────────

export interface EmailComposeData {
  recipient_email: string;
  recipient_name?: string | null;
  cc?: string[] | null;
  custom_subject?: string | null;
  custom_body?: string | null;
  body_html?: string | null;
  case_file_ids?: string[];
  inline_attachments?: ComposeInlineAttachment[];
}

export interface EmailRecipient {
  name: string;
  email: string;
  role: string;
}

interface CaseFileItem {
  id: string;
  original_filename: string;
  file_size: number;
  content_type: string;
}

interface TemplateInfo {
  template_type: string;
  filename: string;
  available: boolean;
}

interface LibraryTemplate {
  template_key: string;
  name: string;
  description: string | null;
}

interface AttachmentRef {
  id: string;
  filename: string;
  size: number;
  source: "dossier" | "upload" | "other" | "library";
}

// ── Helpers ──────────────────────────────────────────────────────────────────

const ROLE_LABELS: Record<string, string> = {
  client: "Cliënt",
  opposing_party: "Wederpartij",
  advocaat_wederpartij: "Adv. wederpartij",
  deurwaarder: "Deurwaarder",
  rechtbank: "Rechtbank",
  mediator: "Mediator",
  deskundige: "Deskundige",
  getuige: "Getuige",
  notaris: "Notaris",
  overig: "Overig",
};

const TEMPLATE_LABELS: Record<string, string> = {
  aanmaning: "Aanmaning",
  sommatie: "Sommatie",
  tweede_sommatie: "Tweede sommatie",
  "14_dagenbrief": "14-dagenbrief",
  herinnering: "Herinnering",
  dagvaarding: "Dagvaarding",
  renteoverzicht: "Renteoverzicht",
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ── Props ────────────────────────────────────────────────────────────────────

export interface EmailComposeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSend: (data: EmailComposeData) => void;
  onSendDirect?: (data: EmailComposeData) => void;
  isSending?: boolean;
  defaultTo?: string;
  defaultToName?: string;
  defaultSubject?: string;
  defaultBody?: string;
  attachmentName?: string;
  title?: string;
  recipients?: EmailRecipient[];
  caseId?: string;
}

// ── Component ────────────────────────────────────────────────────────────────

export function EmailComposeDialog({
  open,
  onOpenChange,
  onSend,
  onSendDirect,
  isSending = false,
  defaultTo = "",
  defaultToName = "",
  defaultSubject = "",
  defaultBody = "",
  attachmentName,
  title = "Nieuwe e-mail",
  recipients,
  caseId,
}: EmailComposeDialogProps) {
  // ── State ─────────────────────────────────────────────────────────────
  const [to, setTo] = useState(defaultTo);
  const [toName, setToName] = useState(defaultToName);
  const [ccList, setCcList] = useState<string[]>([]);
  const [ccInput, setCcInput] = useState("");
  const [showCc, setShowCc] = useState(false);
  const [subject, setSubject] = useState(defaultSubject);
  const [body, setBody] = useState(defaultBody);
  const [selectedChip, setSelectedChip] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Template
  const [selectedTemplate, setSelectedTemplate] = useState<string>("");
  const [templateHtml, setTemplateHtml] = useState<string | null>(null);
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const renderTemplate = caseId ? useRenderTemplate(caseId) : null;

  // Attachments
  const [attachments, setAttachments] = useState<AttachmentRef[]>([]);
  const [inlineFiles, setInlineFiles] = useState<Map<string, ComposeInlineAttachment>>(new Map());
  const [caseFileIds, setCaseFileIds] = useState<Set<string>>(new Set());
  const [showFilePicker, setShowFilePicker] = useState(false);
  const [caseFiles, setCaseFiles] = useState<CaseFileItem[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Warn on unsaved changes
  const composeDirty = useMemo(
    () => open && (subject !== defaultSubject || body !== defaultBody || to !== defaultTo || attachments.length > 0),
    [open, subject, defaultSubject, body, defaultBody, to, defaultTo, attachments.length]
  );
  useUnsavedWarning(composeDirty);

  // Template editor ref
  const templateEditorRef = useRef<HTMLDivElement>(null);

  // Other-case picker
  const [showOtherCase, setShowOtherCase] = useState(false);
  const [otherSearch, setOtherSearch] = useState("");
  const [otherResults, setOtherResults] = useState<{ id: string; case_number: string; description: string }[]>([]);
  const [otherSelected, setOtherSelected] = useState<string | null>(null);
  const [otherFiles, setOtherFiles] = useState<CaseFileItem[]>([]);
  const [loadingOther, setLoadingOther] = useState(false);
  const [loadingOtherFiles, setLoadingOtherFiles] = useState(false);

  // Library templates (render-to-PDF uit sjablonen-bibliotheek)
  const [showLibrary, setShowLibrary] = useState(false);
  const [libraryTemplates, setLibraryTemplates] = useState<LibraryTemplate[]>([]);
  const [loadingLibrary, setLoadingLibrary] = useState(false);
  const [renderingLibraryKey, setRenderingLibraryKey] = useState<string | null>(null);

  // Load templates
  useEffect(() => {
    if (open && caseId && templates.length === 0) {
      api("/api/documents/docx/templates")
        .then((r) => r.ok ? r.json() : [])
        .then((data: TemplateInfo[]) => setTemplates(data.filter((t) => t.available)))
        .catch(() => {});
    }
  }, [open, caseId]);

  // Reset on open
  const handleOpenChange = (nextOpen: boolean) => {
    if (nextOpen) {
      setTo(defaultTo);
      setToName(defaultToName);
      setCcList([]);
      setCcInput("");
      setShowCc(false);
      setSubject(defaultSubject);
      setBody(defaultBody);
      setSelectedChip(null);
      setErrors({});
      setSelectedTemplate("");
      setTemplateHtml(null);
      setAttachments([]);
      setInlineFiles(new Map());
      setCaseFileIds(new Set());
      setShowFilePicker(false);
      setShowOtherCase(false);
      setOtherSearch("");
      setOtherResults([]);
      setOtherSelected(null);
      setOtherFiles([]);
      setShowLibrary(false);
      setRenderingLibraryKey(null);
    }
    onOpenChange(nextOpen);
  };

  // ── Recipient handlers ────────────────────────────────────────────────

  const selectRecipient = (r: EmailRecipient) => {
    if (selectedChip === r.email) {
      setTo("");
      setToName("");
      setSelectedChip(null);
    } else {
      setTo(r.email);
      setToName(r.name);
      setSelectedChip(r.email);
    }
  };

  const addCc = () => {
    const email = ccInput.trim();
    if (email && !ccList.includes(email)) {
      setCcList([...ccList, email]);
      setCcInput("");
    }
  };

  const addCcFromRecipient = (r: EmailRecipient) => {
    if (!ccList.includes(r.email)) setCcList([...ccList, r.email]);
  };

  // ── Template handlers ─────────────────────────────────────────────────

  const handleTemplateSelect = async (val: string) => {
    if (!val || !caseId || !renderTemplate) {
      setSelectedTemplate("");
      setTemplateHtml(null);
      return;
    }
    setSelectedTemplate(val);
    try {
      const result = await renderTemplate.mutateAsync({ template_type: val });
      if (result.supported && result.body_html) {
        setTemplateHtml(result.body_html);
        if (result.subject && !subject) setSubject(result.subject);
      } else {
        setSelectedTemplate("");
        setTemplateHtml(null);
      }
    } catch {
      setSelectedTemplate("");
      setTemplateHtml(null);
    }
  };

  // ── File picker handlers ──────────────────────────────────────────────

  const loadCaseFiles = async () => {
    if (!caseId) return;
    setLoadingFiles(true);
    try {
      const res = await api(`/api/cases/${caseId}/files`);
      if (res.ok) {
        const data = await res.json();
        setCaseFiles(data.items ?? data);
      }
    } catch { /* ignore */ }
    setLoadingFiles(false);
  };

  const toggleCaseFile = (f: CaseFileItem) => {
    const ids = new Set(caseFileIds);
    const atts = [...attachments];
    if (ids.has(f.id)) {
      ids.delete(f.id);
      const idx = atts.findIndex((a) => a.id === f.id);
      if (idx >= 0) atts.splice(idx, 1);
    } else {
      ids.add(f.id);
      atts.push({ id: f.id, filename: f.original_filename, size: f.file_size, source: "dossier" });
    }
    setCaseFileIds(ids);
    setAttachments(atts);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    Array.from(files).forEach((file) => {
      if (file.size > 3 * 1024 * 1024) {
        setErrors((p) => ({ ...p, attachments: `'${file.name}' is te groot (max 3 MB)` }));
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = (reader.result as string).split(",")[1];
        const id = `upload-${Date.now()}-${file.name}`;
        setInlineFiles((prev) => { const n = new Map(prev); n.set(id, { filename: file.name, data_base64: base64, content_type: file.type || "application/octet-stream" }); return n; });
        setAttachments((prev) => [...prev, { id, filename: file.name, size: file.size, source: "upload" }]);
      };
      reader.readAsDataURL(file);
    });
    e.target.value = "";
  };

  const removeAttachment = (id: string) => {
    setAttachments((p) => p.filter((a) => a.id !== id));
    setCaseFileIds((p) => { const n = new Set(p); n.delete(id); return n; });
    setInlineFiles((p) => { const n = new Map(p); n.delete(id); return n; });
  };

  // ── Library template handlers ────────────────────────────────────────

  const loadLibraryTemplates = async () => {
    if (libraryTemplates.length > 0) return;
    setLoadingLibrary(true);
    try {
      const res = await api("/api/documents/library-templates");
      if (res.ok) {
        const data = (await res.json()) as LibraryTemplate[];
        setLibraryTemplates(data);
      }
    } catch { /* ignore */ }
    setLoadingLibrary(false);
  };

  const attachLibraryTemplate = async (tpl: LibraryTemplate) => {
    if (!caseId) return;
    // Prevent duplicate attachment of the same template
    const dupId = `library-${tpl.template_key}`;
    if (attachments.some((a) => a.id === dupId)) return;

    setRenderingLibraryKey(tpl.template_key);
    setErrors((p) => ({ ...p, attachments: undefined as unknown as string }));
    try {
      const res = await api(`/api/documents/docx/cases/${caseId}/render-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ template_type: tpl.template_key }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setErrors((p) => ({ ...p, attachments: body.detail || "Renderen mislukt" }));
        return;
      }
      const data = await res.json() as {
        filename: string;
        data_base64: string;
        content_type: string;
        size: number;
      };
      setInlineFiles((prev) => {
        const n = new Map(prev);
        n.set(dupId, {
          filename: data.filename,
          data_base64: data.data_base64,
          content_type: data.content_type,
        });
        return n;
      });
      setAttachments((prev) => [
        ...prev,
        { id: dupId, filename: data.filename, size: data.size, source: "library" },
      ]);
    } catch {
      setErrors((p) => ({ ...p, attachments: "Renderen mislukt (netwerkfout)" }));
    }
    setRenderingLibraryKey(null);
  };

  // ── Other-case handlers ───────────────────────────────────────────────

  const searchOtherCases = async () => {
    if (!otherSearch.trim()) return;
    setLoadingOther(true);
    setOtherSelected(null);
    setOtherFiles([]);
    try {
      const res = await api(`/api/cases?search=${encodeURIComponent(otherSearch.trim())}&per_page=10`);
      if (res.ok) {
        const data = await res.json();
        setOtherResults(((data.items ?? data) as { id: string; case_number: string; description?: string }[])
          .filter((c) => c.id !== caseId)
          .map((c) => ({ id: c.id, case_number: c.case_number, description: c.description || "" })));
      }
    } catch { /* ignore */ }
    setLoadingOther(false);
  };

  const selectOtherCase = async (id: string) => {
    setOtherSelected(id);
    setLoadingOtherFiles(true);
    try {
      const res = await api(`/api/cases/${id}/files`);
      if (res.ok) { const data = await res.json(); setOtherFiles(data.items ?? data); }
    } catch { /* ignore */ }
    setLoadingOtherFiles(false);
  };

  const addOtherFile = async (f: CaseFileItem) => {
    if (!otherSelected) return;
    const id = `other-${otherSelected}-${f.id}`;
    try {
      const res = await api(`/api/cases/${otherSelected}/files/${f.id}/download`);
      if (!res.ok) return;
      const blob = await res.blob();
      if (blob.size > 3 * 1024 * 1024) { setErrors((p) => ({ ...p, attachments: `'${f.original_filename}' te groot (max 3 MB)` })); return; }
      const base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve((reader.result as string).split(",")[1]);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });
      setInlineFiles((prev) => { const n = new Map(prev); n.set(id, { filename: f.original_filename, data_base64: base64, content_type: f.content_type || "application/octet-stream" }); return n; });
      setAttachments((prev) => [...prev, { id, filename: f.original_filename, size: blob.size, source: "other" }]);
    } catch { /* ignore */ }
  };

  // ── Submit ────────────────────────────────────────────────────────────

  const buildEmailData = (): EmailComposeData | null => {
    const errs: Record<string, string> = {};
    if (!to.trim()) errs.to = "Vul een e-mailadres in";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(to.trim())) errs.to = "Ongeldig e-mailadres";
    if (!subject.trim()) errs.subject = "Vul een onderwerp in";
    if (Object.keys(errs).length > 0) { setErrors(errs); return null; }

    // Capture latest edits from contentEditable template editor
    const currentTemplateHtml = templateEditorRef.current?.innerHTML ?? templateHtml;

    return {
      recipient_email: to.trim(),
      recipient_name: toName.trim() || null,
      cc: ccList.length > 0 ? ccList : null,
      custom_subject: subject.trim() || null,
      custom_body: currentTemplateHtml ? null : (body.trim() || null),
      body_html: currentTemplateHtml || null,
      case_file_ids: Array.from(caseFileIds).length > 0 ? Array.from(caseFileIds) : undefined,
      inline_attachments: Array.from(inlineFiles.values()).length > 0 ? Array.from(inlineFiles.values()) : undefined,
    };
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data = buildEmailData();
    if (!data) return;
    // Primary action: direct send via Graph API if available, otherwise fallback
    if (onSendDirect) {
      onSendDirect(data);
    } else {
      onSend(data);
    }
  };

  const handleOpenInOutlook = () => {
    const data = buildEmailData();
    if (!data) return;
    onSend(data);
  };

  const validRecipients = recipients?.filter((r) => r.email) ?? [];
  const ccRecipients = validRecipients.filter((r) => r.email !== to && !ccList.includes(r.email));
  const isLoading = renderTemplate?.isPending ?? false;

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[95vw] w-full max-h-[92vh] h-[92vh] p-0 flex flex-col">
        {/* Header */}
        <DialogHeader className="px-6 pt-5 pb-3 shrink-0">
          <DialogTitle className="flex items-center gap-2 text-base">
            <Mail className="h-4 w-4 text-primary" />
            {title}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col flex-1 min-h-0">
          <div className="px-6 space-y-3 shrink-0">
            {/* ── Aan (To) ─────────────────────────────────────────── */}
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground w-12 shrink-0">Aan</span>
                <div className="flex-1 flex flex-wrap items-center gap-1.5 min-h-[36px] rounded-md border border-input bg-background px-3 py-1.5 focus-within:ring-1 focus-within:ring-ring">
                  {/* Selected recipient chip */}
                  {to && selectedChip && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 text-primary px-2.5 py-0.5 text-xs font-medium">
                      {toName || to}
                      <button type="button" onClick={() => { setTo(""); setToName(""); setSelectedChip(null); }} className="hover:text-destructive">
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  )}
                  {/* Input (hidden when chip selected) */}
                  {!selectedChip && (
                    <input
                      type="email"
                      placeholder="E-mailadres..."
                      value={to}
                      onChange={(e) => { setTo(e.target.value); if (errors.to) setErrors((p) => { const n = { ...p }; delete n.to; return n; }); }}
                      className="flex-1 min-w-[120px] bg-transparent text-sm outline-none placeholder:text-muted-foreground"
                    />
                  )}
                </div>
                <button type="button" onClick={() => setShowCc(!showCc)} className={cn("text-xs font-medium px-2 py-1 rounded hover:bg-muted transition-colors", showCc ? "text-primary" : "text-muted-foreground")}>
                  CC
                </button>
              </div>
              {errors.to && <p className="text-xs text-destructive ml-14">{errors.to}</p>}

              {/* Quick-select chips (only when no recipient selected) */}
              {!selectedChip && validRecipients.length > 0 && (
                <div className="flex flex-wrap gap-1.5 ml-14">
                  {validRecipients.map((r) => (
                    <button
                      key={r.email}
                      type="button"
                      onClick={() => selectRecipient(r)}
                      className="inline-flex items-center gap-1 rounded-full border border-dashed border-muted-foreground/40 px-2.5 py-0.5 text-[11px] text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
                    >
                      <Plus className="h-2.5 w-2.5" />
                      {r.name}
                      <span className="opacity-60">{ROLE_LABELS[r.role] ?? r.role}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* ── CC ───────────────────────────────────────────────── */}
            {showCc && (
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground w-12 shrink-0">CC</span>
                  <div className="flex-1 flex flex-wrap items-center gap-1.5 min-h-[36px] rounded-md border border-input bg-background px-3 py-1.5 focus-within:ring-1 focus-within:ring-ring">
                    {ccList.map((email) => (
                      <span key={email} className="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium">
                        {email}
                        <button type="button" onClick={() => setCcList(ccList.filter((e) => e !== email))} className="hover:text-destructive">
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                    <input
                      type="email"
                      placeholder={ccList.length ? "" : "E-mailadres..."}
                      value={ccInput}
                      onChange={(e) => setCcInput(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter" || e.key === ",") { e.preventDefault(); addCc(); } }}
                      className="flex-1 min-w-[80px] bg-transparent text-sm outline-none placeholder:text-muted-foreground"
                    />
                  </div>
                </div>
                {/* CC quick-select */}
                {ccRecipients.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 ml-14">
                    {ccRecipients.map((r) => (
                      <button key={`cc-${r.email}`} type="button" onClick={() => addCcFromRecipient(r)}
                        className="inline-flex items-center gap-1 rounded-full border border-dashed border-muted-foreground/40 px-2.5 py-0.5 text-[11px] text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer">
                        <Plus className="h-2.5 w-2.5" />
                        {r.name}
                        <span className="opacity-60">{ROLE_LABELS[r.role] ?? r.role}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* ── Divider ─────────────────────────────────────────── */}
            <div className="border-t border-border" />

            {/* ── Onderwerp ────────────────────────────────────────── */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground w-12 shrink-0">Betreft</span>
              <input
                type="text"
                placeholder="Onderwerp..."
                value={subject}
                onChange={(e) => { setSubject(e.target.value); if (errors.subject) setErrors((p) => { const n = { ...p }; delete n.subject; return n; }); }}
                className={cn("flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground", errors.subject && "text-destructive")}
              />
            </div>
            {errors.subject && <p className="text-xs text-destructive ml-14">{errors.subject}</p>}

            {/* ── Template selector ────────────────────────────────── */}
            {caseId && templates.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground w-12 shrink-0">Sjabloon</span>
                <Select value={selectedTemplate} onValueChange={handleTemplateSelect}>
                  <SelectTrigger className="flex-1 h-8 text-sm">
                    <SelectValue placeholder="Geen sjabloon" />
                  </SelectTrigger>
                  <SelectContent>
                    {templates.map((t) => (
                      <SelectItem key={t.template_type} value={t.template_type}>
                        {TEMPLATE_LABELS[t.template_type] ?? t.template_type}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedTemplate && (
                  <button type="button" onClick={() => { setSelectedTemplate(""); setTemplateHtml(null); }} className="text-xs text-muted-foreground hover:text-foreground">
                    Wissen
                  </button>
                )}
              </div>
            )}

            {/* ── Divider ─────────────────────────────────────────── */}
            <div className="border-t border-border" />
          </div>

          {/* ── Body ──────────────────────────────────────────────── */}
          <div className="px-6 py-2 flex-1 min-h-0 flex flex-col">
            {isLoading ? (
              <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground flex-1">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Sjabloon laden...</span>
              </div>
            ) : templateHtml ? (
              <div
                ref={templateEditorRef}
                contentEditable
                suppressContentEditableWarning
                dangerouslySetInnerHTML={{ __html: templateHtml }}
                onBlur={() => {
                  if (templateEditorRef.current) {
                    setTemplateHtml(templateEditorRef.current.innerHTML);
                  }
                }}
                className="rounded-md border border-input bg-background p-4 text-sm overflow-y-auto flex-1 min-h-0 focus:outline-none focus:ring-1 focus:ring-ring prose prose-sm max-w-none"
              />
            ) : (
              <Textarea
                placeholder="Typ uw bericht..."
                value={body}
                onChange={(e) => setBody(e.target.value)}
                className="resize-none border-0 shadow-none focus-visible:ring-0 px-0 text-sm flex-1"
              />
            )}
          </div>

          {/* ── Attachments ───────────────────────────────────────── */}
          <div className="px-6 pb-3 space-y-2 shrink-0">
            {/* Attachment chips */}
            {attachments.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {attachments.map((att) => (
                  <span key={att.id} className="inline-flex items-center gap-1.5 rounded-md bg-muted/80 px-2.5 py-1 text-xs">
                    <Paperclip className="h-3 w-3 text-muted-foreground" />
                    <span className="max-w-[140px] truncate">{att.filename}</span>
                    <span className="text-muted-foreground">{formatSize(att.size)}</span>
                    <button type="button" onClick={() => removeAttachment(att.id)} className="hover:text-destructive ml-0.5">
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}

            {/* Legacy indicator */}
            {attachmentName && !caseId && (
              <div className="flex items-center gap-2 rounded-md bg-muted/50 px-3 py-1.5 text-xs">
                <Paperclip className="h-3 w-3 text-muted-foreground" />
                <span className="text-muted-foreground">Bijlage: <span className="font-medium text-foreground">{attachmentName}</span></span>
              </div>
            )}

            {/* File picker panel */}
            {showFilePicker && (
              <div className="rounded-md border p-3 space-y-2 bg-muted/20 text-xs">
                <p className="font-medium text-muted-foreground">Bestanden in dit dossier</p>
                {loadingFiles ? (
                  <div className="flex items-center gap-2 py-2 text-muted-foreground">
                    <Loader2 className="h-3 w-3 animate-spin" /> Laden...
                  </div>
                ) : caseFiles.length === 0 ? (
                  <p className="text-muted-foreground py-1">Geen bestanden</p>
                ) : (
                  <div className="space-y-0.5 max-h-[120px] overflow-y-auto">
                    {caseFiles.map((f) => (
                      <label key={f.id} className={cn("flex items-center gap-2 rounded px-2 py-1 cursor-pointer hover:bg-muted transition-colors", caseFileIds.has(f.id) && "bg-primary/5")}>
                        <input type="checkbox" checked={caseFileIds.has(f.id)} onChange={() => toggleCaseFile(f)} className="rounded border-border" />
                        <FileText className="h-3 w-3 text-muted-foreground shrink-0" />
                        <span className="truncate flex-1">{f.original_filename}</span>
                        <span className="text-muted-foreground shrink-0">{formatSize(f.file_size)}</span>
                      </label>
                    ))}
                  </div>
                )}
                <button type="button" onClick={() => setShowFilePicker(false)} className="text-muted-foreground hover:text-foreground text-xs">Sluiten</button>
              </div>
            )}

            {/* Other-case picker */}
            {showOtherCase && (
              <div className="rounded-md border p-3 space-y-2 bg-muted/20 text-xs">
                <p className="font-medium text-muted-foreground">Bestand uit ander dossier</p>
                <div className="flex gap-2">
                  <Input placeholder="Zoek dossier..." value={otherSearch} onChange={(e) => setOtherSearch(e.target.value)}
                    onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); searchOtherCases(); } }} className="flex-1 h-7 text-xs" />
                  <Button type="button" variant="outline" size="sm" className="h-7 text-xs" onClick={searchOtherCases} disabled={loadingOther || !otherSearch.trim()}>
                    {loadingOther ? <Loader2 className="h-3 w-3 animate-spin" /> : "Zoeken"}
                  </Button>
                </div>
                {otherResults.length > 0 && !otherSelected && (
                  <div className="space-y-0.5 max-h-[100px] overflow-y-auto">
                    {otherResults.map((c) => (
                      <button key={c.id} type="button" onClick={() => selectOtherCase(c.id)}
                        className="w-full flex items-center gap-2 rounded px-2 py-1 text-left hover:bg-muted transition-colors">
                        <FolderSearch className="h-3 w-3 text-muted-foreground shrink-0" />
                        <span className="font-medium">{c.case_number}</span>
                        <span className="text-muted-foreground truncate">{c.description}</span>
                      </button>
                    ))}
                  </div>
                )}
                {otherSelected && (
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">Dossier: <span className="font-medium text-foreground">{otherResults.find((c) => c.id === otherSelected)?.case_number}</span></span>
                      <button type="button" onClick={() => { setOtherSelected(null); setOtherFiles([]); }} className="text-primary text-[10px] hover:underline">Wijzig</button>
                    </div>
                    {loadingOtherFiles ? (
                      <div className="flex items-center gap-2 py-1 text-muted-foreground"><Loader2 className="h-3 w-3 animate-spin" /> Laden...</div>
                    ) : otherFiles.length === 0 ? (
                      <p className="text-muted-foreground">Geen bestanden</p>
                    ) : (
                      <div className="space-y-0.5 max-h-[100px] overflow-y-auto">
                        {otherFiles.map((f) => {
                          const added = attachments.some((a) => a.id === `other-${otherSelected}-${f.id}`);
                          return (
                            <button key={f.id} type="button" onClick={() => !added && addOtherFile(f)} disabled={added}
                              className={cn("w-full flex items-center gap-2 rounded px-2 py-1 text-left hover:bg-muted transition-colors", added && "opacity-40")}>
                              <FileText className="h-3 w-3 text-muted-foreground shrink-0" />
                              <span className="truncate flex-1">{f.original_filename}</span>
                              <span className="text-muted-foreground shrink-0">{formatSize(f.file_size)}</span>
                              {added && <span className="text-primary text-[10px]">✓</span>}
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
                <button type="button" onClick={() => setShowOtherCase(false)} className="text-muted-foreground hover:text-foreground text-xs">Sluiten</button>
              </div>
            )}

            {/* Library picker panel */}
            {showLibrary && (
              <div className="rounded-md border p-3 space-y-2 bg-muted/20 text-xs">
                <p className="font-medium text-muted-foreground">Sjablonen-bibliotheek (wordt als PDF bijgevoegd)</p>
                {loadingLibrary ? (
                  <div className="flex items-center gap-2 py-2 text-muted-foreground">
                    <Loader2 className="h-3 w-3 animate-spin" /> Laden...
                  </div>
                ) : libraryTemplates.length === 0 ? (
                  <p className="text-muted-foreground py-1">Geen sjablonen beschikbaar</p>
                ) : (
                  <div className="space-y-0.5 max-h-[180px] overflow-y-auto">
                    {libraryTemplates.map((tpl) => {
                      const dupId = `library-${tpl.template_key}`;
                      const added = attachments.some((a) => a.id === dupId);
                      const rendering = renderingLibraryKey === tpl.template_key;
                      return (
                        <button
                          key={tpl.template_key}
                          type="button"
                          disabled={added || rendering}
                          onClick={() => attachLibraryTemplate(tpl)}
                          className={cn(
                            "w-full flex items-start gap-2 rounded px-2 py-2 text-left hover:bg-muted transition-colors",
                            (added || rendering) && "opacity-50 cursor-not-allowed",
                          )}
                        >
                          <BookMarked className="h-3.5 w-3.5 text-muted-foreground shrink-0 mt-0.5" />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium truncate">{tpl.name}</div>
                            {tpl.description && (
                              <div className="text-muted-foreground text-[11px] truncate">{tpl.description}</div>
                            )}
                          </div>
                          {rendering && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground shrink-0" />}
                          {added && <span className="text-primary text-[10px] shrink-0">✓</span>}
                        </button>
                      );
                    })}
                  </div>
                )}
                <button type="button" onClick={() => setShowLibrary(false)} className="text-muted-foreground hover:text-foreground text-xs">Sluiten</button>
              </div>
            )}

            {errors.attachments && <p className="text-xs text-destructive">{errors.attachments}</p>}
          </div>

          {/* ── Footer ────────────────────────────────────────────── */}
          <div className="border-t px-6 py-3 flex items-center justify-between shrink-0">
            {/* Left: attachments button */}
            {caseId && (
              <div className="flex items-center gap-2">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button type="button" variant="ghost" size="sm" className="h-8 gap-1.5 text-xs text-muted-foreground">
                      <Paperclip className="h-3.5 w-3.5" />
                      {attachments.length > 0 ? `Bijlagen (${attachments.length})` : "Bijlage"}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start">
                    <DropdownMenuItem onClick={() => { setShowFilePicker(true); setShowOtherCase(false); setShowLibrary(false); loadCaseFiles(); }}>
                      <FileText className="h-4 w-4 mr-2" /> Uit dit dossier
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => fileInputRef.current?.click()}>
                      <Upload className="h-4 w-4 mr-2" /> Uploaden
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => { setShowOtherCase(true); setShowFilePicker(false); setShowLibrary(false); }}>
                      <FolderSearch className="h-4 w-4 mr-2" /> Ander dossier
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => { setShowLibrary(true); setShowFilePicker(false); setShowOtherCase(false); loadLibraryTemplates(); }}>
                      <BookMarked className="h-4 w-4 mr-2" /> Uit sjablonen-bibliotheek
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                <input ref={fileInputRef} type="file" multiple className="hidden" onChange={handleFileUpload} />
              </div>
            )}

            {/* Right: cancel + outlook + send */}
            <div className="flex items-center gap-2 ml-auto">
              <Button type="button" variant="ghost" size="sm" onClick={() => handleOpenChange(false)} disabled={isSending}>
                Annuleren
              </Button>
              {caseId && (
                <Button type="button" variant="outline" size="sm" disabled={isSending || !to.trim()} className="gap-1.5" onClick={handleOpenInOutlook}>
                  <ExternalLink className="h-3.5 w-3.5" /> Open in Outlook
                </Button>
              )}
              <Button type="submit" size="sm" disabled={isSending || !to.trim()} className="gap-1.5">
                {isSending ? (
                  <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Bezig...</>
                ) : (
                  <><Mail className="h-3.5 w-3.5" /> Versturen</>
                )}
              </Button>
            </div>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
