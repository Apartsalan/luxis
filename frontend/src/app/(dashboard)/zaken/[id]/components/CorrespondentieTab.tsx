"use client";

import { useState, useMemo } from "react";
import {
  ArrowDownLeft,
  ArrowUpRight,
  Bot,
  Check,
  CheckCheck,
  Download,
  File,
  FolderInput,
  Loader2,
  Mail,
  Plus,
  XCircle,
} from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { ClassificationCard } from "@/components/classification-card";
import { toast } from "sonner";
import { sanitizeHtml } from "@/lib/sanitize";
import {
  useEmailLogs,
  type EmailLogEntry,
} from "@/hooks/use-documents";
import {
  useCaseEmails,
  useSyncEmails,
  useSyncedEmailDetail,
  useSaveAttachmentToCase,
  type SyncedEmailSummary,
  type EmailAttachmentInfo,
} from "@/hooks/use-email-sync";
import { useClassifications, type Classification } from "@/hooks/use-ai-agent";
import { useGenerateDraft, type AiDraft } from "@/hooks/use-ai-draft";
import { confidenceBadgeClasses, confidenceLabelText } from "@/lib/confidence";
import { useEmailOAuthStatus } from "@/hooks/use-email-oauth";
import { formatDate, formatDateShort } from "@/lib/utils";
import { tokenStore } from "@/lib/token-store";

// ── Email Detail Panel ──────────────────────────────────────────────────────

