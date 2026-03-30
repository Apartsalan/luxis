"use client";

import { useState, useEffect, useMemo } from "react";
import {
  Mail,
  ArrowDownLeft,
  ArrowUpRight,
  Paperclip,
  RefreshCw,
  Search,
  XCircle,
  Check,
  EyeOff,
  CheckSquare,
  Square,
  File,
  Star,
  Briefcase,
  Loader2,
  Inbox,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  useAllEmails,
  useUnlinkedEmails,
  useUnlinkedCount,
  useSyncEmails,
  useSyncedEmailDetail,
  useSuggestCases,
  useBulkLinkEmails,
  useDismissEmails,
  useLinkEmail,
  type SyncedEmailSummary,
  type CaseSuggestion,
} from "@/hooks/use-email-sync";
import { useCases } from "@/hooks/use-cases";
import { toast } from "sonner";
import { sanitizeHtml } from "@/lib/sanitize";
import { formatRelativeTime } from "@/lib/utils";

// ── Helpers ──────────────────────────────────────────────────────────────────

function useDebounce(value: string, delay: number) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

// ── Main Page ────────────────────────────────────────────────────────────────

export default function CorrespondentiePage() {
  // Tab state
  const [activeTab, setActiveTab] = useState<"alle" | "ongesorteerd">("alle");

  // Data hooks
  const { data: allEmailsData, isLoading: allLoading } = useAllEmails("all", undefined, 200);
  const { data: unlinkedData, isLoading } = useUnlinkedEmails(100);
  const { data: countData } = useUnlinkedCount();
  const syncEmails = useSyncEmails();
  const bulkLink = useBulkLinkEmails();
  const dismissEmails = useDismissEmails();
  const linkEmail = useLinkEmail();

  // UI state
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [emailFilter, setEmailFilter] = useState("");
  const [caseSearch, setCaseSearch] = useState("");
  const debouncedSearch = useDebounce(caseSearch, 300);

  // Case search for manual linking
  const { data: casesData } = useCases(
    debouncedSearch.length >= 2
      ? { search: debouncedSearch, per_page: 8 }
      : undefined
  );

  // Case suggestions for selected email
  const { data: suggestData, isLoading: suggestLoading } =
    useSuggestCases(selectedEmailId ?? undefined);

  // Selected email detail
  const { data: emailDetail } = useSyncedEmailDetail(
    selectedEmailId ?? undefined
  );

  const allEmails = unlinkedData?.emails ?? [];
  const total = countData?.count ?? unlinkedData?.total ?? 0;

  // Client-side filter on subject, sender, snippet
  const emails = useMemo(() => {
    if (!emailFilter.trim()) return allEmails;
    const q = emailFilter.toLowerCase();
    return allEmails.filter(
      (e) =>
        e.subject.toLowerCase().includes(q) ||
        e.from_email.toLowerCase().includes(q) ||
        e.from_name.toLowerCase().includes(q) ||
        e.snippet.toLowerCase().includes(q) ||
        e.to_emails.some((t) => t.toLowerCase().includes(q))
    );
  }, [allEmails, emailFilter]);

  // Group emails by date for display
  const groupedEmails = useMemo(() => {
    if (emails.length === 0) return [];
    const groups: { label: string; emails: typeof emails }[] = [];
    let currentLabel = "";

    for (const email of emails) {
      const label = getDateGroupLabel(email.email_date);
      if (label !== currentLabel) {
        currentLabel = label;
        groups.push({ label, emails: [email] });
      } else {
        groups[groups.length - 1].emails.push(email);
      }
    }
    return groups;
  }, [emails]);

  // Clear selection when emails change
  useEffect(() => {
    if (selectedEmailId && !allEmails.find((e) => e.id === selectedEmailId)) {
      setSelectedEmailId(null);
    }
  }, [allEmails, selectedEmailId]);

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleSync = () => {
    syncEmails.mutate(
      { maxResults: 100 },
      {
        onSuccess: (data) => {
          toast.success(`Sync voltooid: ${data.new} nieuw, ${data.linked} gekoppeld`);
        },
        onError: (err) => {
          toast.error(`Sync mislukt: ${err.message}`);
        },
      }
    );
  };

  const handleLinkToCase = (caseId: string, emailId?: string) => {
    const idsToLink = emailId ? [emailId] : Array.from(selectedIds);
    if (idsToLink.length === 0) return;

    if (idsToLink.length === 1) {
      linkEmail.mutate(
        { emailId: idsToLink[0], caseId },
        {
          onSuccess: () => {
            toast.success("E-mail gekoppeld aan dossier");
            setSelectedEmailId(null);
            setSelectedIds(new Set());
            setCaseSearch("");
          },
        }
      );
    } else {
      bulkLink.mutate(
        { emailIds: idsToLink, caseId },
        {
          onSuccess: (data) => {
            toast.success(`${data.linked_count} e-mail(s) gekoppeld`);
            setSelectedEmailId(null);
            setSelectedIds(new Set());
            setCaseSearch("");
          },
        }
      );
    }
  };

  const handleDismiss = (emailId?: string) => {
    const idsToDismiss = emailId ? [emailId] : Array.from(selectedIds);
    if (idsToDismiss.length === 0) return;

    dismissEmails.mutate(
      { emailIds: idsToDismiss },
      {
        onSuccess: (data) => {
          toast.success(`${data.dismissed_count} e-mail(s) genegeerd`);
          setSelectedEmailId(null);
          setSelectedIds(new Set());
        },
      }
    );
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === emails.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(emails.map((e) => e.id)));
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Correspondentie
          </h1>
          <div className="flex items-center gap-1 mt-2">
            <button
              onClick={() => { setActiveTab("alle"); setSelectedEmailId(null); setSelectedIds(new Set()); }}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                activeTab === "alle"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              Alle e-mails
              {allEmailsData?.total ? (
                <span className="ml-1.5 text-xs opacity-70">({allEmailsData.total})</span>
              ) : null}
            </button>
            <button
              onClick={() => { setActiveTab("ongesorteerd"); setSelectedEmailId(null); setSelectedIds(new Set()); }}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                activeTab === "ongesorteerd"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              Ongesorteerd
              {total > 0 && (
                <span className="ml-1.5 inline-flex items-center justify-center h-5 min-w-5 rounded-full bg-amber-500 text-white text-[10px] font-bold px-1.5">
                  {total}
                </span>
              )}
            </button>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Zoek op afzender, onderwerp..."
              className="pl-9 h-9 text-sm w-64"
              value={emailFilter}
              onChange={(e) => setEmailFilter(e.target.value)}
            />
            {emailFilter && (
              <button
                onClick={() => setEmailFilter("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                <XCircle className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleSync}
            disabled={syncEmails.isPending}
          >
            <RefreshCw
              className={`h-4 w-4 mr-2 ${syncEmails.isPending ? "animate-spin" : ""}`}
            />
            Sync inbox
          </Button>
        </div>
      </div>

      {/* Alle e-mails tab */}
      {activeTab === "alle" && (
        <AllEmailsView
          emails={allEmailsData?.emails ?? []}
          isLoading={allLoading}
          emailFilter={emailFilter}
        />
      )}

      {/* Ongesorteerd tab content */}
      {activeTab === "ongesorteerd" && <>
      {/* Bulk actions bar */}
      {selectedIds.size > 0 && (
        <div className="flex items-center gap-3 rounded-lg border border-border bg-muted/50 px-4 py-2">
          <span className="text-sm font-medium">
            {selectedIds.size} geselecteerd
          </span>
          <div className="flex gap-2 ml-auto">
            <BulkLinkButton
              selectedCount={selectedIds.size}
              onLink={(caseId) => handleLinkToCase(caseId)}
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleDismiss()}
              disabled={dismissEmails.isPending}
            >
              <EyeOff className="h-4 w-4 mr-1" />
              Negeren
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedIds(new Set())}
            >
              Deselecteer
            </Button>
          </div>
        </div>
      )}

      {/* Main content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      ) : emails.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="flex gap-4">
          {/* Email list */}
          <div
            className={`${selectedEmailId ? "w-2/5" : "w-full"} transition-all`}
          >
            {/* Select all */}
            <div className="flex items-center gap-2 mb-2 px-1">
              <button
                onClick={toggleSelectAll}
                className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                {selectedIds.size === emails.length ? (
                  <CheckSquare className="h-3.5 w-3.5" />
                ) : (
                  <Square className="h-3.5 w-3.5" />
                )}
                {selectedIds.size === emails.length
                  ? "Deselecteer alles"
                  : "Selecteer alles"}
              </button>
              <span className="text-xs text-muted-foreground">
                {emailFilter
                  ? `${emails.length} van ${allEmails.length} e-mails`
                  : `${emails.length} e-mails`}
              </span>
            </div>

            <div className="rounded-xl border border-border bg-card overflow-hidden">
              {groupedEmails.map((group) => (
                <div key={group.label}>
                  <div className="sticky top-0 z-10 bg-muted/80 backdrop-blur-sm px-4 py-1.5 border-b border-border">
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                      {group.label}
                    </span>
                  </div>
                  <div className="divide-y divide-border">
                    {group.emails.map((email) => (
                      <EmailListItem
                        key={email.id}
                        email={email}
                        isSelected={selectedEmailId === email.id}
                        isChecked={selectedIds.has(email.id)}
                        onSelect={() => setSelectedEmailId(email.id)}
                        onToggleCheck={() => toggleSelect(email.id)}
                        compact={!!selectedEmailId}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Detail + action panel */}
          {selectedEmailId && emailDetail && (
            <div className="w-3/5 space-y-4">
              {/* Email detail */}
              <div className="rounded-xl border border-border bg-card overflow-hidden">
                {/* Header */}
                <div className="flex items-start justify-between gap-4 border-b border-border p-4">
                  <div className="min-w-0 flex-1">
                    <h3 className="text-sm font-semibold truncate">
                      {emailDetail.subject || "(Geen onderwerp)"}
                    </h3>
                    <div className="mt-1 space-y-0.5 text-xs text-muted-foreground">
                      <p>
                        <span className="font-medium text-foreground">Van:</span>{" "}
                        {emailDetail.from_name
                          ? `${emailDetail.from_name} <${emailDetail.from_email}>`
                          : emailDetail.from_email}
                      </p>
                      <p>
                        <span className="font-medium text-foreground">Aan:</span>{" "}
                        {emailDetail.to_emails.join(", ")}
                      </p>
                      {emailDetail.cc_emails.length > 0 && (
                        <p>
                          <span className="font-medium text-foreground">CC:</span>{" "}
                          {emailDetail.cc_emails.join(", ")}
                        </p>
                      )}
                      <p>
                        <span className="font-medium text-foreground">Datum:</span>{" "}
                        {new Date(emailDetail.email_date).toLocaleString(
                          "nl-NL",
                          {
                            day: "numeric",
                            month: "long",
                            year: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          }
                        )}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedEmailId(null)}
                    className="rounded-md p-1 hover:bg-muted transition-colors"
                  >
                    <XCircle className="h-4 w-4 text-muted-foreground" />
                  </button>
                </div>

                {/* Attachments */}
                {emailDetail.attachments.length > 0 && (
                  <div className="border-b border-border px-4 py-3 flex flex-wrap gap-2">
                    {emailDetail.attachments.map((att) => (
                      <a
                        key={att.id}
                        href={`/api/email/attachments/${att.id}/download`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-muted/30 px-2.5 py-1.5 text-xs font-medium hover:bg-muted/60 transition-colors"
                      >
                        <File className="h-3 w-3" />
                        <span className="max-w-[150px] truncate">
                          {att.filename}
                        </span>
                        <span className="text-muted-foreground">
                          ({formatFileSize(att.file_size)})
                        </span>
                      </a>
                    ))}
                  </div>
                )}

                {/* Body */}
                <div className="p-4 overflow-auto max-h-[400px]">
                  {emailDetail.body_html ? (
                    <div
                      className="prose prose-sm max-w-none text-foreground"
                      dangerouslySetInnerHTML={{
                        __html: sanitizeHtml(emailDetail.body_html),
                      }}
                    />
                  ) : (
                    <pre className="text-sm text-foreground whitespace-pre-wrap font-sans">
                      {emailDetail.body_text || emailDetail.snippet}
                    </pre>
                  )}
                </div>
              </div>

              {/* Action panel: Link to case */}
              <div className="rounded-xl border border-border bg-card overflow-hidden">
                <div className="p-4 space-y-4">
                  <h4 className="text-sm font-semibold flex items-center gap-2">
                    <Briefcase className="h-4 w-4" />
                    Koppel aan dossier
                  </h4>

                  {/* Suggestions */}
                  {suggestLoading ? (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      Suggesties laden...
                    </div>
                  ) : (
                    suggestData &&
                    suggestData.suggestions.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-xs text-muted-foreground font-medium">
                          Suggesties
                        </p>
                        {suggestData.suggestions.map((s) => (
                          <SuggestionItem
                            key={s.case_id}
                            suggestion={s}
                            onLink={() =>
                              handleLinkToCase(s.case_id, selectedEmailId!)
                            }
                            isLinking={linkEmail.isPending}
                          />
                        ))}
                      </div>
                    )
                  )}

                  {/* Manual search */}
                  <div className="space-y-2">
                    <p className="text-xs text-muted-foreground font-medium">
                      Of zoek handmatig
                    </p>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                      <Input
                        placeholder="Zoek op dossiernummer, naam of cliënt..."
                        className="pl-9 h-9 text-sm"
                        value={caseSearch}
                        onChange={(e) => setCaseSearch(e.target.value)}
                      />
                    </div>
                    {debouncedSearch.length >= 2 && casesData?.items && (
                      <div className="rounded-lg border border-border divide-y divide-border max-h-[200px] overflow-auto">
                        {casesData.items.length === 0 ? (
                          <p className="px-3 py-2 text-xs text-muted-foreground">
                            Geen dossiers gevonden
                          </p>
                        ) : (
                          casesData.items.map((c) => (
                            <button
                              key={c.id}
                              onClick={() =>
                                handleLinkToCase(c.id, selectedEmailId!)
                              }
                              className="w-full text-left px-3 py-2 hover:bg-muted/50 transition-colors flex items-center justify-between gap-2"
                            >
                              <div className="min-w-0">
                                <p className="text-sm font-medium truncate">
                                  {c.case_number} — {c.description || "Geen beschrijving"}
                                </p>
                                <p className="text-xs text-muted-foreground truncate">
                                  {c.client?.name || "Geen cliënt"}
                                </p>
                              </div>
                              <Check className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                            </button>
                          ))
                        )}
                      </div>
                    )}
                  </div>

                  {/* Dismiss button */}
                  <div className="pt-2 border-t border-border">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-muted-foreground"
                      onClick={() => handleDismiss(selectedEmailId!)}
                      disabled={dismissEmails.isPending}
                    >
                      <EyeOff className="h-4 w-4 mr-1" />
                      Negeren — niet relevant
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      </>}
    </div>
  );
}

// ── All Emails View ─────────────────────────────────────────────────────────

function AllEmailsView({
  emails,
  isLoading,
  emailFilter,
}: {
  emails: SyncedEmailSummary[];
  isLoading: boolean;
  emailFilter: string;
}) {
  const filtered = useMemo(() => {
    if (!emailFilter.trim()) return emails;
    const q = emailFilter.toLowerCase();
    return emails.filter(
      (e) =>
        e.subject.toLowerCase().includes(q) ||
        e.from_email.toLowerCase().includes(q) ||
        e.from_name.toLowerCase().includes(q) ||
        e.snippet.toLowerCase().includes(q)
    );
  }, [emails, emailFilter]);

  const grouped = useMemo(() => {
    if (filtered.length === 0) return [];
    const groups: { label: string; emails: typeof filtered }[] = [];
    let currentLabel = "";
    for (const email of filtered) {
      const label = getDateGroupLabel(email.email_date);
      if (label !== currentLabel) {
        currentLabel = label;
        groups.push({ label, emails: [email] });
      } else {
        groups[groups.length - 1].emails.push(email);
      }
    }
    return groups;
  }, [filtered]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (filtered.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
          <Inbox className="h-8 w-8 text-muted-foreground/50" />
        </div>
        <p className="mt-5 text-base font-medium text-foreground">Geen e-mails</p>
        <p className="mt-1 text-sm text-muted-foreground">
          {emailFilter ? "Geen e-mails gevonden voor deze zoekopdracht" : "Er zijn nog geen e-mails gesynchroniseerd"}
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      {grouped.map((group) => (
        <div key={group.label}>
          <div className="px-4 py-2 bg-muted/30 border-b border-border">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              {group.label}
            </p>
          </div>
          {group.emails.map((email) => (
            <div
              key={email.id}
              className={`flex items-start gap-3 px-4 py-3 border-b border-border/50 hover:bg-muted/30 transition-colors border-l-3 ${
                email.direction === "inbound"
                  ? "border-l-blue-500 dark:border-l-blue-400"
                  : "border-l-emerald-500 dark:border-l-emerald-400"
              }`}
            >
              <div className="mt-0.5 shrink-0">
                {email.direction === "inbound" ? (
                  <ArrowDownLeft className="h-4 w-4 text-blue-500" />
                ) : (
                  <ArrowUpRight className="h-4 w-4 text-emerald-500" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground truncate">
                    {email.from_name || email.from_email}
                  </span>
                  <span className="text-[11px] text-muted-foreground shrink-0">
                    {formatRelativeTime(email.email_date)}
                  </span>
                  {email.has_attachments && (
                    <Paperclip className="h-3 w-3 text-muted-foreground shrink-0" />
                  )}
                </div>
                <p className="text-sm text-foreground truncate">{email.subject}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <p className="text-xs text-muted-foreground truncate flex-1">{email.snippet}</p>
                  {email.case_number ? (
                    <a
                      href={`/zaken/${email.case_id}`}
                      className="inline-flex items-center gap-1 shrink-0 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20 dark:bg-emerald-950 dark:text-emerald-300 dark:ring-emerald-400/30 hover:bg-emerald-100 transition-colors"
                    >
                      <Briefcase className="h-2.5 w-2.5" />
                      {email.case_number}
                    </a>
                  ) : (
                    <span className="inline-flex items-center gap-1 shrink-0 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700 ring-1 ring-inset ring-amber-600/20 dark:bg-amber-950 dark:text-amber-300 dark:ring-amber-400/30">
                      Niet gekoppeld
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

// ── Sub-components ───────────────────────────────────────────────────────────

function EmailListItem({
  email,
  isSelected,
  isChecked,
  onSelect,
  onToggleCheck,
  compact,
}: {
  email: SyncedEmailSummary;
  isSelected: boolean;
  isChecked: boolean;
  onSelect: () => void;
  onToggleCheck: () => void;
  compact: boolean;
}) {
  const directionBorder = email.direction === "inbound"
    ? "border-l-blue-500 dark:border-l-blue-400"
    : "border-l-emerald-500 dark:border-l-emerald-400";

  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 hover:bg-muted/30 transition-colors cursor-pointer border-l-3 ${
        isSelected
          ? `bg-primary/5 ${directionBorder}`
          : directionBorder
      }`}
    >
      {/* Checkbox */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onToggleCheck();
        }}
        className="mt-0.5 shrink-0"
      >
        {isChecked ? (
          <CheckSquare className="h-4 w-4 text-primary" />
        ) : (
          <Square className="h-4 w-4 text-muted-foreground" />
        )}
      </button>

      {/* Direction icon */}
      <div
        className={`h-7 w-7 rounded-full flex items-center justify-center shrink-0 ${
          email.direction === "inbound"
            ? "bg-blue-100 dark:bg-blue-900/30"
            : "bg-emerald-100 dark:bg-emerald-900/30"
        }`}
        onClick={onSelect}
      >
        {email.direction === "inbound" ? (
          <ArrowDownLeft
            className={`h-3.5 w-3.5 ${
              email.direction === "inbound"
                ? "text-blue-600 dark:text-blue-400"
                : "text-emerald-600 dark:text-emerald-400"
            }`}
          />
        ) : (
          <ArrowUpRight className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0" onClick={onSelect}>
        <div className="flex items-center justify-between gap-2">
          <p className="text-sm font-medium truncate" title={email.direction === "inbound" ? email.from_email : email.to_emails[0]}>
            {email.direction === "inbound"
              ? email.from_name
                ? `${email.from_name} (${email.from_email.split("@")[0]})`
                : email.from_email
              : email.to_emails[0] || "Onbekend"}
          </p>
          <div className="flex items-center gap-1.5 shrink-0">
            {email.has_attachments && (
              <Paperclip className="h-3 w-3 text-muted-foreground" />
            )}
            <span className="text-xs text-muted-foreground whitespace-nowrap">
              {formatRelativeTime(email.email_date)}
            </span>
          </div>
        </div>
        <p className="text-sm text-foreground truncate">
          {email.subject || "(Geen onderwerp)"}
        </p>
        {!compact && email.snippet && (
          <p className="text-xs text-muted-foreground truncate mt-0.5">
            {email.snippet}
          </p>
        )}
      </div>
    </div>
  );
}

function SuggestionItem({
  suggestion,
  onLink,
  isLinking,
}: {
  suggestion: CaseSuggestion;
  onLink: () => void;
  isLinking: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-border px-3 py-2 hover:bg-muted/30 transition-colors">
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          {suggestion.confidence === "high" && (
            <Star className="h-3 w-3 text-amber-500 fill-amber-500 shrink-0" />
          )}
          <p className="text-sm font-medium truncate">
            {suggestion.case_number}
            {suggestion.description && ` — ${suggestion.description}`}
          </p>
        </div>
        <p className="text-xs text-muted-foreground truncate">
          {suggestion.client_name && `${suggestion.client_name} · `}
          {suggestion.match_reason}
        </p>
      </div>
      <Button
        variant="outline"
        size="sm"
        className="shrink-0 h-7 text-xs"
        onClick={onLink}
        disabled={isLinking}
      >
        <Check className="h-3 w-3 mr-1" />
        Koppel
      </Button>
    </div>
  );
}

function BulkLinkButton({
  selectedCount,
  onLink,
}: {
  selectedCount: number;
  onLink: (caseId: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const { data: casesData } = useCases(
    debouncedSearch.length >= 2
      ? { search: debouncedSearch, per_page: 8 }
      : undefined
  );

  return (
    <div className="relative">
      <Button
        variant="default"
        size="sm"
        onClick={() => setOpen(!open)}
      >
        <Briefcase className="h-4 w-4 mr-1" />
        Koppel aan dossier
      </Button>
      {open && (
        <div className="absolute top-full mt-1 left-0 z-50 w-80 rounded-lg border border-border bg-card shadow-lg p-3 space-y-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Zoek dossier..."
              className="pl-9 h-8 text-sm"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
            />
          </div>
          {debouncedSearch.length >= 2 && casesData?.items && (
            <div className="rounded-lg border border-border divide-y divide-border max-h-[200px] overflow-auto">
              {casesData.items.length === 0 ? (
                <p className="px-3 py-2 text-xs text-muted-foreground">
                  Geen dossiers gevonden
                </p>
              ) : (
                casesData.items.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => {
                      onLink(c.id);
                      setOpen(false);
                      setSearch("");
                    }}
                    className="w-full text-left px-3 py-2 hover:bg-muted/50 transition-colors"
                  >
                    <p className="text-sm font-medium truncate">
                      {c.case_number} — {c.description || "Geen beschrijving"}
                    </p>
                    <p className="text-xs text-muted-foreground truncate">
                      {c.client?.name || "Geen cliënt"}
                    </p>
                  </button>
                ))
              )}
            </div>
          )}
          <button
            onClick={() => {
              setOpen(false);
              setSearch("");
            }}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            Annuleren
          </button>
        </div>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="h-14 w-14 rounded-2xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mb-4">
        <Inbox className="h-7 w-7 text-emerald-600 dark:text-emerald-400" />
      </div>
      <h3 className="text-lg font-semibold">Alles gesorteerd</h3>
      <p className="text-sm text-muted-foreground mt-1 max-w-sm">
        Alle e-mails zijn aan een dossier gekoppeld of genegeerd. Nieuwe
        ongesorteerde e-mails verschijnen hier automatisch na de volgende sync.
      </p>
    </div>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getDateGroupLabel(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const emailDay = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const diffDays = Math.floor((today.getTime() - emailDay.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Vandaag";
  if (diffDays === 1) return "Gisteren";
  if (diffDays < 7) return `${diffDays} dagen geleden`;

  return date.toLocaleDateString("nl-NL", {
    day: "numeric",
    month: "long",
    year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
  });
}
