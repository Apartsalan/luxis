"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  Mail,
  ArrowDownLeft,
  ArrowLeft,
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
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AiReplyDialog } from "@/components/ai-reply-dialog";
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
  buildSyncToastMessage,
  type SyncedEmailSummary,
  type SyncedEmailDetail,
  type CaseSuggestion,
} from "@/hooks/use-email-sync";
import { useCases } from "@/hooks/use-cases";
import {
  useIntakes,
  useIntakePendingCount,
  useApproveIntake,
  useRejectIntake,
  useCreateIntakeFromEmail,
  type IntakeResponse,
} from "@/hooks/use-intake";
import { useDebounce } from "@/hooks/use-debounce";
import { EmailComposeDialog, type EmailComposeData } from "@/components/email-compose-dialog";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { sanitizeHtml } from "@/lib/sanitize";
import { formatRelativeTime } from "@/lib/utils";
import { buildReplyPrefill, buildForwardPrefill, type ReplyPrefill } from "@/lib/email-reply";
import { Reply, Forward } from "lucide-react";

// ── Main Page ────────────────────────────────────────────────────────────────

export default function CorrespondentiePage() {
  const router = useRouter();
  // Tab state
  const [activeTab, setActiveTab] = useState<"alle" | "ongesorteerd" | "aanvragen">("alle");

  // Data hooks
  const { data: unlinkedData, isLoading } = useUnlinkedEmails(100);
  const { data: countData } = useUnlinkedCount();
  const { data: intakeCountData } = useIntakePendingCount();
  const createIntakeFromEmail = useCreateIntakeFromEmail();
  const syncEmails = useSyncEmails();
  const bulkLink = useBulkLinkEmails();
  const dismissEmails = useDismissEmails();
  const linkEmail = useLinkEmail();

  // UI state
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [emailFilter, setEmailFilter] = useState("");
  const [caseSearch, setCaseSearch] = useState("");
  const [showComposeDialog, setShowComposeDialog] = useState(false);
  const [replyPrefill, setReplyPrefill] = useState<ReplyPrefill | null>(null);
  // S223 — "AI-antwoord maken" op een inkomende mail van de wederpartij
  const [aiReplyEmail, setAiReplyEmail] = useState<SyncedEmailDetail | null>(null);

  // Free-compose verzending via OutlookProvider (geen dossier-context)
  const handleFreeComposeSend = async (data: EmailComposeData) => {
    const subject = data.custom_subject || "";
    const body = data.custom_body || "";
    try {
      const res = await api("/api/email/compose/send", {
        method: "POST",
        body: JSON.stringify({
          to: [data.recipient_email],
          subject,
          body_html: data.body_html || `<p>${body.replace(/\n/g, "<br>")}</p>`,
          cc: data.cc,
          bcc: data.bcc,
          case_id: data.case_id,
          case_file_ids: data.case_file_ids,
          inline_attachments: data.inline_attachments,
          reply_to_message_id: data.reply_to_message_id,
          references_root: data.references_root,
          forward_from_email_id: data.forward_from_email_id,
          already_branded: data.already_branded,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        const detail = err?.detail;
        const msg = typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join(", ")
            : "E-mail verzenden mislukt";
        throw new Error(msg);
      }
      toast.success("E-mail verzonden");
      setShowComposeDialog(false);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "E-mail verzenden mislukt");
    }
  };
  const debouncedSearch = useDebounce(caseSearch, 300);

  // "Alle e-mails": zoek server-side door de HÉLE mailbox (niet alleen de
  // geladen 200). Alleen actief op dit tabblad; de Ongesorteerd-tab filtert
  // client-side. Limiet 200 → toont de nieuwste 200 treffers; `total` toont
  // hoeveel er in totaal matchen.
  const debouncedEmailFilter = useDebounce(emailFilter, 300);
  const serverSearch =
    activeTab === "alle" && debouncedEmailFilter.trim()
      ? debouncedEmailFilter.trim()
      : undefined;
  const {
    data: allEmailsPages,
    isLoading: allLoading,
    fetchNextPage: allFetchNext,
    hasNextPage: allHasNext,
    isFetchingNextPage: allFetchingNext,
  } = useAllEmails("all", serverSearch);
  const allEmailsFlat = useMemo(
    () => allEmailsPages?.pages.flatMap((p) => p.emails) ?? [],
    [allEmailsPages]
  );
  const allEmailsTotal = allEmailsPages?.pages[0]?.total ?? 0;

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

  // Clear selection when the selected email is no longer in the visible list
  // (per tab). Bij tab-wissel wordt de selectie sowieso al gewist.
  useEffect(() => {
    const visible = activeTab === "alle" ? allEmailsFlat : allEmails;
    if (selectedEmailId && !visible.find((e) => e.id === selectedEmailId)) {
      setSelectedEmailId(null);
    }
  }, [activeTab, allEmails, allEmailsFlat, selectedEmailId]);

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleSync = () => {
    syncEmails.mutate(
      { maxResults: 100 },
      {
        onSuccess: (data) => {
          toast.success(buildSyncToastMessage(data));
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

  const handleMakeCaseFromEmail = (emailId: string) => {
    createIntakeFromEmail.mutate(
      { emailId },
      {
        onSuccess: () => {
          toast.success("Aanvraag gemaakt — controleer bij Nieuwe aanvragen");
          setSelectedEmailId(null);
          setActiveTab("aanvragen");
        },
        onError: (e) => toast.error(e instanceof Error ? e.message : "Aanvraag maken mislukt"),
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
            Mail
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
              {allEmailsTotal ? (
                <span className="ml-1.5 text-xs opacity-70">({allEmailsTotal})</span>
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
            <button
              onClick={() => { setActiveTab("aanvragen"); setSelectedEmailId(null); setSelectedIds(new Set()); }}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                activeTab === "aanvragen"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              Nieuwe aanvragen
              {intakeCountData?.count ? (
                <span className="ml-1.5 inline-flex items-center justify-center h-5 min-w-5 rounded-full bg-blue-500 text-white text-[10px] font-bold px-1.5">
                  {intakeCountData.count}
                </span>
              ) : null}
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
            size="sm"
            onClick={() => setShowComposeDialog(true)}
          >
            <Mail className="h-4 w-4 mr-2" />
            Nieuwe mail
          </Button>
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

      {/* Compose dialog — nieuw, beantwoorden of doorsturen */}
      {showComposeDialog && (
        <EmailComposeDialog
          open={showComposeDialog}
          onOpenChange={(open) => {
            setShowComposeDialog(open);
            if (!open) setReplyPrefill(null);
          }}
          title={
            replyPrefill
              ? replyPrefill.replyToMessageId
                ? "Beantwoorden"
                : "Doorsturen"
              : "Nieuwe e-mail"
          }
          defaultTo={replyPrefill?.to ?? ""}
          defaultToName={replyPrefill?.toName ?? ""}
          defaultSubject={replyPrefill?.subject ?? ""}
          defaultBodyHtml={replyPrefill?.bodyHtml ?? ""}
          replyToMessageId={replyPrefill?.replyToMessageId ?? null}
          referencesRoot={replyPrefill?.referencesRoot ?? null}
          forwardFromEmailId={replyPrefill?.forwardFromEmailId ?? null}
          caseId={emailDetail?.case_id ?? undefined}
          onSend={async (data) => {
            await handleFreeComposeSend(data);
          }}
          onSendDirect={async (data) => {
            await handleFreeComposeSend(data);
          }}
        />
      )}

      {/* AI-antwoord maken — concept op een inkomende mail van de wederpartij */}
      {aiReplyEmail && (
        <AiReplyDialog
          email={aiReplyEmail}
          onClose={() => setAiReplyEmail(null)}
          onOpenDraft={(draftId) =>
            router.push(`/zaken/${aiReplyEmail.case_id}?draft=${draftId}`)
          }
        />
      )}

      {/* Nieuwe aanvragen tab — bestaande intake-detectie zichtbaar */}
      {activeTab === "aanvragen" && <IntakeRequestsView />}

      {/* Alle e-mails tab — lijst + gedeeld leesvenster (zelfde als Ongesorteerd) */}
      {activeTab === "alle" && (
        <div className="flex gap-4">
          <div className={selectedEmailId ? "hidden lg:block lg:w-2/5" : "w-full"}>
            <AllEmailsView
              emails={allEmailsFlat}
              total={allEmailsTotal}
              isLoading={allLoading}
              emailFilter={debouncedEmailFilter}
              selectedId={selectedEmailId}
              onSelect={setSelectedEmailId}
              hasMore={!!allHasNext}
              isLoadingMore={allFetchingNext}
              onLoadMore={() => allFetchNext()}
            />
          </div>
          {selectedEmailId && emailDetail && (
            <div className="w-full lg:w-3/5 space-y-4">
              <button
                onClick={() => setSelectedEmailId(null)}
                className="lg:hidden inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                Terug naar lijst
              </button>
              <EmailDetailPanel
                email={emailDetail}
                onClose={() => setSelectedEmailId(null)}
                onReply={() => { setReplyPrefill(buildReplyPrefill(emailDetail)); setShowComposeDialog(true); }}
                onForward={() => { setReplyPrefill(buildForwardPrefill(emailDetail)); setShowComposeDialog(true); }}
                onAiReply={() => setAiReplyEmail(emailDetail)}
                suggestions={suggestData?.suggestions}
                suggestLoading={suggestLoading}
                caseSearch={caseSearch}
                onCaseSearchChange={setCaseSearch}
                caseResults={casesData?.items}
                showResults={debouncedSearch.length >= 2}
                onLinkToCase={(caseId) => handleLinkToCase(caseId, selectedEmailId!)}
                isLinking={linkEmail.isPending}
                onDismiss={() => handleDismiss(selectedEmailId!)}
                isDismissing={dismissEmails.isPending}
                onMakeCase={() => handleMakeCaseFromEmail(selectedEmailId!)}
                isMakingCase={createIntakeFromEmail.isPending}
              />
            </div>
          )}
        </div>
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
          {/* Email list — onder lg verborgen zodra een mail open is
              (detail wordt dan full-width i.p.v. een geplette split-view) */}
          <div
            className={selectedEmailId ? "hidden lg:block lg:w-2/5" : "w-full"}
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

          {/* Detail + action panel — gedeeld met "Alle e-mails" */}
          {selectedEmailId && emailDetail && (
            <div className="w-full lg:w-3/5 space-y-4">
              {/* Mobiel: terug naar de lijst */}
              <button
                onClick={() => setSelectedEmailId(null)}
                className="lg:hidden inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                Terug naar lijst
              </button>
              <EmailDetailPanel
                email={emailDetail}
                onClose={() => setSelectedEmailId(null)}
                onReply={() => { setReplyPrefill(buildReplyPrefill(emailDetail)); setShowComposeDialog(true); }}
                onForward={() => { setReplyPrefill(buildForwardPrefill(emailDetail)); setShowComposeDialog(true); }}
                onAiReply={() => setAiReplyEmail(emailDetail)}
                suggestions={suggestData?.suggestions}
                suggestLoading={suggestLoading}
                caseSearch={caseSearch}
                onCaseSearchChange={setCaseSearch}
                caseResults={casesData?.items}
                showResults={debouncedSearch.length >= 2}
                onLinkToCase={(caseId) => handleLinkToCase(caseId, selectedEmailId!)}
                isLinking={linkEmail.isPending}
                onDismiss={() => handleDismiss(selectedEmailId!)}
                isDismissing={dismissEmails.isPending}
                onMakeCase={() => handleMakeCaseFromEmail(selectedEmailId!)}
                isMakingCase={createIntakeFromEmail.isPending}
              />
            </div>
          )}
        </div>
      )}
      </>}
    </div>
  );
}

// ── Nieuwe aanvragen (intake) ───────────────────────────────────────────────

function formatEuro(amount: string | null): string {
  if (!amount) return "—";
  const n = Number(amount);
  if (Number.isNaN(n)) return amount;
  return new Intl.NumberFormat("nl-NL", { style: "currency", currency: "EUR" }).format(n);
}

function IntakeRequestsView() {
  const { data: intakes, isLoading } = useIntakes("pending_review");
  const approve = useApproveIntake();
  const reject = useRejectIntake();
  const [busyId, setBusyId] = useState<string | null>(null);

  const handleApprove = (intake: IntakeResponse) => {
    setBusyId(intake.id);
    approve.mutate(
      { id: intake.id },
      {
        onSuccess: (r) => toast.success(`Dossier ${r.created_case_number ?? ""} aangemaakt`),
        onError: (e) => toast.error(e instanceof Error ? e.message : "Goedkeuren mislukt"),
        onSettled: () => setBusyId(null),
      }
    );
  };

  const handleReject = (intake: IntakeResponse) => {
    setBusyId(intake.id);
    reject.mutate(
      { id: intake.id },
      {
        onSuccess: () => toast.success("Aanvraag afgewezen"),
        onError: (e) => toast.error(e instanceof Error ? e.message : "Afwijzen mislukt"),
        onSettled: () => setBusyId(null),
      }
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!intakes || intakes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
          <Inbox className="h-8 w-8 text-muted-foreground" />
        </div>
        <p className="mt-5 text-base font-medium text-foreground">Geen nieuwe aanvragen</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Nieuwe incasso-opdrachten van je opdrachtgevers verschijnen hier automatisch.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {intakes.map((intake) => {
        const busy = busyId === intake.id;
        return (
          <div key={intake.id} className="rounded-xl border border-border bg-card overflow-hidden">
            <div className="flex items-start justify-between gap-4 border-b border-border p-4">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="text-sm font-semibold truncate">
                    {intake.debtor_name || "Onbekende debiteur"}
                  </h3>
                  {intake.principal_amount && (
                    <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium">
                      {formatEuro(intake.principal_amount)}
                    </span>
                  )}
                  {intake.ai_confidence != null && (
                    <span className="rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-medium text-blue-700 ring-1 ring-inset ring-blue-600/20">
                      AI-zekerheid {Math.round(intake.ai_confidence * 100)}%
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Van {intake.client_name || intake.email_from} · {intake.email_subject}
                </p>
              </div>
              <a
                href={`/intake/${intake.id}`}
                className="shrink-0 text-xs font-medium text-primary hover:underline"
              >
                Details bewerken →
              </a>
            </div>

            {/* AI-uittreksel */}
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 p-4 text-sm sm:grid-cols-3">
              <IntakeField label="Debiteur" value={intake.debtor_name} />
              <IntakeField label="E-mail" value={intake.debtor_email} />
              <IntakeField label="KvK" value={intake.debtor_kvk} />
              <IntakeField label="Factuurnr." value={intake.invoice_number} />
              <IntakeField label="Vervaldatum" value={intake.due_date} />
              <IntakeField label="Hoofdsom" value={formatEuro(intake.principal_amount)} />
              {intake.description && (
                <div className="col-span-2 sm:col-span-3">
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Omschrijving</p>
                  <p className="text-sm text-foreground">{intake.description}</p>
                </div>
              )}
            </div>

            {/* Acties */}
            <div className="flex items-center gap-2 border-t border-border bg-muted/20 px-4 py-3">
              <Button size="sm" onClick={() => handleApprove(intake)} disabled={busy}>
                {busy ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Check className="h-4 w-4 mr-1" />}
                Maak dossier
              </Button>
              <Button variant="ghost" size="sm" className="text-muted-foreground" onClick={() => handleReject(intake)} disabled={busy}>
                <XCircle className="h-4 w-4 mr-1" />
                Afwijzen
              </Button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function IntakeField({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="min-w-0">
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="truncate text-sm text-foreground">{value || "—"}</p>
    </div>
  );
}

// ── Gedeeld leesvenster (Ongesorteerd + Alle e-mails) ───────────────────────

interface CaseSearchResult {
  id: string;
  case_number: string;
  description?: string | null;
  client?: { name?: string } | null;
}

function EmailDetailPanel({
  email,
  onClose,
  onReply,
  onForward,
  onAiReply,
  suggestions,
  suggestLoading,
  caseSearch,
  onCaseSearchChange,
  caseResults,
  showResults,
  onLinkToCase,
  isLinking,
  onDismiss,
  isDismissing,
  onMakeCase,
  isMakingCase,
}: {
  email: SyncedEmailDetail;
  onClose: () => void;
  onReply: () => void;
  onForward: () => void;
  onAiReply: () => void;
  suggestions?: CaseSuggestion[];
  suggestLoading: boolean;
  caseSearch: string;
  onCaseSearchChange: (v: string) => void;
  caseResults?: CaseSearchResult[];
  showResults: boolean;
  onLinkToCase: (caseId: string) => void;
  isLinking: boolean;
  onDismiss: () => void;
  isDismissing: boolean;
  onMakeCase?: () => void;
  isMakingCase?: boolean;
}) {
  return (
    <>
      {/* Email detail */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 border-b border-border p-4">
          <div className="min-w-0 flex-1">
            <h3 className="text-sm font-semibold truncate">
              {email.subject || "(Geen onderwerp)"}
            </h3>
            <div className="mt-1 space-y-0.5 text-xs text-muted-foreground">
              <p>
                <span className="font-medium text-foreground">Van:</span>{" "}
                {email.from_name
                  ? `${email.from_name} <${email.from_email}>`
                  : email.from_email}
              </p>
              <p>
                <span className="font-medium text-foreground">Aan:</span>{" "}
                {email.to_emails.join(", ")}
              </p>
              {email.cc_emails.length > 0 && (
                <p>
                  <span className="font-medium text-foreground">CC:</span>{" "}
                  {email.cc_emails.join(", ")}
                </p>
              )}
              <p>
                <span className="font-medium text-foreground">Datum:</span>{" "}
                {new Date(email.email_date).toLocaleString("nl-NL", {
                  day: "numeric",
                  month: "long",
                  year: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            {email.direction === "inbound" && email.case_id && (
              <button
                onClick={onAiReply}
                title="AI schrijft een concept-antwoord op deze mail"
                className="inline-flex items-center gap-1 rounded-md border border-primary/30 bg-primary/5 px-2 py-1 text-xs font-medium text-primary hover:bg-primary/10 transition-colors"
              >
                <Sparkles className="h-3.5 w-3.5" /> AI-antwoord maken
              </button>
            )}
            <button
              onClick={onReply}
              className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs font-medium hover:bg-muted transition-colors"
            >
              <Reply className="h-3.5 w-3.5" /> Beantwoorden
            </button>
            <button
              onClick={onForward}
              className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs font-medium hover:bg-muted transition-colors"
            >
              <Forward className="h-3.5 w-3.5" /> Doorsturen
            </button>
            <button
              onClick={onClose}
              aria-label="E-mail sluiten"
              className="rounded-md p-1 hover:bg-muted transition-colors"
            >
              <XCircle className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
        </div>

        {/* Attachments */}
        {email.attachments.length > 0 && (
          <div className="border-b border-border px-4 py-3 flex flex-wrap gap-2">
            {email.attachments.map((att) => (
              <a
                key={att.id}
                href={`/api/email/attachments/${att.id}/download`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-muted/30 px-2.5 py-1.5 text-xs font-medium hover:bg-muted/60 transition-colors"
              >
                <File className="h-3 w-3" />
                <span className="max-w-[150px] truncate">{att.filename}</span>
                <span className="text-muted-foreground">
                  ({formatFileSize(att.file_size)})
                </span>
              </a>
            ))}
          </div>
        )}

        {/* Body */}
        <div className="p-4 overflow-auto max-h-[400px]">
          {email.body_html ? (
            <div
              className="prose prose-sm max-w-none text-foreground"
              dangerouslySetInnerHTML={{ __html: sanitizeHtml(email.body_html) }}
            />
          ) : (
            <pre className="text-sm text-foreground whitespace-pre-wrap font-sans">
              {email.body_text || email.snippet}
            </pre>
          )}
        </div>
      </div>

      {/* Action panel: Link to case */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="p-4 space-y-4">
          <h4 className="text-sm font-semibold flex items-center gap-2">
            <Briefcase className="h-4 w-4" />
            {email.case_number ? "Gekoppeld dossier" : "Koppel aan dossier"}
          </h4>

          {/* Al gekoppeld → toon het dossier met snelkoppeling */}
          {email.case_number && (
            <a
              href={`/zaken/${email.case_id}`}
              className="flex items-center gap-2 rounded-md border border-emerald-600/20 bg-emerald-50 px-3 py-1.5 text-sm font-medium text-emerald-700 hover:bg-emerald-100 transition-colors"
            >
              <Briefcase className="h-3.5 w-3.5" />
              {email.case_number}
              <span className="ml-auto text-xs">Open dossier →</span>
            </a>
          )}

          {/* Suggestions */}
          {suggestLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" />
              Suggesties laden...
            </div>
          ) : (
            suggestions &&
            suggestions.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs text-muted-foreground font-medium">Suggesties</p>
                {suggestions.map((s) => (
                  <SuggestionItem
                    key={s.case_id}
                    suggestion={s}
                    onLink={() => onLinkToCase(s.case_id)}
                    isLinking={isLinking}
                  />
                ))}
              </div>
            )
          )}

          {/* Manual search */}
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground font-medium">
              {email.case_number ? "Koppel aan een ander dossier" : "Of zoek handmatig"}
            </p>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                placeholder="Zoek op dossiernummer, naam of cliënt..."
                className="pl-9 h-9 text-sm"
                value={caseSearch}
                onChange={(e) => onCaseSearchChange(e.target.value)}
              />
            </div>
            {showResults && caseResults && (
              <div className="rounded-lg border border-border divide-y divide-border max-h-[200px] overflow-auto">
                {caseResults.length === 0 ? (
                  <p className="px-3 py-2 text-xs text-muted-foreground">
                    Geen dossiers gevonden
                  </p>
                ) : (
                  caseResults.map((c) => (
                    <button
                      key={c.id}
                      onClick={() => onLinkToCase(c.id)}
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

          {/* Extra acties voor niet-gekoppelde mail */}
          {!email.case_number && (
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-border">
              {onMakeCase && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onMakeCase}
                  disabled={isMakingCase}
                >
                  {isMakingCase ? (
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  ) : (
                    <Briefcase className="h-4 w-4 mr-1" />
                  )}
                  Maak dossier van deze mail
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                className="text-muted-foreground"
                onClick={onDismiss}
                disabled={isDismissing}
              >
                <EyeOff className="h-4 w-4 mr-1" />
                Negeren — niet relevant
              </Button>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

// ── All Emails View ─────────────────────────────────────────────────────────

function AllEmailsView({
  emails,
  total,
  isLoading,
  emailFilter,
  selectedId,
  onSelect,
  hasMore,
  isLoadingMore,
  onLoadMore,
}: {
  emails: SyncedEmailSummary[];
  total: number;
  isLoading: boolean;
  emailFilter: string;
  selectedId: string | null;
  onSelect: (id: string) => void;
  hasMore: boolean;
  isLoadingMore: boolean;
  onLoadMore: () => void;
}) {
  // Server heeft al gefilterd/gezocht — hier alleen groeperen op datum.
  const grouped = useMemo(() => {
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (emails.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
          <Inbox className="h-8 w-8 text-muted-foreground" />
        </div>
        <p className="mt-5 text-base font-medium text-foreground">Geen e-mails</p>
        <p className="mt-1 text-sm text-muted-foreground">
          {emailFilter ? "Geen e-mails gevonden voor deze zoekopdracht" : "Er zijn nog geen e-mails gesynchroniseerd"}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* Teller — `total` is het totaal aantal treffers; de lijst groeit met
          "meer laden". */}
      <p className="px-1 text-xs text-muted-foreground">
        {emailFilter
          ? `${total} resultaten voor "${emailFilter}"${total > emails.length ? ` — ${emails.length} getoond` : ""}`
          : `${total} e-mails${total > emails.length ? ` — ${emails.length} getoond` : ""}`}
      </p>
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
              role="button"
              tabIndex={0}
              onClick={() => onSelect(email.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelect(email.id);
                }
              }}
              className={`flex items-start gap-3 px-4 py-3 border-b border-border/50 cursor-pointer transition-colors border-l-3 ${
                email.direction === "inbound"
                  ? "border-l-blue-500"
                  : "border-l-emerald-500"
              } ${selectedId === email.id ? "bg-muted" : "hover:bg-muted/30"}`}
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
                  {!email.is_read && (
                    <span className="h-2 w-2 shrink-0 rounded-full bg-blue-500" aria-label="Ongelezen" />
                  )}
                  <span className={`text-sm truncate ${email.is_read ? "font-medium text-foreground" : "font-bold text-foreground"}`}>
                    {email.from_name || email.from_email}
                  </span>
                  <span className="text-[11px] text-muted-foreground shrink-0">
                    {formatRelativeTime(email.email_date)}
                  </span>
                  {email.has_attachments && (
                    <Paperclip className="h-3 w-3 text-muted-foreground shrink-0" />
                  )}
                </div>
                <p className={`text-sm text-foreground truncate ${email.is_read ? "" : "font-semibold"}`}>{email.subject}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <p className="text-xs text-muted-foreground truncate flex-1">{email.snippet}</p>
                  {email.case_number ? (
                    <a
                      href={`/zaken/${email.case_id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center gap-1 shrink-0 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20 hover:bg-emerald-100 transition-colors"
                    >
                      <Briefcase className="h-2.5 w-2.5" />
                      {email.case_number}
                    </a>
                  ) : (
                    <span className="inline-flex items-center gap-1 shrink-0 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700 ring-1 ring-inset ring-amber-600/20">
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
    {hasMore && (
      <div className="flex justify-center pt-2">
        <Button variant="outline" size="sm" onClick={onLoadMore} disabled={isLoadingMore}>
          {isLoadingMore ? (
            <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Laden...</>
          ) : (
            "Meer laden"
          )}
        </Button>
      </div>
    )}
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
    ? "border-l-blue-500"
    : "border-l-emerald-500";

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect();
        }
      }}
      aria-label={`E-mail openen: ${email.subject || "(Geen onderwerp)"}`}
      className={`flex items-start gap-3 px-4 py-3 hover:bg-muted/30 transition-colors cursor-pointer border-l-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary/40 ${
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
        onKeyDown={(e) => e.stopPropagation()}
        aria-label={isChecked ? "E-mail deselecteren" : "E-mail selecteren"}
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
            ? "bg-blue-100"
            : "bg-emerald-100"
        }`}
      >
        {email.direction === "inbound" ? (
          <ArrowDownLeft
            className={`h-3.5 w-3.5 ${
              email.direction === "inbound"
                ? "text-blue-600"
                : "text-emerald-600"
            }`}
          />
        ) : (
          <ArrowUpRight className="h-3.5 w-3.5 text-emerald-600" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
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
        {/* S221 punt 18 — dossiernummer direct klikbaar in de lijstrij (voorheen
            alleen in het detailpaneel). stopPropagation zodat de klik navigeert
            i.p.v. de mail te openen. */}
        {email.case_id && email.case_number && (
          <a
            href={`/zaken/${email.case_id}`}
            onClick={(e) => e.stopPropagation()}
            className="mt-1 inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
          >
            <Briefcase className="h-3 w-3" />
            {email.case_number}
          </a>
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
      <div className="h-14 w-14 rounded-2xl bg-emerald-100 flex items-center justify-center mb-4">
        <Inbox className="h-7 w-7 text-emerald-600" />
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
