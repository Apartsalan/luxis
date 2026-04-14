"use client";

import { useState, useEffect, useRef } from "react";
import { useConfirm, usePrompt } from "@/components/confirm-dialog";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Bot,
  Briefcase,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  CreditCard,
  Euro,
  File,
  Loader2,
  Mail,
  Receipt,
  Users,
  X,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { useCase, useUpdateCaseStatus, useDeleteCase } from "@/hooks/use-cases";
import {
  getTemplatesForStatus,
  useSendCaseEmail,
  type EmailLogEntry,
} from "@/hooks/use-documents";
import {
  EmailComposeDialog,
  type EmailComposeData,
  type EmailRecipient,
} from "@/components/email-compose-dialog";
import {
  useWorkflowStatuses,
  useWorkflowTransitions,
} from "@/hooks/use-workflow";
import { useModules } from "@/hooks/use-modules";
import { useTimer, useAutoTimerPreference, AUTO_SAVE_MIN_SECONDS } from "@/hooks/use-timer";
import { useBreadcrumbs } from "@/components/layout/breadcrumb-context";
import { useSendViaProvider } from "@/hooks/use-email-sync";
import { useFollowupForCase, useApproveAndExecuteFollowup } from "@/hooks/use-followup";
import {
  useClassifications,
  useApproveAndExecuteClassification,
  useRejectClassification,
  type Classification,
} from "@/hooks/use-ai-agent";
import { api } from "@/lib/api";
import { confidenceLabelText, confidenceTextColor as confidenceTextCls } from "@/lib/confidence";
import { STATUS_LABELS } from "./types";

// ── Tab components ───────────────────────────────────────────────────────────
import DossierHeader from "./components/DossierHeader";
import DetailsTab from "./components/DetailsTab";
import TijdregistratieTab from "./components/TijdregistratieTab";
import UrenTab from "./components/UrenTab";
import { VorderingenFinancieelTab, BetalingenDerdengeldenTab } from "./components/incasso";
import { FacturenTab, DocumentenTab } from "./components/DocumentenTab";
import CorrespondentieTab from "./components/CorrespondentieTab";
import ActiviteitenTab from "./components/ActiviteitenTab";
import PartijenTab from "./components/PartijenTab";
import DossierSidebar from "./components/DossierSidebar";
import { ErrorBoundary } from "@/components/error-boundary";

function TabErrorFallback({ tabName }: { tabName: string }) {
  return (
    <div className="flex items-center justify-center rounded-xl border border-dashed border-destructive/30 bg-destructive/5 py-12">
      <div className="text-center">
        <p className="text-sm font-medium text-destructive">
          Er ging iets mis in het tabblad &quot;{tabName}&quot;
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          De overige tabbladen werken nog normaal.
        </p>
      </div>
    </div>
  );
}