function EmailDetailPanel({ emailId, caseId, onClose }: { emailId: string; caseId: string; onClose: () => void }) {
  const { data: email, isLoading } = useSyncedEmailDetail(emailId);
  const saveToCase = useSaveAttachmentToCase();
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());

  const handleDownloadAttachment = async (attachmentId: string, filename: string) => {
    setDownloadingId(attachmentId);
    try {
      const token = tokenStore.getAccess();
      const apiUrl = "";
      const res = await fetch(
        `${apiUrl}/api/email/attachments/${attachmentId}/download`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!res.ok) throw new Error("Download mislukt");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Download mislukt");
    } finally {
      setDownloadingId(null);
    }
  };

  const handleSaveToCase = async (attachmentId: string) => {
    try {
      await saveToCase.mutateAsync({ attachmentId, caseId });
      setSavedIds((prev) => new Set(prev).add(attachmentId));
      toast.success("Bijlage opgeslagen in dossier");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Opslaan mislukt");
    }
  };

  if (isLoading) {
    return (
      <div className="w-3/5 rounded-xl border border-border bg-card p-6">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          E-mail laden...
        </div>
      </div>
    );
  }

  if (!email) {
    return (
      <div className="w-3/5 rounded-xl border border-border bg-card p-6">
        <p className="text-sm text-muted-foreground">E-mail niet gevonden</p>
      </div>
    );
  }

  return (
    <div className="w-3/5 rounded-xl border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="border-b border-border p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-foreground">{email.subject}</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 hover:bg-muted transition-colors"
          >
            <XCircle className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>
        <div className="space-y-1 text-xs text-muted-foreground">
          <div className="flex gap-2">
            <span className="font-medium w-8">Van:</span>
            <span>{email.from_name ? `${email.from_name} <${email.from_email}>` : email.from_email}</span>
          </div>
          <div className="flex gap-2">
            <span className="font-medium w-8">Aan:</span>
            <span>{email.to_emails.join(", ")}</span>
          </div>
          {email.cc_emails.length > 0 && (
            <div className="flex gap-2">
              <span className="font-medium w-8">CC:</span>
              <span>{email.cc_emails.join(", ")}</span>
            </div>
          )}
          <div className="flex gap-2">
            <span className="font-medium w-12">Datum:</span>
            <span>{formatDate(email.email_date)}</span>
          </div>
        </div>
      </div>
      {/* AI Classification */}
      <div className="border-b border-border px-4 py-3">
        <ClassificationCard syncedEmailId={emailId} />
      </div>
      {/* Attachments */}
      {email.attachments && email.attachments.length > 0 && (
        <div className="border-b border-border px-4 py-3">
          <p className="text-xs font-medium text-muted-foreground mb-2">
            {email.attachments.length} bijlage{email.attachments.length > 1 ? "n" : ""}
          </p>
          <div className="flex flex-wrap gap-2">
            {email.attachments.map((att: EmailAttachmentInfo) => (
              <div key={att.id} className="inline-flex items-center gap-0.5">
                <button
                  type="button"
                  onClick={() => handleDownloadAttachment(att.id, att.filename)}
                  disabled={downloadingId === att.id}
                  className="inline-flex items-center gap-1.5 rounded-l-lg border border-border bg-muted/30 px-2.5 py-1.5 text-xs font-medium text-foreground hover:bg-muted/60 transition-colors"
                >
                  {downloadingId === att.id ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <File className="h-3 w-3 text-muted-foreground" />
                  )}
                  <span className="max-w-[150px] truncate">{att.filename}</span>
                  <span className="text-muted-foreground">
                    ({att.file_size > 1048576
                      ? `${(att.file_size / 1048576).toFixed(1)} MB`
                      : `${Math.round(att.file_size / 1024)} KB`})
                  </span>
                  <Download className="h-3 w-3 text-muted-foreground" />
                </button>
                <button
                  type="button"
                  onClick={() => handleSaveToCase(att.id)}
                  disabled={savedIds.has(att.id) || saveToCase.isPending}
                  title="Opslaan in dossier"
                  className="inline-flex items-center gap-1 rounded-r-lg border border-l-0 border-border bg-muted/30 px-2 py-1.5 text-xs font-medium text-muted-foreground hover:bg-primary/10 hover:text-primary transition-colors disabled:opacity-50"
                >
                  {savedIds.has(att.id) ? (
                    <Check className="h-3 w-3 text-emerald-600" />
                  ) : (
                    <FolderInput className="h-3 w-3" />
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
      {/* Body */}
      <div className="p-4 overflow-auto max-h-[600px]">
        {email.body_html ? (
          <div
            className="prose prose-sm max-w-none text-foreground"
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(email.body_html) }}
          />
        ) : (
          <pre className="text-sm text-foreground whitespace-pre-wrap font-sans">
            {email.body_text}
          </pre>
        )}
      </div>
    </div>
  );
}

// ── Correspondentie Tab ─────────────────────────────────────────────────────

// ── Classification Badge ─────────────────────────────────────────────────────

function ClassificationBadge({ classification }: { classification: Classification }) {
  const confidenceColor = confidenceBadgeClasses(classification.confidence);

  const statusIcon =
    classification.status === "executed" ? (
      <CheckCheck className="h-2.5 w-2.5" />
    ) : classification.status === "approved" ? (
      <Check className="h-2.5 w-2.5" />
    ) : classification.status === "pending" ? (
      <span className="relative flex h-1.5 w-1.5">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-current opacity-75" />
        <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-current" />
      </span>
    ) : null;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${confidenceColor}`}
      title={`${classification.category_label} (${confidenceLabelText(classification.confidence)}) — ${classification.suggested_action_label}`}
    >
      {statusIcon}
      {classification.category_label}
    </span>
  );
}

// ── Correspondentie Tab ─────────────────────────────────────────────────────

function CorrespondentieTab({ caseId, onCompose }: { caseId: string; onCompose?: () => void }) {
  const { data: logs, isLoading: logsLoading } = useEmailLogs(caseId);
  const { data: syncedData, isLoading: syncedLoading } = useCaseEmails(caseId);
  const { data: classifications } = useClassifications(undefined, caseId, 1, 100);
  const oauthStatus = useEmailOAuthStatus();
  const syncEmails = useSyncEmails();
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const [viewFilter, setViewFilter] = useState<"all" | "inbound" | "outbound">("all");
  const generateDraft = useGenerateDraft();
  const [draft, setDraft] = useState<AiDraft | null>(null);

  // Build lookup map: synced_email_id → Classification
  const classificationMap = useMemo(() => {
    const map = new Map<string, Classification>();
    if (classifications) {
      for (const c of classifications) {
        map.set(c.synced_email_id, c);
      }
    }
    return map;
  }, [classifications]);

  const isLoading = logsLoading || syncedLoading;

  // Merge synced emails + sent email logs into a unified timeline
  type TimelineItem = {
    id: string;
    type: "synced" | "sent";
    date: string;
    subject: string;
    from: string;
    to: string;
    direction: "inbound" | "outbound";
    snippet: string;
    status?: string;
    isRead?: boolean;
    hasAttachments?: boolean;
  };

  const timelineItems: TimelineItem[] = [];

  // Add synced emails (from inbox sync)
  if (syncedData?.emails) {
    for (const e of syncedData.emails) {
      timelineItems.push({
        id: e.id,
        type: "synced",
        date: e.email_date,
        subject: e.subject,
        from: e.from_name || e.from_email,
        to: e.to_emails.join(", "),
        direction: e.direction,
        snippet: e.snippet,
        isRead: e.is_read,
        hasAttachments: e.has_attachments,
      });
    }
  }

  // Add sent email logs (from SMTP / freestanding sends)
  if (logs) {
    for (const log of logs) {
      // Skip if already in synced (avoid duplicates for outbound via Gmail)
      const isDuplicate = timelineItems.some(
        (item) => item.subject === log.subject && item.to === log.recipient && item.type === "synced"
      );
      if (!isDuplicate) {
        timelineItems.push({
          id: log.id,
          type: "sent",
          date: log.sent_at,
          subject: log.subject,
          from: "Luxis",
          to: log.recipient,
          direction: "outbound",
          snippet: "",
          status: log.status,
        });
      }
    }
  }

  // Sort by date descending
  timelineItems.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  // Apply filter
  const filteredItems = viewFilter === "all"
    ? timelineItems
    : timelineItems.filter((item) => item.direction === viewFilter);

  const handleSync = async () => {
    try {
      const stats = await syncEmails.mutateAsync({ caseId });
      toast.success(
        `Sync klaar: ${stats.new} nieuw, ${stats.linked} gekoppeld`
      );
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Sync mislukt");
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="mb-1 text-base font-semibold text-foreground">
              Correspondentie
            </h2>
            <p className="text-sm text-muted-foreground">
              Alle in- en uitgaande e-mails voor dit dossier
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={async () => {
                try {
                  const result = await generateDraft.mutateAsync({ caseId });
                  setDraft(result);
                } catch (err: unknown) {
                  toast.error(err instanceof Error ? err.message : "Concept genereren mislukt");
                }
              }}
              disabled={generateDraft.isPending}
              className="inline-flex items-center gap-1.5 rounded-lg border border-primary/30 bg-primary/5 px-3 py-2 text-xs font-medium text-primary hover:bg-primary/10 transition-colors"
            >
              {generateDraft.isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Bot className="h-3.5 w-3.5" />
              )}
              AI Concept
            </button>
            {oauthStatus.data?.connected && (
              <button
                type="button"
                onClick={handleSync}
                disabled={syncEmails.isPending}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-2 text-xs font-medium text-foreground hover:bg-muted/50 transition-colors"
              >
                {syncEmails.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <ArrowDownLeft className="h-3.5 w-3.5" />
                )}
                Sync inbox
              </button>
            )}
            {onCompose && (
              <button
                type="button"
                onClick={onCompose}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                <Plus className="h-3.5 w-3.5" />
                Nieuwe e-mail
              </button>
            )}
          </div>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-1 rounded-lg bg-muted/50 p-1 w-fit">
          {([["all", "Alles"], ["inbound", "Ontvangen"], ["outbound", "Verzonden"]] as const).map(
            ([key, label]) => (
              <button
                key={key}
                onClick={() => setViewFilter(key)}
                className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                  viewFilter === key
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {label}
                {key === "all" && timelineItems.length > 0 && (
                  <span className="ml-1 text-muted-foreground">({timelineItems.length})</span>
                )}
              </button>
            )
          )}
        </div>
      </div>

      {/* AI Draft preview panel */}
      {draft && (
        <div className="rounded-xl border border-primary/20 bg-primary/5 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-primary/10">
            <div className="flex items-center gap-2">
              <Bot className="h-4 w-4 text-primary" />
              <span className="text-sm font-semibold text-foreground">AI Concept</span>
              <span className="rounded-md bg-violet-100 dark:bg-violet-900/30 px-1.5 py-0.5 text-[9px] font-semibold text-violet-700 dark:text-violet-400 uppercase tracking-wider">
                AI
              </span>
              <span className="text-[10px] text-muted-foreground">
                {draft.tone} · {draft.model}
              </span>
            </div>
            <button
              type="button"
              onClick={() => setDraft(null)}
              className="rounded-md p-1 hover:bg-muted transition-colors"
            >
              <XCircle className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
          <div className="p-4 space-y-3">
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Onderwerp</p>
              <p className="text-sm font-medium text-foreground">{draft.subject}</p>
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Bericht</p>
              <pre className="text-sm text-foreground whitespace-pre-wrap font-sans bg-card rounded-lg border border-border p-3 max-h-[300px] overflow-y-auto">
                {draft.body}
              </pre>
            </div>
            {draft.sources.length > 0 && (
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-1">Bronnen</p>
                <div className="flex flex-wrap gap-1.5">
                  {draft.sources.map((s, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground"
                    >
                      {s.type === "email" ? "📧" : s.type === "factuur" ? "📄" : s.type === "av" ? "📋" : "⚖️"}{" "}
                      {s.reference}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {draft.reasoning && (
              <p className="text-xs text-muted-foreground italic">{draft.reasoning}</p>
            )}
            <div className="flex items-center gap-2 pt-1">
              <button
                type="button"
                onClick={() => {
                  if (onCompose) onCompose();
                  setDraft(null);
                }}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                <Mail className="h-3.5 w-3.5" />
                Gebruik als e-mail
              </button>
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(`Onderwerp: ${draft.subject}\n\n${draft.body}`);
                  toast.success("Concept gekopieerd naar klembord");
                }}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-2 text-xs font-medium text-foreground hover:bg-muted/50 transition-colors"
              >
                Kopiëren
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Email list + detail split */}
      <div className="flex gap-4">
        {/* Email list */}
        <div className={`${selectedEmailId ? "w-2/5" : "w-full"} space-y-0`}>
          {isLoading ? (
            <div className="rounded-xl border border-border bg-card p-6">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                E-mails laden...
              </div>
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="rounded-xl border border-border bg-card p-6">
              <EmptyState
                icon={Mail}
                title="Nog geen e-mails"
                description={oauthStatus.data?.connected
                  ? "Nog geen e-mails voor dit dossier. Klik 'Sync inbox' om e-mails op te halen."
                  : "Verbind je e-mail via Instellingen om e-mails te synchroniseren."}
              />
            </div>
          ) : (
            <div className="rounded-xl border border-border bg-card overflow-hidden divide-y divide-border">
              {filteredItems.map((item) => (
                <button
                  key={`${item.type}-${item.id}`}
                  type="button"
                  onClick={() => item.type === "synced" ? setSelectedEmailId(item.id) : null}
                  className={`w-full text-left px-4 py-3 hover:bg-muted/30 transition-colors ${
                    selectedEmailId === item.id ? "bg-primary/5 border-l-2 border-l-primary" : ""
                  } ${item.type === "sent" ? "cursor-default" : "cursor-pointer"}`}
                >
                  <div className="flex items-start gap-3">
                    {/* Direction icon */}
                    <div className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                      item.direction === "inbound"
                        ? "bg-blue-100 dark:bg-blue-900/30"
                        : "bg-emerald-100 dark:bg-emerald-900/30"
                    }`}>
                      {item.direction === "inbound" ? (
                        <ArrowDownLeft className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                      ) : (
                        <ArrowUpRight className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                      )}
                    </div>
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className={`text-sm truncate ${item.isRead === false ? "font-semibold" : "font-medium"}`}>
                          {item.direction === "inbound" ? item.from : item.to}
                        </p>
                        <span className="text-xs text-muted-foreground whitespace-nowrap">
                          {formatDateShort(item.date)}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <p className="text-sm text-foreground truncate">{item.subject}</p>
                        {item.type === "synced" && classificationMap.get(item.id)?.status === "pending" && (
                          <span className="shrink-0 flex items-center gap-1 rounded-full bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium text-amber-600 dark:text-amber-400" title="Wacht op review">
                            <Bot className="h-2.5 w-2.5" />
                            Review
                          </span>
                        )}
                      </div>
                      {item.snippet && (
                        <p className="text-xs text-muted-foreground truncate mt-0.5">
                          {item.snippet}
                        </p>
                      )}
                      <div className="flex items-center gap-2 mt-1">
                        {item.type === "synced" && item.direction === "inbound" && classificationMap.has(item.id) && (
                          <ClassificationBadge classification={classificationMap.get(item.id)!} />
                        )}
                        {item.status === "failed" && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-1.5 py-0.5 text-[10px] font-medium text-red-600">
                            <XCircle className="h-2.5 w-2.5" />
                            Mislukt
                          </span>
                        )}
                        {item.hasAttachments && (
                          <span className="text-[10px] text-muted-foreground">{"\ud83d\udcce"}</span>
                        )}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Email detail panel */}
        {selectedEmailId && (
          <EmailDetailPanel
            emailId={selectedEmailId}
            caseId={caseId}
            onClose={() => setSelectedEmailId(null)}
          />
        )}
      </div>
    </div>
  );
}

export default CorrespondentieTab;
