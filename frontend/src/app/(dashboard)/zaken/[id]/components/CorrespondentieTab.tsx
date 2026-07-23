"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ArrowDownLeft,
  ArrowUpRight,
  Bot,
  Check,
  ChevronDown,
  ChevronRight,
  Download,
  File,
  FolderInput,
  Forward,
  Loader2,
  Mail,
  Paperclip,
  Plus,
  Reply,
  Sparkles,
  XCircle,
} from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { ClassificationCard } from "@/components/classification-card";
import { AiReplyDialog } from "@/components/ai-reply-dialog";
import { toast } from "sonner";
import { sanitizeHtml } from "@/lib/sanitize";
import { useEmailLogs } from "@/hooks/use-documents";
import {
  useCaseEmails,
  useSyncEmails,
  useSyncedEmailDetail,
  buildSyncToastMessage,
  useSaveAttachmentToCase,
  type SyncedEmailDetail,
  type EmailAttachmentInfo,
} from "@/hooks/use-email-sync";
import { useClassifications, type Classification } from "@/hooks/use-ai-agent";
import { useEmailOAuthStatus } from "@/hooks/use-email-oauth";
import { formatDateTime } from "@/lib/utils";
import { tokenStore } from "@/lib/token-store";

// ── Draad-groepering (S244) ─────────────────────────────────────────────────
// Gmail/Outlook-model: de lijst toont gesprekken (draden), niet losse mails.
// Sleutel = provider_thread_id; mails zonder thread-id (oude SMTP-logs, losse
// berichten) vallen terug op het genormaliseerde onderwerp. Een onderwerp-groep
// wordt samengevoegd met een thread-id-groep als er precies één draad met dat
// onderwerp bestaat — anders blijft hij apart (nooit gokken tussen twee draden).

type TimelineItem = {
  id: string;
  type: "synced" | "sent";
  date: string;
  subject: string;
  from: string;
  to: string;
  direction: "inbound" | "outbound";
  snippet: string;
  threadId: string | null;
  status?: string;
  isRead?: boolean;
  hasAttachments?: boolean;
};

type Thread = {
  key: string;
  subject: string;
  items: TimelineItem[]; // oudste eerst (Gmail-volgorde in het leesvenster)
  latest: TimelineItem;
  unreadCount: number;
  hasAttachments: boolean;
};

function normalizeSubject(subject: string): string {
  let s = (subject || "").trim();
  // Re:/Fwd:/Fw: (ook gestapeld: "Re: Fwd: ...") eraf
  for (;;) {
    const stripped = s.replace(/^(re|fwd|fw)\s*:\s*/i, "");
    if (stripped === s) break;
    s = stripped;
  }
  return s.toLowerCase();
}

function buildThreads(items: TimelineItem[]): Thread[] {
  const byKey = new Map<string, TimelineItem[]>();
  // norm-onderwerp → thread-keys die dat onderwerp dragen
  const tidKeysBySubject = new Map<string, Set<string>>();

  for (const item of items) {
    if (item.threadId) {
      const key = `tid:${item.threadId}`;
      if (!byKey.has(key)) byKey.set(key, []);
      byKey.get(key)!.push(item);
      const norm = normalizeSubject(item.subject);
      if (!tidKeysBySubject.has(norm)) tidKeysBySubject.set(norm, new Set());
      tidKeysBySubject.get(norm)!.add(key);
    }
  }
  for (const item of items) {
    if (item.threadId) continue;
    const norm = normalizeSubject(item.subject);
    const tidKeys = tidKeysBySubject.get(norm);
    // Precies één bestaande draad met dit onderwerp → daarin voegen
    const key = tidKeys && tidKeys.size === 1 ? [...tidKeys][0] : `sub:${norm}`;
    if (!byKey.has(key)) byKey.set(key, []);
    byKey.get(key)!.push(item);
  }

  const threads: Thread[] = [];
  for (const [key, threadItems] of byKey) {
    threadItems.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
    const latest = threadItems[threadItems.length - 1];
    threads.push({
      key,
      subject: latest.subject || "(Geen onderwerp)",
      items: threadItems,
      latest,
      unreadCount: threadItems.filter((i) => i.isRead === false && i.direction === "inbound").length,
      hasAttachments: threadItems.some((i) => i.hasAttachments),
    });
  }
  threads.sort((a, b) => new Date(b.latest.date).getTime() - new Date(a.latest.date).getTime());
  return threads;
}

