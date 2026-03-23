"use client";

import { useEffect, useRef, useState } from "react";
import {
  Mail, Paperclip, Loader2, X, Plus, User,
  ExternalLink, FileText, Upload, FolderSearch, Trash2,
} from "lucide-react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
  DialogDescription, DialogFooter,
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

/** A known recipient from the case (client, opposing party, etc.) */
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
  created_at: string;
}

interface TemplateInfo {
  template_type: string;
  filename: string;
  available: boolean;
}

interface AttachmentRef {
  id: string;
  filename: string;
  size: number;
  source: "dossier" | "upload" | "other";
}

// ── Dutch role labels ───────────────────────────────────────────────────────

const ROLE_LABELS: Record<string, string> = {
  client: "Cliënt",
  opposing_party: "Wederpartij",
  advocaat_wederpartij: "Advocaat wederpartij",
  deurwaarder: "Deurwaarder",
  rechtbank: "Rechtbank",
  mediator: "Mediator",
  deskundige: "Deskundige",
  getuige: "Getuige",
  notaris: "Notaris",
  overig: "Overig",
};

function getRoleLabel(role: string): string {
  return ROLE_LABELS[role] ?? role;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const TEMPLATE_LABELS: Record<string, string> = {
  aanmaning: "Aanmaning",
  sommatie: "Sommatie",
  tweede_sommatie: "Tweede sommatie",
  "14_dagenbrief": "14-dagenbrief",
  herinnering: "Herinnering",
  dagvaarding: "Dagvaarding",
  renteoverzicht: "Renteoverzicht",
};

// ── Props ────────────────────────────────────────────────────────────────────

export interface EmailComposeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSend: (data: EmailComposeData) => void;
  isSending?: boolean;
  defaultTo?: string;
  defaultToName?: string;
  defaultSubject?: string;
  defaultBody?: string;
  attachmentName?: string;
  title?: string;
  recipients?: EmailRecipient[];
  /** Case ID — enables template selector + file picker */
  caseId?: string;
}

// ── Component ────────────────────────────────────────────────────────────────