export default function ZaakDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const id = params.id as string;
  const { data: zaak, isLoading } = useCase(id);
  const updateStatus = useUpdateCaseStatus();
  const deleteCase = useDeleteCase();
  const { confirm, ConfirmDialog: ConfirmDialogEl } = useConfirm();
  const { prompt: promptDialog, PromptDialog: PromptDialogEl } = usePrompt();
  const { data: workflowStatuses } = useWorkflowStatuses();
  const { data: workflowTransitions } = useWorkflowTransitions();

  const { data: followupData } = useFollowupForCase(id);
  const followupRec = followupData?.items?.[0] ?? null;
  const approveAndExecuteFollowup = useApproveAndExecuteFollowup();

  // AI-UX-04: pending classifications for this case
  const { data: pendingClassifications } = useClassifications("pending", id, 1, 1);
  const latestPendingClassification = pendingClassifications?.[0] ?? null;
  const approveClassification = useApproveAndExecuteClassification();
  const rejectClassification = useRejectClassification();
  const [aiBannerCollapsed, setAiBannerCollapsed] = useState(false);
  const [aiBannerDismissed, setAiBannerDismissed] = useState(false);

  // Set breadcrumb label to case number
  useBreadcrumbs(zaak ? [{ segment: id, label: zaak.case_number }] : []);
  const { hasModule } = useModules();
  const { startTimer, stopTimer, discardTimer, timer } = useTimer();
  const [autoTimerEnabled] = useAutoTimerPreference();
  const tabFromUrl = searchParams.get("tab");
  const [activeTab, setActiveTab] = useState(tabFromUrl || "overzicht");
  const [phoneNoteText, setPhoneNoteText] = useState("");
  const autoStartedRef = useRef<string | null>(null);

  // T2: Workflow-suggestie banner state
  const [statusSuggestion, setStatusSuggestion] = useState<{ status: string; templates: string[] } | null>(null);

  // Auto-start timer when opening a case (if enabled)
  useEffect(() => {
    if (!autoTimerEnabled || !zaak) return;

    // Already auto-started for this case in this render cycle
    if (autoStartedRef.current === zaak.id) return;

    // Timer already running for THIS case — do nothing
    if (timer.running && timer.caseId === zaak.id) {
      autoStartedRef.current = zaak.id;
      return;
    }

    // Timer running for ANOTHER case — save/discard + start new
    if (timer.running && timer.caseId !== zaak.id) {
      const prevName = timer.caseName;
      const prevSeconds = timer.seconds;
      if (prevSeconds >= AUTO_SAVE_MIN_SECONDS) {
        stopTimer().then(() => {
          const m = Math.max(1, Math.round(prevSeconds / 60));
          const h = Math.floor(m / 60);
          const min = m % 60;
          toast.info(
            `${h}:${String(min).padStart(2, "0")} opgeslagen voor ${prevName}`
          );
        });
      } else {
        discardTimer();
      }
    }

    // Start timer for current case
    const label = `${zaak.case_number}${zaak.client ? ` — ${zaak.client.name}` : ""}`;
    const timeout = timer.running && timer.caseId !== zaak.id ? 300 : 0;
    const t = setTimeout(() => {
      startTimer(zaak.id, label);
      toast.info(`Timer gestart voor ${zaak.case_number}`, { duration: 2000 });
    }, timeout);
    autoStartedRef.current = zaak.id;

    return () => clearTimeout(t);
  }, [zaak?.id, autoTimerEnabled]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleStatusChange = async (newStatus: string) => {
    const note = await promptDialog({ title: "Statuswijziging", description: "Notitie bij statuswijziging (optioneel):", placeholder: "Typ een notitie...", confirmText: "Wijzigen" });
    try {
      await updateStatus.mutateAsync({
        id,
        new_status: newStatus,
        note: note?.trim() || null,
      });
      toast.success(`Status gewijzigd naar ${STATUS_LABELS[newStatus]}`);

      // T2: Toon suggestie-banner als er aanbevolen templates zijn
      const nextTemplates = getTemplatesForStatus(newStatus, zaak?.debtor_type);
      if (nextTemplates.recommended.length > 0) {
        setStatusSuggestion({ status: newStatus, templates: nextTemplates.recommended });
        setTimeout(() => setStatusSuggestion(null), 30000);
      }
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Statuswijziging mislukt");
    }
  };

  const handleDelete = async () => {
    if (!await confirm({ title: "Dossier verwijderen", description: "Weet je zeker dat je dit dossier wilt verwijderen?", variant: "destructive", confirmText: "Verwijderen" })) return;
    try {
      await deleteCase.mutateAsync(id);
      toast.success("Dossier verwijderd");
      router.push("/zaken");
    } catch {
      toast.error("Kon het dossier niet verwijderen");
    }
  };

  // ── Freestanding email compose (F11) ────────────────────────────────────
  const [caseEmailOpen, setCaseEmailOpen] = useState(false);
  const sendCaseEmail = useSendCaseEmail(id);
  const sendViaProvider = useSendViaProvider(id);

  function buildDossierRecipients(z: typeof zaak): EmailRecipient[] {
    if (!z) return [];
    const recipients: EmailRecipient[] = [];
    if (z.client?.email) {
      recipients.push({ name: z.client.name, email: z.client.email, role: "client" });
    }
    if (z.opposing_party?.email) {
      recipients.push({ name: z.opposing_party.name, email: z.opposing_party.email, role: "opposing_party" });
    }
    if (z.parties) {
      for (const p of z.parties) {
        if (p.contact?.email && !recipients.some((r) => r.email === p.contact.email)) {
          recipients.push({ name: p.contact.name, email: p.contact.email, role: p.role });
        }
      }
    }
    return recipients;
  }

  const handleOpenInOutlook = async (data: EmailComposeData) => {
    const subject = data.custom_subject || `${zaak?.case_number || ""}`;
    const body = data.custom_body || "";

    try {
      const res = await api(`/api/email/compose/cases/${id}`, {
        method: "POST",
        body: JSON.stringify({
          recipient_email: data.recipient_email,
          recipient_name: data.recipient_name,
          cc: data.cc,
          subject,
          body,
          body_html: data.body_html,
          case_file_ids: data.case_file_ids,
          inline_attachments: data.inline_attachments,
          template_type: data.template_type,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "E-mail opstellen mislukt");
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `email-${zaak?.case_number || "concept"}.eml`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast.success("E-mail geopend in Outlook");
      setCaseEmailOpen(false);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "E-mail opstellen mislukt");
    }
  };

  const handleDirectSend = async (data: EmailComposeData) => {
    const subject = data.custom_subject || `${zaak?.case_number || ""}`;
    const body = data.custom_body || "";

    try {
      const res = await api("/api/email/compose/send", {
        method: "POST",
        body: JSON.stringify({
          to: data.recipient_email,
          subject,
          body_html: data.body_html || `<p>${body.replace(/\n/g, "<br>")}</p>`,
          cc: data.cc,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "E-mail verzenden mislukt");
      }

      toast.success("E-mail verzonden via Outlook");
      setCaseEmailOpen(false);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "E-mail verzenden mislukt");
    }
  };

  // G5: Keyboard shortcuts (Linear-style)
  // Tab IDs for numeric shortcuts — order matches the tab bar
  const isIncasso = hasModule("incasso") && zaak?.case_type === "incasso";
  const tabIds = [
    "overzicht", "taken", "uren",
    ...(isIncasso ? ["vorderingen", "betalingen", "derdengelden"] : []),
    "facturen", "documenten", "correspondentie", "activiteiten", "partijen",
  ];

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger when typing in inputs/textareas or when modifier keys are held
      const tag = (e.target as HTMLElement).tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (e.target as HTMLElement).isContentEditable) return;
      if (e.ctrlKey || e.metaKey || e.altKey) return;

      switch (e.key.toLowerCase()) {
        case "t":
          e.preventDefault();
          if (timer.running && timer.caseId === id) {
            stopTimer();
            toast.info("Timer gestopt");
          } else if (zaak) {
            const label = `${zaak.case_number}${zaak.client ? ` — ${zaak.client.name}` : ""}`;
            startTimer(zaak.id, label);
            toast.info("Timer gestart");
          }
          break;
        case "n":
          e.preventDefault();
          setActiveTab("overzicht");
          // Focus the note textarea after tab switch
          setTimeout(() => {
            const textarea = document.querySelector<HTMLTextAreaElement>('textarea[placeholder="Schrijf een notitie..."]');
            textarea?.focus();
          }, 100);
          break;
        case "d":
          e.preventDefault();
          setActiveTab("documenten");
          break;
        case "e":
          e.preventDefault();
          setCaseEmailOpen(true);
          break;
        case "f":
          e.preventDefault();
          setActiveTab("facturen");
          break;
        default:
          // 1-9: switch tabs
          if (e.key >= "1" && e.key <= "9") {
            const idx = parseInt(e.key) - 1;
            if (idx < tabIds.length) {
              e.preventDefault();
              setActiveTab(tabIds[idx]);
            }
          }
          break;
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [timer.running, timer.caseId, id, zaak, tabIds.length]); // eslint-disable-line react-hooks/exhaustive-deps

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
        <div className="h-10 rounded-lg skeleton" />
        <div className="h-64 rounded-xl skeleton" />
      </div>
    );
  }

  if (!zaak) {
    return (
      <div className="py-20 text-center">
        <Briefcase className="mx-auto h-12 w-12 text-muted-foreground/30" />
        <p className="mt-4 text-base font-medium text-foreground">
          Dossier niet gevonden
        </p>
        <Link
          href="/zaken"
          className="mt-2 inline-block text-sm text-primary hover:underline"
        >
          ← Terug naar dossiers
        </Link>
      </div>
    );
  }

  const tabs = [
    { id: "overzicht", label: "Overzicht", icon: Briefcase },
    { id: "taken", label: "Taken", icon: CheckCircle2 },
    { id: "uren", label: "Uren", icon: Clock },
    ...(isIncasso
      ? [
          { id: "vorderingen", label: "Vorderingen", icon: Euro },
          { id: "betalingen", label: "Betalingen", icon: Receipt },
        ]
      : []),
    { id: "facturen", label: "Facturen", icon: CreditCard },
    { id: "documenten", label: "Documenten", icon: File },
    { id: "correspondentie", label: "Correspondentie", icon: Mail },
    { id: "activiteiten", label: "Activiteiten", icon: Clock },
    { id: "partijen", label: "Partijen", icon: Users },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {ConfirmDialogEl}
      {PromptDialogEl}
      <DossierHeader
        zaak={zaak}
        isIncasso={isIncasso}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        handleStatusChange={handleStatusChange}
        handleDelete={handleDelete}
        updateStatusPending={updateStatus.isPending}
        statusSuggestion={statusSuggestion}
        setStatusSuggestion={setStatusSuggestion}
        workflowStatuses={workflowStatuses}
        workflowTransitions={workflowTransitions}
        timer={timer}
        startTimer={startTimer}
        setCaseEmailOpen={setCaseEmailOpen}
        setPhoneNoteText={setPhoneNoteText}
      />

      {/* AI-UX-04: AI suggestion banner */}
      {!aiBannerDismissed && (latestPendingClassification || followupRec) && (
        <div className="rounded-xl border border-primary/20 bg-primary/5 overflow-hidden">
          {/* Header — clickable to collapse */}
          <button
            type="button"
            onClick={() => setAiBannerCollapsed(!aiBannerCollapsed)}
            className="w-full flex items-center justify-between px-4 py-3 hover:bg-primary/10 transition-colors"
          >
            <div className="flex items-center gap-2">
              <Bot className="h-4 w-4 text-primary" />
              <span className="text-sm font-semibold text-foreground">
                AI-suggestie
              </span>
              <span className="rounded-md bg-violet-100 dark:bg-violet-900/30 px-1.5 py-0.5 text-[9px] font-semibold text-violet-700 dark:text-violet-400 uppercase tracking-wider">
                AI
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); setAiBannerDismissed(true); }}
                className="rounded-md p-1 hover:bg-muted transition-colors"
                title="Verberg"
              >
                <X className="h-3.5 w-3.5 text-muted-foreground" />
              </button>
              {aiBannerCollapsed ? (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronUp className="h-4 w-4 text-muted-foreground" />
              )}
            </div>
          </button>

          {/* Content — collapsible */}
          {!aiBannerCollapsed && (
            <div className="px-4 pb-4 space-y-3">
              {/* Pending classification */}
              {latestPendingClassification && (
                <div className="flex items-center justify-between gap-3 rounded-lg border border-border bg-card p-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <Mail className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                      <p className="text-sm font-medium text-foreground truncate">
                        {latestPendingClassification.category_label}
                      </p>
                      <span className={`shrink-0 text-[10px] font-medium ${confidenceTextCls(latestPendingClassification.confidence)}`}>
                        {confidenceLabelText(latestPendingClassification.confidence)}
                      </span>
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground truncate pl-5.5">
                      {latestPendingClassification.suggested_action_label}
                      {latestPendingClassification.email_subject && ` — "${latestPendingClassification.email_subject}"`}
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      type="button"
                      onClick={() => {
                        approveClassification.mutate(
                          { id: latestPendingClassification.id },
                          { onSuccess: () => toast.success("Classificatie goedgekeurd en uitgevoerd") },
                        );
                      }}
                      disabled={approveClassification.isPending || rejectClassification.isPending}
                      className="inline-flex items-center gap-1 rounded-md bg-emerald-600 px-2.5 py-1.5 text-[11px] font-medium text-white hover:bg-emerald-700 disabled:opacity-50 transition-colors"
                    >
                      {approveClassification.isPending ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <Check className="h-3 w-3" />
                      )}
                      Akkoord + Uitvoeren
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        rejectClassification.mutate(
                          { id: latestPendingClassification.id },
                          { onSuccess: () => toast.success("Classificatie afgewezen") },
                        );
                      }}
                      disabled={approveClassification.isPending || rejectClassification.isPending}
                      className="inline-flex items-center gap-1 rounded-md border border-border bg-background px-2.5 py-1.5 text-[11px] font-medium text-muted-foreground hover:bg-muted/50 disabled:opacity-50 transition-colors"
                    >
                      {rejectClassification.isPending ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <X className="h-3 w-3" />
                      )}
                      Afwijzen
                    </button>
                  </div>
                </div>
              )}

              {/* Followup recommendation */}
              {followupRec && (
                <div className="flex items-center justify-between gap-3 rounded-lg border border-border bg-card p-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <Zap className="h-3.5 w-3.5 text-amber-600 shrink-0" />
                      <p className="text-sm font-medium text-foreground truncate">
                        {followupRec.action_label}
                      </p>
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground truncate pl-5.5">
                      {followupRec.reasoning}
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      type="button"
                      onClick={() => {
                        approveAndExecuteFollowup.mutate(
                          { id: followupRec.id },
                          { onSuccess: () => toast.success("Aanbeveling uitgevoerd") },
                        );
                      }}
                      disabled={approveAndExecuteFollowup.isPending}
                      className="inline-flex items-center gap-1 rounded-md bg-amber-600 px-2.5 py-1.5 text-[11px] font-medium text-white hover:bg-amber-700 disabled:opacity-50 transition-colors"
                    >
                      <CheckCircle2 className="h-3 w-3" />
                      Uitvoeren
                    </button>
                    <Link
                      href="/followup"
                      className="text-[11px] text-muted-foreground hover:text-foreground hover:underline"
                    >
                      Details
                    </Link>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Main content + sidebar */}
      <div className="flex gap-6">
        <div className="min-w-0 flex-1">
          {/* Tabs — sticky under app header (UX-6: scroll indicators, UX-7: sticky) */}
          <div className="sticky top-14 z-30 bg-background -mx-4 sm:-mx-6 px-4 sm:px-6">
            <div className="relative">
              <div className="border-b border-border overflow-x-auto">
                <nav className="flex gap-0.5 min-w-max">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap ${
                        activeTab === tab.id
                          ? "border-primary text-primary"
                          : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                      }`}
                    >
                      <tab.icon className="h-4 w-4" />
                      {tab.label}
                    </button>
                  ))}
                </nav>
              </div>
            </div>
          </div>

          {/* Tab content — each tab wrapped in ErrorBoundary (UX-19) */}
          <div className="mt-6">
            {activeTab === "overzicht" && (
              <ErrorBoundary key="overzicht" fallback={<TabErrorFallback tabName="Overzicht" />}>
                <DetailsTab zaak={zaak} initialNoteText={phoneNoteText} onNoteTextConsumed={() => setPhoneNoteText("")} />
              </ErrorBoundary>
            )}
            {activeTab === "taken" && (
              <ErrorBoundary key="taken" fallback={<TabErrorFallback tabName="Taken" />}>
                <TijdregistratieTab caseId={id} />
              </ErrorBoundary>
            )}
            {activeTab === "uren" && (
              <ErrorBoundary key="uren" fallback={<TabErrorFallback tabName="Uren" />}>
                <UrenTab caseId={id} />
              </ErrorBoundary>
            )}
            {isIncasso && activeTab === "vorderingen" && (
              <ErrorBoundary key="vorderingen" fallback={<TabErrorFallback tabName="Vorderingen" />}>
                <VorderingenFinancieelTab caseId={id} />
              </ErrorBoundary>
            )}
            {isIncasso && activeTab === "betalingen" && (
              <ErrorBoundary key="betalingen" fallback={<TabErrorFallback tabName="Betalingen" />}>
                <BetalingenDerdengeldenTab caseId={id} />
              </ErrorBoundary>
            )}
            {activeTab === "facturen" && (
              <ErrorBoundary key="facturen" fallback={<TabErrorFallback tabName="Facturen" />}>
                <FacturenTab caseId={id} clientId={zaak?.client?.id} />
              </ErrorBoundary>
            )}
            {activeTab === "documenten" && (
              <ErrorBoundary key="documenten" fallback={<TabErrorFallback tabName="Documenten" />}>
                <DocumentenTab caseId={id} caseNumber={zaak?.case_number} caseStatus={zaak?.status} debtorType={zaak?.debtor_type} opposingPartyName={zaak?.opposing_party?.name} />
              </ErrorBoundary>
            )}
            {activeTab === "correspondentie" && (
              <ErrorBoundary key="correspondentie" fallback={<TabErrorFallback tabName="Correspondentie" />}>
                <CorrespondentieTab caseId={id} onCompose={() => setCaseEmailOpen(true)} />
              </ErrorBoundary>
            )}
            {activeTab === "activiteiten" && (
              <ErrorBoundary key="activiteiten" fallback={<TabErrorFallback tabName="Activiteiten" />}>
                <ActiviteitenTab zaak={zaak} />
              </ErrorBoundary>
            )}
            {activeTab === "partijen" && (
              <ErrorBoundary key="partijen" fallback={<TabErrorFallback tabName="Partijen" />}>
                <PartijenTab zaak={zaak} />
              </ErrorBoundary>
            )}
          </div>
        </div>

        {/* G14: Properties sidebar */}
        <DossierSidebar zaak={zaak} isIncasso={isIncasso} />
      </div>

      {/* Freestanding email compose dialog (F11) */}
      <EmailComposeDialog
        open={caseEmailOpen}
        onOpenChange={setCaseEmailOpen}
        onSend={handleOpenInOutlook}
        onSendDirect={handleDirectSend}
        isSending={sendCaseEmail.isPending}
        title="E-mail opstellen"
        defaultSubject={zaak ? `${zaak.case_number}${zaak.client ? ` — ${zaak.client.name}` : ""}` : ""}
        recipients={zaak ? buildDossierRecipients(zaak) : []}
        caseId={id}
      />
    </div>
  );
}