// ── Eén bericht in het gesprek (uitklapbaar) ────────────────────────────────

function ThreadMessage({
  item,
  caseId,
  defaultOpen,
  onReply,
  onAiReply,
}: {
  item: TimelineItem;
  caseId: string;
  defaultOpen: boolean;
  onReply?: (email: SyncedEmailDetail, mode: "reply" | "forward") => void;
  onAiReply?: (email: SyncedEmailDetail) => void;
}) {
  const [open, setOpen] = useState(defaultOpen);
  // Lazy: volledige inhoud pas ophalen bij uitklappen (patroon MailThreadPanel)
  const { data: detail, isLoading } = useSyncedEmailDetail(
    open && item.type === "synced" ? item.id : undefined
  );
  const saveToCase = useSaveAttachmentToCase();
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const inbound = item.direction === "inbound";

  const handleDownloadAttachment = async (attachmentId: string, filename: string) => {
    setDownloadingId(attachmentId);
    try {
      const token = tokenStore.getAccess();
      const res = await fetch(`/api/email/attachments/${attachmentId}/download`, {
        headers: { Authorization: `Bearer ${token}` },
      });
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

  // Verzend-logboekregel (SMTP/brief): geen opgeslagen inhoud — alleen de kop.
  if (item.type === "sent") {
    return (
      <div className="rounded-lg border border-border bg-muted/20 px-3 py-2">
        <div className="flex items-center gap-2 text-xs">
          <ArrowUpRight className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
          <span className="min-w-0 flex-1 truncate font-medium text-foreground">
            Luxis → {item.to}
          </span>
          {item.status === "failed" && (
            <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-1.5 py-0.5 text-[10px] font-medium text-red-600">
              <XCircle className="h-2.5 w-2.5" /> Mislukt
            </span>
          )}
          <span className="shrink-0 text-muted-foreground">
            {formatDateTime(item.date, "short")}
          </span>
        </div>
        <p className="mt-0.5 pl-6 text-xs text-muted-foreground truncate">
          {item.subject} · verstuurd via Luxis (inhoud in Documenten)
        </p>
      </div>
    );
  }

  return (
    <div className={`rounded-lg border bg-card ${open ? "border-border" : "border-border/70"}`}>
      {/* Kop — klik = in-/uitklappen */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left"
      >
        {open ? (
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        )}
        {inbound ? (
          <ArrowDownLeft className="h-3.5 w-3.5 shrink-0 text-blue-600" />
        ) : (
          <ArrowUpRight className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
        )}
        <span
          className={`min-w-0 flex-1 truncate text-sm ${
            item.isRead === false ? "font-semibold" : "font-medium"
          } text-foreground`}
        >
          {inbound ? item.from : `Aan ${item.to}`}
        </span>
        {!open && item.snippet && (
          <span className="hidden sm:block min-w-0 max-w-[40%] truncate text-xs text-muted-foreground">
            {item.snippet}
          </span>
        )}
        {item.hasAttachments && <Paperclip className="h-3 w-3 shrink-0 text-muted-foreground" />}
        <span className="shrink-0 text-xs text-muted-foreground whitespace-nowrap">
          {formatDateTime(item.date, "short")}
        </span>
      </button>

      {open && (
        <div className="border-t border-border">
          {isLoading || !detail ? (
            <div className="flex items-center gap-2 px-4 py-3 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Laden...
            </div>
          ) : (
            <>
              {/* Volledige kop + acties */}
              <div className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-start sm:justify-between border-b border-border">
                <div className="space-y-0.5 text-xs text-muted-foreground min-w-0">
                  <p className="break-words">
                    <span className="font-medium text-foreground">Van:</span>{" "}
                    {detail.from_name
                      ? `${detail.from_name} <${detail.from_email}>`
                      : detail.from_email}
                  </p>
                  <p className="break-words">
                    <span className="font-medium text-foreground">Aan:</span>{" "}
                    {detail.to_emails.join(", ")}
                  </p>
                  {detail.cc_emails.length > 0 && (
                    <p className="break-words">
                      <span className="font-medium text-foreground">CC:</span>{" "}
                      {detail.cc_emails.join(", ")}
                    </p>
                  )}
                  <p>
                    <span className="font-medium text-foreground">Datum:</span>{" "}
                    {formatDateTime(detail.email_date, "long")}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-1 shrink-0">
                  {onAiReply && inbound && (
                    <button
                      type="button"
                      onClick={() => onAiReply(detail)}
                      title="AI schrijft een concept-antwoord op deze mail"
                      className="inline-flex items-center gap-1 rounded-md border border-primary/30 bg-primary/5 px-2 py-1 text-xs font-medium text-primary hover:bg-primary/10 transition-colors"
                    >
                      <Sparkles className="h-3.5 w-3.5" /> AI-antwoord
                    </button>
                  )}
                  {onReply && (
                    <>
                      <button
                        type="button"
                        onClick={() => onReply(detail, "reply")}
                        className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs font-medium hover:bg-muted transition-colors"
                      >
                        <Reply className="h-3.5 w-3.5" /> Beantwoorden
                      </button>
                      <button
                        type="button"
                        onClick={() => onReply(detail, "forward")}
                        className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs font-medium hover:bg-muted transition-colors"
                      >
                        <Forward className="h-3.5 w-3.5" /> Doorsturen
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* AI-beoordeling (alleen inkomend) */}
              {inbound && (
                <div className="border-b border-border px-4 py-2">
                  <ClassificationCard syncedEmailId={item.id} />
                </div>
              )}

              {/* Bijlagen */}
              {detail.attachments && detail.attachments.length > 0 && (
                <div className="border-b border-border px-4 py-2">
                  <div className="flex flex-wrap gap-2">
                    {detail.attachments.map((att: EmailAttachmentInfo) => (
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

              {/* Inhoud */}
              <div className="p-4 overflow-auto max-h-[480px]">
                {detail.body_html ? (
                  <div
                    className="prose prose-sm max-w-none text-foreground"
                    dangerouslySetInnerHTML={{ __html: sanitizeHtml(detail.body_html) }}
                  />
                ) : (
                  <pre className="text-sm text-foreground whitespace-pre-wrap font-sans">
                    {detail.body_text || item.snippet}
                  </pre>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

// ── Gespreksweergave (leesvenster) ──────────────────────────────────────────

function ThreadView({
  thread,
  caseId,
  onClose,
  onReply,
  onAiReply,
}: {
  thread: Thread;
  caseId: string;
  onClose: () => void;
  onReply?: (email: SyncedEmailDetail, mode: "reply" | "forward") => void;
  onAiReply?: (email: SyncedEmailDetail) => void;
}) {
  // Nieuwste synced-bericht standaard open (Gmail-gedrag)
  const lastSyncedId = [...thread.items].reverse().find((i) => i.type === "synced")?.id;

  return (
    <div className="w-full lg:w-3/5">
      <div className="rounded-xl border border-border bg-card">
        {/* Gesprekskop */}
        <div className="flex items-start justify-between gap-3 border-b border-border p-4">
          <div className="min-w-0">
            <button
              type="button"
              onClick={onClose}
              className="lg:hidden mb-2 inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
            >
              <ArrowDownLeft className="h-4 w-4 rotate-45" />
              Terug naar lijst
            </button>
            <h3 className="text-sm font-semibold text-foreground break-words">
              {thread.subject}
            </h3>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {thread.items.length === 1
                ? "1 bericht"
                : `${thread.items.length} berichten`}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Gesprek sluiten"
            className="rounded-md p-1 hover:bg-muted transition-colors shrink-0"
          >
            <XCircle className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>
        {/* Berichten — oudste boven, nieuwste open */}
        <div className="space-y-2 p-3">
          {thread.items.map((item) => (
            <ThreadMessage
              key={`${item.type}-${item.id}`}
              item={item}
              caseId={caseId}
              defaultOpen={item.id === lastSyncedId}
              onReply={onReply}
              onAiReply={onAiReply}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Correspondentie Tab ─────────────────────────────────────────────────────

function CorrespondentieTab({
  caseId,
  onCompose,
  onReply,
  onOpenDraft,
}: {
  caseId: string;
  onCompose?: () => void;
  onReply?: (email: SyncedEmailDetail, mode: "reply" | "forward") => void;
  onOpenDraft?: (draftId: string, sourceEmail?: SyncedEmailDetail) => void;
}) {
  const { data: logs, isLoading: logsLoading } = useEmailLogs(caseId);
  // ponytail: 200 dekt het drukste dossier ruim (max ~83 nu); voeg echte paging
  // toe zodra een dossier de 200 nadert.
  const { data: syncedData, isLoading: syncedLoading } = useCaseEmails(caseId, 200);
  const { data: classifications } = useClassifications(undefined, caseId, 1, 100);
  const oauthStatus = useEmailOAuthStatus();
  const syncEmails = useSyncEmails();
  const [selectedThreadKey, setSelectedThreadKey] = useState<string | null>(null);
  const [viewFilter, setViewFilter] = useState<"all" | "inbound" | "outbound">("all");
  // S227/S244 — AI-antwoord opent hier zodat het concept in deze pagina opent
  const [aiReplyEmail, setAiReplyEmail] = useState<SyncedEmailDetail | null>(null);

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

  // Samenvoegen: gesynchte mails + verzend-logboek (dedup zoals voorheen)
  const timelineItems: TimelineItem[] = useMemo(() => {
    const items: TimelineItem[] = [];
    if (syncedData?.emails) {
      for (const e of syncedData.emails) {
        items.push({
          id: e.id,
          type: "synced",
          date: e.email_date,
          subject: e.subject,
          from: e.from_name || e.from_email,
          to: e.to_emails.join(", "),
          direction: e.direction,
          snippet: e.snippet,
          threadId: e.provider_thread_id ?? null,
          isRead: e.is_read,
          hasAttachments: e.has_attachments,
        });
      }
    }
    if (logs) {
      for (const log of logs) {
        const isDuplicate = items.some(
          (item) => item.subject === log.subject && item.to === log.recipient && item.type === "synced"
        );
        if (!isDuplicate) {
          items.push({
            id: log.id,
            type: "sent",
            date: log.sent_at,
            subject: log.subject,
            from: "Luxis",
            to: log.recipient,
            direction: "outbound",
            snippet: "",
            threadId: null,
            status: log.status,
          });
        }
      }
    }
    return items;
  }, [syncedData, logs]);

  // Richting-filter vóór groepering: "Ontvangen" toont draden met alleen de
  // ontvangen berichten erin (voorspelbaar; zelfde gedrag als de oude lijst).
  const filteredItems = useMemo(
    () =>
      viewFilter === "all"
        ? timelineItems
        : timelineItems.filter((item) => item.direction === viewFilter),
    [timelineItems, viewFilter]
  );

  const threads = useMemo(() => buildThreads(filteredItems), [filteredItems]);
  const selectedThread = threads.find((t) => t.key === selectedThreadKey) ?? null;

  // Filterwissel kan de geopende draad laten verdwijnen → selectie wissen
  useEffect(() => {
    if (selectedThreadKey && !threads.some((t) => t.key === selectedThreadKey)) {
      setSelectedThreadKey(null);
    }
  }, [threads, selectedThreadKey]);

  const handleSync = async () => {
    try {
      const stats = await syncEmails.mutateAsync({ caseId });
      toast.success(buildSyncToastMessage(stats));
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
              Alle e-mails voor dit dossier, gegroepeerd per gesprek
            </p>
          </div>
          <div className="flex items-center gap-2">
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

      {/* Gesprekkenlijst + leesvenster. Onder lg: één paneel tegelijk. */}
      <div className="flex gap-4">
        {/* Lijst */}
        <div className={`${selectedThread ? "hidden lg:block lg:w-2/5" : "w-full"}`}>
          {isLoading ? (
            <div className="rounded-xl border border-border bg-card p-6">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                E-mails laden...
              </div>
            </div>
          ) : threads.length === 0 ? (
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
              {threads.map((thread) => {
                const t = thread.latest;
                const pendingReview = thread.items.some(
                  (i) => i.type === "synced" && classificationMap.get(i.id)?.status === "pending"
                );
                const unread = thread.unreadCount > 0;
                return (
                  <button
                    key={thread.key}
                    type="button"
                    onClick={() => setSelectedThreadKey(thread.key)}
                    className={`w-full text-left px-3 py-2.5 hover:bg-muted/30 transition-colors ${
                      selectedThreadKey === thread.key
                        ? "bg-primary/5 border-l-2 border-l-primary"
                        : ""
                    }`}
                  >
                    {/* Compacte rij: pijl · afzender · onderwerp · datum */}
                    <div className="flex items-center gap-2">
                      {t.direction === "inbound" ? (
                        <ArrowDownLeft className="h-3.5 w-3.5 shrink-0 text-blue-600" />
                      ) : (
                        <ArrowUpRight className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
                      )}
                      {unread && (
                        <span className="h-2 w-2 shrink-0 rounded-full bg-blue-500" aria-label="Ongelezen" />
                      )}
                      <span
                        className={`shrink-0 max-w-[35%] truncate text-sm ${
                          unread ? "font-semibold" : "font-medium"
                        } text-foreground`}
                      >
                        {t.direction === "inbound" ? t.from : t.to}
                      </span>
                      <span
                        className={`min-w-0 flex-1 truncate text-sm ${
                          unread ? "font-semibold text-foreground" : "text-muted-foreground"
                        }`}
                      >
                        {thread.subject}
                        {thread.items.length > 1 && (
                          <span className="ml-1 text-xs text-muted-foreground font-normal">
                            ({thread.items.length})
                          </span>
                        )}
                      </span>
                      {pendingReview && (
                        <span
                          className="shrink-0 flex items-center gap-1 rounded-full bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium text-amber-600"
                          title="Wacht op review"
                        >
                          <Bot className="h-2.5 w-2.5" />
                          Review
                        </span>
                      )}
                      {thread.hasAttachments && (
                        <Paperclip className="h-3 w-3 shrink-0 text-muted-foreground" />
                      )}
                      <span className="shrink-0 text-xs text-muted-foreground whitespace-nowrap">
                        {formatDateTime(t.date, "short")}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Leesvenster */}
        {selectedThread && (
          <ThreadView
            thread={selectedThread}
            caseId={caseId}
            onClose={() => setSelectedThreadKey(null)}
            onReply={onReply}
            onAiReply={onOpenDraft ? (email) => setAiReplyEmail(email) : undefined}
          />
        )}
      </div>

      {/* AI-antwoord maken (gedeelde dialoog, zelfde flow als Mail-pagina) */}
      {aiReplyEmail && onOpenDraft && (
        <AiReplyDialog
          email={aiReplyEmail}
          onClose={() => setAiReplyEmail(null)}
          onOpenDraft={(draftId) => {
            const src = aiReplyEmail;
            setAiReplyEmail(null);
            onOpenDraft(draftId, src);
          }}
        />
      )}
    </div>
  );
}

export default CorrespondentieTab;