export function EmailComposeDialog({
  open,
  onOpenChange,
  onSend,
  isSending = false,
  defaultTo = "",
  defaultToName = "",
  defaultSubject = "",
  defaultBody = "",
  attachmentName,
  title = "E-mail opstellen",
  recipients,
  caseId,
}: EmailComposeDialogProps) {
  const [to, setTo] = useState(defaultTo);
  const [toName, setToName] = useState(defaultToName);
  const [ccList, setCcList] = useState<string[]>([]);
  const [ccInput, setCcInput] = useState("");
  const [showCc, setShowCc] = useState(false);
  const [subject, setSubject] = useState(defaultSubject);
  const [body, setBody] = useState(defaultBody);
  const [selectedRecipientEmail, setSelectedRecipientEmail] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Template state
  const [selectedTemplate, setSelectedTemplate] = useState<string>("");
  const [templateHtml, setTemplateHtml] = useState<string | null>(null);
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const renderTemplate = caseId ? useRenderTemplate(caseId) : null;

  // Attachment state
  const [attachments, setAttachments] = useState<AttachmentRef[]>([]);
  const [inlineFiles, setInlineFiles] = useState<Map<string, ComposeInlineAttachment>>(new Map());
  const [caseFileIds, setCaseFileIds] = useState<Set<string>>(new Set());
  const [showFilePicker, setShowFilePicker] = useState(false);
  const [caseFiles, setCaseFiles] = useState<CaseFileItem[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // "Ander dossier" state
  const [showOtherCase, setShowOtherCase] = useState(false);
  const [otherCaseSearch, setOtherCaseSearch] = useState("");
  const [otherCaseResults, setOtherCaseResults] = useState<{ id: string; case_number: string; description: string }[]>([]);
  const [otherCaseSelected, setOtherCaseSelected] = useState<string | null>(null);
  const [otherCaseFiles, setOtherCaseFiles] = useState<CaseFileItem[]>([]);
  const [loadingOtherCase, setLoadingOtherCase] = useState(false);
  const [loadingOtherFiles, setLoadingOtherFiles] = useState(false);

  // Load templates list when dialog opens
  useEffect(() => {
    if (open && caseId && templates.length === 0) {
      api("/api/documents/docx/templates")
        .then((r) => r.ok ? r.json() : [])
        .then((data: TemplateInfo[]) => setTemplates(data.filter((t) => t.available)))
        .catch(() => {});
    }
  }, [open, caseId]);

  // Reset form when dialog opens
  const handleOpenChange = (nextOpen: boolean) => {
    if (nextOpen) {
      setTo(defaultTo);
      setToName(defaultToName);
      setCcList([]);
      setCcInput("");
      setShowCc(false);
      setSubject(defaultSubject);
      setBody(defaultBody);
      setSelectedRecipientEmail(null);
      setFieldErrors({});
      setSelectedTemplate("");
      setTemplateHtml(null);
      setAttachments([]);
      setInlineFiles(new Map());
      setCaseFileIds(new Set());
      setShowFilePicker(false);
      setShowOtherCase(false);
      setOtherCaseSearch("");
      setOtherCaseResults([]);
      setOtherCaseSelected(null);
      setOtherCaseFiles([]);
    }
    onOpenChange(nextOpen);
  };

  const selectRecipient = (recipient: EmailRecipient) => {
    if (selectedRecipientEmail === recipient.email) {
      setTo("");
      setToName("");
      setSelectedRecipientEmail(null);
    } else {
      setTo(recipient.email);
      setToName(recipient.name);
      setSelectedRecipientEmail(recipient.email);
    }
  };

  const addCc = () => {
    const email = ccInput.trim();
    if (email && !ccList.includes(email)) {
      setCcList([...ccList, email]);
      setCcInput("");
    }
  };

  const removeCc = (email: string) => {
    setCcList(ccList.filter((e) => e !== email));
  };

  const handleCcKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addCc();
    }
  };

  // ── Template handling ─────────────────────────────────────────────────

  const handleTemplateSelect = async (templateType: string) => {
    if (!templateType || !caseId || !renderTemplate) {
      setSelectedTemplate("");
      setTemplateHtml(null);
      return;
    }
    setSelectedTemplate(templateType);
    try {
      const result = await renderTemplate.mutateAsync({ template_type: templateType });
      if (result.supported && result.body_html) {
        setTemplateHtml(result.body_html);
        if (result.subject && !subject) {
          setSubject(result.subject);
        }
      } else {
        setSelectedTemplate("");
        setTemplateHtml(null);
      }
    } catch {
      setSelectedTemplate("");
      setTemplateHtml(null);
    }
  };

  const clearTemplate = () => {
    setSelectedTemplate("");
    setTemplateHtml(null);
  };

  // ── File picker ───────────────────────────────────────────────────────

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

  const toggleFilePicker = () => {
    if (!showFilePicker) loadCaseFiles();
    setShowFilePicker(!showFilePicker);
  };

  const toggleCaseFile = (file: CaseFileItem) => {
    const newIds = new Set(caseFileIds);
    const newAtts = [...attachments];
    if (newIds.has(file.id)) {
      newIds.delete(file.id);
      const idx = newAtts.findIndex((a) => a.id === file.id);
      if (idx >= 0) newAtts.splice(idx, 1);
    } else {
      newIds.add(file.id);
      newAtts.push({
        id: file.id,
        filename: file.original_filename,
        size: file.file_size,
        source: "dossier",
      });
    }
    setCaseFileIds(newIds);
    setAttachments(newAtts);
  };

  // ── Upload handling ───────────────────────────────────────────────────

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    Array.from(files).forEach((file) => {
      if (file.size > 3 * 1024 * 1024) {
        setFieldErrors((prev) => ({
          ...prev,
          attachments: `'${file.name}' is te groot (max 3 MB)`,
        }));
        return;
      }

      const reader = new FileReader();
      reader.onload = () => {
        const base64 = (reader.result as string).split(",")[1];
        const id = `upload-${Date.now()}-${file.name}`;

        setInlineFiles((prev) => {
          const next = new Map(prev);
          next.set(id, {
            filename: file.name,
            data_base64: base64,
            content_type: file.type || "application/octet-stream",
          });
          return next;
        });

        setAttachments((prev) => [
          ...prev,
          { id, filename: file.name, size: file.size, source: "upload" },
        ]);
      };
      reader.readAsDataURL(file);
    });

    // Reset input so same file can be selected again
    e.target.value = "";
  };

  const removeAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((a) => a.id !== id));
    setCaseFileIds((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
    setInlineFiles((prev) => {
      const next = new Map(prev);
      next.delete(id);
      return next;
    });
    if (fieldErrors.attachments) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next.attachments;
        return next;
      });
    }
  };

  // ── Other case file picker ─────────────────────────────────────────

  const searchOtherCases = async () => {
    if (!otherCaseSearch.trim()) return;
    setLoadingOtherCase(true);
    setOtherCaseSelected(null);
    setOtherCaseFiles([]);
    try {
      const res = await api(`/api/cases?search=${encodeURIComponent(otherCaseSearch.trim())}&per_page=10`);
      if (res.ok) {
        const data = await res.json();
        const items = (data.items ?? data) as { id: string; case_number: string; description?: string }[];
        // Filter out current case
        setOtherCaseResults(items.filter((c) => c.id !== caseId).map((c) => ({
          id: c.id,
          case_number: c.case_number,
          description: c.description || "",
        })));
      }
    } catch { /* ignore */ }
    setLoadingOtherCase(false);
  };

  const selectOtherCase = async (otherCaseId: string) => {
    setOtherCaseSelected(otherCaseId);
    setLoadingOtherFiles(true);
    try {
      const res = await api(`/api/cases/${otherCaseId}/files`);
      if (res.ok) {
        const data = await res.json();
        setOtherCaseFiles(data.items ?? data);
      }
    } catch { /* ignore */ }
    setLoadingOtherFiles(false);
  };

  const addOtherCaseFile = async (file: CaseFileItem) => {
    if (!otherCaseSelected) return;
    const id = `other-${otherCaseSelected}-${file.id}`;

    try {
      const res = await api(`/api/cases/${otherCaseSelected}/files/${file.id}/download`);
      if (!res.ok) {
        setFieldErrors((prev) => ({ ...prev, attachments: `Kan '${file.original_filename}' niet downloaden` }));
        return;
      }
      const blob = await res.blob();
      if (blob.size > 3 * 1024 * 1024) {
        setFieldErrors((prev) => ({ ...prev, attachments: `'${file.original_filename}' is te groot (max 3 MB)` }));
        return;
      }

      // Read as base64
      const base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve((reader.result as string).split(",")[1]);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });

      setInlineFiles((prev) => {
        const next = new Map(prev);
        next.set(id, {
          filename: file.original_filename,
          data_base64: base64,
          content_type: file.content_type || "application/octet-stream",
        });
        return next;
      });
      setAttachments((prev) => [
        ...prev,
        { id, filename: file.original_filename, size: blob.size, source: "other" },
      ]);
    } catch {
      setFieldErrors((prev) => ({ ...prev, attachments: `Fout bij downloaden '${file.original_filename}'` }));
    }
  };

  // ── Submit ────────────────────────────────────────────────────────────

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const errors: Record<string, string> = {};
    if (!to.trim()) {
      errors.to = "E-mailadres is verplicht";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(to.trim())) {
      errors.to = "Ongeldig e-mailadres";
    }
    if (!subject.trim()) {
      errors.subject = "Onderwerp is verplicht";
    }
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    const fileIds = Array.from(caseFileIds);
    const uploads = Array.from(inlineFiles.values());

    onSend({
      recipient_email: to.trim(),
      recipient_name: toName.trim() || null,
      cc: ccList.length > 0 ? ccList : null,
      custom_subject: subject.trim() || null,
      custom_body: templateHtml ? null : (body.trim() || null),
      body_html: templateHtml || null,
      case_file_ids: fileIds.length > 0 ? fileIds : undefined,
      inline_attachments: uploads.length > 0 ? uploads : undefined,
    });
  };

  const validRecipients = recipients?.filter((r) => r.email) ?? [];
  const isTemplateLoading = renderTemplate?.isPending ?? false;

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[680px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5 text-primary" />
            {title}
          </DialogTitle>
          <DialogDescription>
            Stel de e-mail samen en open in Outlook
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Recipient quick-select chips */}
          {validRecipients.length > 0 && (
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Snelkeuze ontvanger</Label>
              <div className="flex flex-wrap gap-1.5">
                {validRecipients.map((r) => (
                  <button
                    key={r.email}
                    type="button"
                    onClick={() => selectRecipient(r)}
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors",
                      "border cursor-pointer",
                      selectedRecipientEmail === r.email
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-background text-foreground border-border hover:bg-muted"
                    )}
                  >
                    <User className="h-3 w-3" />
                    <span>{r.name}</span>
                    <span className="text-[10px] opacity-70">
                      {getRoleLabel(r.role)}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Aan */}
          <div className="space-y-1.5">
            <Label htmlFor="email-to">Aan *</Label>
            <div className="flex gap-2">
              <Input
                id="email-to"
                type="email"
                placeholder="email@voorbeeld.nl"
                value={to}
                onChange={(e) => {
                  setTo(e.target.value);
                  if (fieldErrors.to) setFieldErrors((p) => { const n = { ...p }; delete n.to; return n; });
                  if (selectedRecipientEmail && e.target.value !== selectedRecipientEmail) {
                    setSelectedRecipientEmail(null);
                  }
                }}
                required
                className={cn("flex-1", fieldErrors.to && "border-destructive ring-1 ring-destructive/30")}
              />
              {!showCc && (
                <Button type="button" variant="ghost" size="sm" onClick={() => setShowCc(true)} className="text-xs text-muted-foreground">
                  CC
                </Button>
              )}
            </div>
            {fieldErrors.to && <p className="text-[13px] text-destructive">{fieldErrors.to}</p>}
          </div>

          {/* Naam ontvanger */}
          <div className="space-y-1.5">
            <Label htmlFor="email-to-name">Naam ontvanger</Label>
            <Input
              id="email-to-name"
              placeholder="Naam (voor aanhef)"
              value={toName}
              onChange={(e) => setToName(e.target.value)}
            />
          </div>

          {/* CC */}
          {showCc && (
            <div className="space-y-1.5">
              <Label>CC</Label>
              {/* CC quick-select chips */}
              {validRecipients.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {validRecipients
                    .filter((r) => r.email !== to && !ccList.includes(r.email))
                    .map((r) => (
                      <button
                        key={`cc-${r.email}`}
                        type="button"
                        onClick={() => {
                          if (!ccList.includes(r.email)) {
                            setCcList([...ccList, r.email]);
                          }
                        }}
                        className="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-medium border border-dashed border-border text-muted-foreground hover:bg-muted hover:text-foreground transition-colors cursor-pointer"
                      >
                        <Plus className="h-2.5 w-2.5" />
                        {r.name}
                        <span className="text-[10px] opacity-70">{getRoleLabel(r.role)}</span>
                      </button>
                    ))}
                </div>
              )}
              {ccList.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {ccList.map((email) => (
                    <span key={email} className="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-foreground">
                      {email}
                      <button type="button" onClick={() => removeCc(email)} className="rounded-full p-0.5 hover:bg-destructive/10 hover:text-destructive">
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
              <div className="flex gap-2">
                <Input type="email" placeholder="cc@voorbeeld.nl" value={ccInput} onChange={(e) => setCcInput(e.target.value)} onKeyDown={handleCcKeyDown} className="flex-1" />
                <Button type="button" variant="outline" size="icon" onClick={addCc} disabled={!ccInput.trim()}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">Druk op Enter of komma om toe te voegen</p>
            </div>
          )}

          {/* Onderwerp */}
          <div className="space-y-1.5">
            <Label htmlFor="email-subject">Onderwerp *</Label>
            <Input
              id="email-subject"
              placeholder="Onderwerp van de e-mail"
              value={subject}
              onChange={(e) => {
                setSubject(e.target.value);
                if (fieldErrors.subject) setFieldErrors((p) => { const n = { ...p }; delete n.subject; return n; });
              }}
              className={cn(fieldErrors.subject && "border-destructive ring-1 ring-destructive/30")}
            />
            {fieldErrors.subject && <p className="text-[13px] text-destructive">{fieldErrors.subject}</p>}
          </div>

          {/* Template selector */}
          {caseId && templates.length > 0 && (
            <div className="space-y-1.5">
              <Label>Template</Label>
              <div className="flex gap-2">
                <Select value={selectedTemplate} onValueChange={handleTemplateSelect}>
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Geen template (vrije tekst)" />
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
                  <Button type="button" variant="ghost" size="sm" onClick={clearTemplate} className="text-xs text-muted-foreground">
                    Wis template
                  </Button>
                )}
              </div>
            </div>
          )}

          {/* Body — template preview OR free text */}
          {isTemplateLoading ? (
            <div className="flex items-center justify-center gap-2 py-8 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Template laden...</span>
            </div>
          ) : templateHtml ? (
            <div className="space-y-1.5">
              <Label>Bericht (template)</Label>
              <div className="rounded-lg border border-border overflow-hidden">
                <iframe
                  srcDoc={templateHtml}
                  className="w-full border-0"
                  style={{ height: "300px" }}
                  sandbox="allow-same-origin"
                  title="Template preview"
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Template wordt als e-mail body verstuurd. Klik &quot;Wis template&quot; voor vrije tekst.
              </p>
            </div>
          ) : (
            <div className="space-y-1.5">
              <Label htmlFor="email-body">Bericht</Label>
              <Textarea
                id="email-body"
                placeholder="Typ hier uw bericht..."
                value={body}
                onChange={(e) => setBody(e.target.value)}
                rows={6}
                className="resize-y"
              />
            </div>
          )}

          {/* Legacy attachment indicator */}
          {attachmentName && !caseId && (
            <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/50 px-3 py-2">
              <Paperclip className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                Bijlage: <span className="font-medium text-foreground">{attachmentName}</span>
              </span>
            </div>
          )}

          {/* Attachments section */}
          {caseId && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Label>Bijlagen</Label>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button type="button" variant="outline" size="sm" className="h-7 gap-1 text-xs">
                      <Plus className="h-3 w-3" />
                      Bijlage toevoegen
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start">
                    <DropdownMenuItem onClick={toggleFilePicker}>
                      <FileText className="h-4 w-4 mr-2" />
                      Uit dit dossier
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => fileInputRef.current?.click()}>
                      <Upload className="h-4 w-4 mr-2" />
                      Bestand uploaden
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => { setShowOtherCase(true); setShowFilePicker(false); }}>
                      <FolderSearch className="h-4 w-4 mr-2" />
                      Uit ander dossier
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  className="hidden"
                  onChange={handleFileUpload}
                />
              </div>

              {/* File picker panel */}
              {showFilePicker && (
                <div className="rounded-lg border border-border p-3 space-y-2 bg-muted/30">
                  <p className="text-xs font-medium text-muted-foreground">Bestanden in dit dossier</p>
                  {loadingFiles ? (
                    <div className="flex items-center gap-2 py-2 text-muted-foreground">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      <span className="text-xs">Laden...</span>
                    </div>
                  ) : caseFiles.length === 0 ? (
                    <p className="text-xs text-muted-foreground py-2">Geen bestanden in dit dossier</p>
                  ) : (
                    <div className="space-y-1 max-h-[150px] overflow-y-auto">
                      {caseFiles.map((f) => (
                        <label
                          key={f.id}
                          className={cn(
                            "flex items-center gap-2 rounded px-2 py-1.5 text-xs cursor-pointer hover:bg-muted transition-colors",
                            caseFileIds.has(f.id) && "bg-primary/10"
                          )}
                        >
                          <input
                            type="checkbox"
                            checked={caseFileIds.has(f.id)}
                            onChange={() => toggleCaseFile(f)}
                            className="rounded border-border"
                          />
                          <FileText className="h-3 w-3 text-muted-foreground shrink-0" />
                          <span className="truncate flex-1">{f.original_filename}</span>
                          <span className="text-muted-foreground shrink-0">{formatFileSize(f.file_size)}</span>
                        </label>
                      ))}
                    </div>
                  )}
                  <Button type="button" variant="ghost" size="sm" onClick={() => setShowFilePicker(false)} className="text-xs">
                    Sluiten
                  </Button>
                </div>
              )}

              {/* Other case file picker */}
              {showOtherCase && (
                <div className="rounded-lg border border-border p-3 space-y-2 bg-muted/30">
                  <p className="text-xs font-medium text-muted-foreground">Bestand uit ander dossier</p>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Zoek op dossiernummer of naam..."
                      value={otherCaseSearch}
                      onChange={(e) => setOtherCaseSearch(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); searchOtherCases(); } }}
                      className="flex-1 h-8 text-xs"
                    />
                    <Button type="button" variant="outline" size="sm" className="h-8 text-xs" onClick={searchOtherCases} disabled={loadingOtherCase || !otherCaseSearch.trim()}>
                      {loadingOtherCase ? <Loader2 className="h-3 w-3 animate-spin" /> : "Zoeken"}
                    </Button>
                  </div>

                  {/* Case results */}
                  {otherCaseResults.length > 0 && !otherCaseSelected && (
                    <div className="space-y-1 max-h-[120px] overflow-y-auto">
                      {otherCaseResults.map((c) => (
                        <button
                          key={c.id}
                          type="button"
                          onClick={() => selectOtherCase(c.id)}
                          className="w-full flex items-center gap-2 rounded px-2 py-1.5 text-xs text-left hover:bg-muted transition-colors"
                        >
                          <FolderSearch className="h-3 w-3 text-muted-foreground shrink-0" />
                          <span className="font-medium">{c.case_number}</span>
                          <span className="text-muted-foreground truncate">{c.description}</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Files from selected other case */}
                  {otherCaseSelected && (
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <p className="text-xs text-muted-foreground">
                          Dossier: <span className="font-medium text-foreground">{otherCaseResults.find((c) => c.id === otherCaseSelected)?.case_number}</span>
                        </p>
                        <Button type="button" variant="ghost" size="sm" className="h-5 text-[10px] px-1.5" onClick={() => { setOtherCaseSelected(null); setOtherCaseFiles([]); }}>
                          Wijzig
                        </Button>
                      </div>
                      {loadingOtherFiles ? (
                        <div className="flex items-center gap-2 py-2 text-muted-foreground">
                          <Loader2 className="h-3 w-3 animate-spin" />
                          <span className="text-xs">Bestanden laden...</span>
                        </div>
                      ) : otherCaseFiles.length === 0 ? (
                        <p className="text-xs text-muted-foreground py-1">Geen bestanden in dit dossier</p>
                      ) : (
                        <div className="space-y-1 max-h-[120px] overflow-y-auto">
                          {otherCaseFiles.map((f) => (
                            <button
                              key={f.id}
                              type="button"
                              onClick={() => addOtherCaseFile(f)}
                              disabled={attachments.some((a) => a.id === `other-${otherCaseSelected}-${f.id}`)}
                              className={cn(
                                "w-full flex items-center gap-2 rounded px-2 py-1.5 text-xs text-left hover:bg-muted transition-colors",
                                attachments.some((a) => a.id === `other-${otherCaseSelected}-${f.id}`) && "opacity-50 cursor-not-allowed"
                              )}
                            >
                              <FileText className="h-3 w-3 text-muted-foreground shrink-0" />
                              <span className="truncate flex-1">{f.original_filename}</span>
                              <span className="text-muted-foreground shrink-0">{formatFileSize(f.file_size)}</span>
                              {attachments.some((a) => a.id === `other-${otherCaseSelected}-${f.id}`) && (
                                <span className="text-[10px] text-primary">Toegevoegd</span>
                              )}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  <Button type="button" variant="ghost" size="sm" onClick={() => setShowOtherCase(false)} className="text-xs">
                    Sluiten
                  </Button>
                </div>
              )}

              {/* Attachment badges */}
              {attachments.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {attachments.map((att) => (
                    <span
                      key={att.id}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-muted/50 px-2.5 py-1 text-xs"
                    >
                      <Paperclip className="h-3 w-3 text-muted-foreground" />
                      <span className="max-w-[150px] truncate">{att.filename}</span>
                      <span className="text-muted-foreground">{formatFileSize(att.size)}</span>
                      <button
                        type="button"
                        onClick={() => removeAttachment(att.id)}
                        className="rounded-full p-0.5 hover:bg-destructive/10 hover:text-destructive"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}

              {fieldErrors.attachments && (
                <p className="text-[13px] text-destructive">{fieldErrors.attachments}</p>
              )}
            </div>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleOpenChange(false)} disabled={isSending}>
              Annuleren
            </Button>
            <Button type="submit" disabled={isSending || !to.trim()}>
              {isSending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Aanmaken...
                </>
              ) : caseId ? (
                <>
                  <ExternalLink className="h-4 w-4" />
                  Open in Outlook
                </>
              ) : (
                <>
                  <Mail className="h-4 w-4" />
                  Versturen
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
