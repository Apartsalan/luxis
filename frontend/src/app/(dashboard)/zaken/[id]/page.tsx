"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Briefcase,
  Clock,
  Download,
  File,
  Users,
  Trash2,
  ChevronRight,
  Euro,
  FileText,
  Loader2,
  Plus,
  Receipt,
  Wallet,
  CheckCircle2,
  AlertTriangle,
  Building2,
  User,
  CalendarDays,
  ArrowRight,
  CreditCard,
  Phone,
  Mail,
  MessageSquare,
  Send,
  ArrowUpDown,
  ArrowDownLeft,
  ArrowUpRight,
  ChevronLeft,
  ShieldCheck,
  XCircle,
  Ban,
  Upload,
  Star,
  ChevronDown,
} from "lucide-react";
import { toast } from "sonner";
import {
  useCase,
  useUpdateCaseStatus,
  useDeleteCase,
  useCaseActivities,
  useAddCaseActivity,
  useConflictCheck,
  type CaseActivity,
} from "@/hooks/use-cases";
import {
  useClaims,
  useCreateClaim,
  useDeleteClaim,
  usePayments,
  useCreatePayment,
  useCaseInterest,
  useFinancialSummary,
  useDerdengelden,
  useDerdengeldenBalance,
  useCreateDerdengelden,
  useApproveTrustTransaction,
  useRejectTrustTransaction,
} from "@/hooks/use-collections";
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
  useEmailLogs,
  type EmailLogEntry,
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
} from "@/hooks/use-case-files";
import {
  useWorkflowStatuses,
  useWorkflowTransitions,
  useWorkflowTasks,
  useCompleteTask,
  useSkipTask,
  useCreateTask,
  groupStatusesByPhase,
  getAvailableTransitions,
  getPhaseForStatus,
  PHASE_LABELS,
  PHASE_ORDER,
  TASK_TYPE_LABELS,
  TASK_STATUS_LABELS,
} from "@/hooks/use-workflow";
import { useModules } from "@/hooks/use-modules";
import { useTimer, useAutoTimerPreference, AUTO_SAVE_MIN_SECONDS } from "@/hooks/use-timer";
import { formatCurrency, formatDate, formatDateShort, formatRelativeTime } from "@/lib/utils";
import { useBreadcrumbs } from "@/components/layout/breadcrumb-context";

const STATUS_LABELS: Record<string, string> = {
  nieuw: "Nieuw",
  "14_dagenbrief": "14-dagenbrief",
  sommatie: "Sommatie",
  dagvaarding: "Dagvaarding",
  vonnis: "Vonnis",
  executie: "Executie",
  betaald: "Betaald",
  afgesloten: "Afgesloten",
};

const STATUS_BADGE: Record<string, string> = {
  nieuw: "bg-blue-50 text-blue-700 ring-blue-600/20",
  "14_dagenbrief": "bg-sky-50 text-sky-700 ring-sky-600/20",
  sommatie: "bg-amber-50 text-amber-700 ring-amber-600/20",
  dagvaarding: "bg-red-50 text-red-700 ring-red-600/20",
  vonnis: "bg-purple-50 text-purple-700 ring-purple-600/20",
  executie: "bg-red-50 text-red-800 ring-red-700/20",
  betaald: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  afgesloten: "bg-slate-50 text-slate-600 ring-slate-500/20",
};

const PIPELINE_STEPS = [
  "nieuw",
  "14_dagenbrief",
  "sommatie",
  "dagvaarding",
  "vonnis",
  "executie",
  "betaald",
];

const NEXT_STATUSES: Record<string, string[]> = {
  nieuw: ["14_dagenbrief", "afgesloten"],
  "14_dagenbrief": ["sommatie", "betaald", "afgesloten"],
  sommatie: ["dagvaarding", "betaald", "afgesloten"],
  dagvaarding: ["vonnis", "betaald", "afgesloten"],
  vonnis: ["executie", "betaald", "afgesloten"],
  executie: ["betaald", "afgesloten"],
  betaald: [],
  afgesloten: [],
};

const TYPE_LABELS: Record<string, string> = {
  incasso: "Incasso",
  insolventie: "Insolventie",
  advies: "Advies",
  overig: "Overig",
};

const INTEREST_LABELS: Record<string, string> = {
  statutory: "Wettelijke rente (art. 6:119 BW)",
  commercial: "Handelsrente (art. 6:119a BW)",
  government: "Overheidsrente (art. 6:119b BW)",
  contractual: "Contractuele rente",
};

const ACTIVITY_ICONS: Record<string, typeof Briefcase> = {
  status_change: ArrowUpDown,
  note: MessageSquare,
  phone_call: Phone,
  email: Mail,
  document: FileText,
  payment: CreditCard,
};

const ACTIVITY_COLORS: Record<string, string> = {
  status_change: "bg-blue-50 text-blue-600",
  note: "bg-amber-50 text-amber-600",
  phone_call: "bg-emerald-50 text-emerald-600",
  email: "bg-violet-50 text-violet-600",
  document: "bg-slate-100 text-slate-600",
  payment: "bg-green-50 text-green-600",
};

function VerjaringBadge({
  dateOpened,
  status,
}: {
  dateOpened: string;
  status: string;
}) {
  // Art. 3:307 BW — verjaringstermijn is 5 jaar
  const VERJARING_YEARS = 5;
  const terminalStatuses = ["betaald", "afgesloten"];
  if (terminalStatuses.includes(status)) return null;

  const opened = new Date(dateOpened);
  const verjaringDate = new Date(opened);
  verjaringDate.setFullYear(verjaringDate.getFullYear() + VERJARING_YEARS);

  const now = new Date();
  const daysLeft = Math.ceil(
    (verjaringDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
  );

  if (daysLeft <= 0) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/20">
        <AlertTriangle className="h-3 w-3" />
        Verjaard
      </span>
    );
  }

  if (daysLeft <= 30) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/20">
        <AlertTriangle className="h-3 w-3" />
        Verjaring: {daysLeft}d
      </span>
    );
  }

  if (daysLeft <= 90) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-600/20">
        <Clock className="h-3 w-3" />
        Verjaring: {daysLeft}d
      </span>
    );
  }

  return null;
}

export default function ZaakDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { data: zaak, isLoading } = useCase(id);
  const updateStatus = useUpdateCaseStatus();
  const deleteCase = useDeleteCase();
  const { data: workflowStatuses } = useWorkflowStatuses();
  const { data: workflowTransitions } = useWorkflowTransitions();

  // Set breadcrumb label to case number
  useBreadcrumbs(zaak ? [{ segment: id, label: zaak.case_number }] : []);
  const { hasModule } = useModules();
  const { startTimer, stopTimer, discardTimer, timer } = useTimer();
  const [autoTimerEnabled] = useAutoTimerPreference();
  const [activeTab, setActiveTab] = useState("overzicht");
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
        // Save the previous timer (>= 1 min)
        stopTimer().then(() => {
          const m = Math.max(1, Math.round(prevSeconds / 60));
          const h = Math.floor(m / 60);
          const min = m % 60;
          toast.info(
            `${h}:${String(min).padStart(2, "0")} opgeslagen voor ${prevName}`
          );
        });
      } else {
        // Discard short timers (< 1 min)
        discardTimer();
      }
    }

    // Start timer for current case
    const label = `${zaak.case_number}${zaak.client ? ` — ${zaak.client.name}` : ""}`;
    // Small delay to let stopTimer complete if needed
    const timeout = timer.running && timer.caseId !== zaak.id ? 300 : 0;
    const t = setTimeout(() => {
      startTimer(zaak.id, label);
      toast.info(`Timer gestart voor ${zaak.case_number}`, { duration: 2000 });
    }, timeout);
    autoStartedRef.current = zaak.id;

    return () => clearTimeout(t);
  }, [zaak?.id, autoTimerEnabled]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleStatusChange = async (newStatus: string) => {
    const note = prompt("Notitie bij statuswijziging (optioneel):");
    try {
      await updateStatus.mutateAsync({
        id,
        new_status: newStatus,
        note: note || undefined,
      });
      toast.success(`Status gewijzigd naar ${STATUS_LABELS[newStatus]}`);

      // T2: Toon suggestie-banner als er aanbevolen templates zijn
      const nextTemplates = getTemplatesForStatus(newStatus, zaak?.debtor_type);
      if (nextTemplates.recommended.length > 0) {
        setStatusSuggestion({ status: newStatus, templates: nextTemplates.recommended });
        // Auto-dismiss na 30 seconden
        setTimeout(() => setStatusSuggestion(null), 30000);
      }
    } catch (err: any) {
      toast.error(err.message || "Statuswijziging mislukt");
    }
  };

  const handleDelete = async () => {
    if (!confirm("Weet je zeker dat je dit dossier wilt verwijderen?")) return;
    try {
      await deleteCase.mutateAsync(id);
      toast.success("Dossier verwijderd");
      router.push("/zaken");
    } catch {
      toast.error("Kon het dossier niet verwijderen");
    }
  };

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

  const isIncasso = hasModule("incasso") && zaak.case_type === "incasso";

  const tabs = [
    { id: "overzicht", label: "Overzicht", icon: Briefcase },
    { id: "taken", label: "Taken", icon: CheckCircle2 },
    ...(isIncasso
      ? [
          { id: "vorderingen", label: "Vorderingen", icon: Euro },
          { id: "betalingen", label: "Betalingen", icon: Receipt },
          { id: "financieel", label: "Financieel", icon: Wallet },
          { id: "derdengelden", label: "Derdengelden", icon: FileText },
        ]
      : []),
    { id: "facturen", label: "Facturen", icon: CreditCard },
    { id: "documenten", label: "Documenten", icon: File },
    { id: "correspondentie", label: "Correspondentie", icon: Mail },
    { id: "activiteiten", label: "Activiteiten", icon: Clock },
    { id: "partijen", label: "Partijen", icon: Users },
  ];

  // Determine current phase from workflow data or fallback
  const currentPhase = workflowStatuses
    ? getPhaseForStatus(workflowStatuses, zaak.status)
    : null;
  const currentPhaseIndex = currentPhase
    ? PHASE_ORDER.indexOf(currentPhase)
    : -1;
  const isTerminal =
    currentPhase === "afgerond" ||
    zaak.status === "betaald" ||
    zaak.status === "afgesloten";

  // Available transitions from workflow data, with fallback to hardcoded
  const availableNextStatuses = workflowStatuses && workflowTransitions
    ? getAvailableTransitions(
        workflowTransitions,
        zaak.status,
        zaak.debtor_type ?? "both",
        workflowStatuses
      )
    : null;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <Link
            href="/zaken"
            className="mt-1 rounded-lg p-2 hover:bg-muted transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-muted-foreground" />
          </Link>
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold text-foreground">
                {zaak.case_number}
              </h1>
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
                  STATUS_BADGE[zaak.status] ??
                  "bg-slate-50 text-slate-600 ring-slate-500/20"
                }`}
              >
                {STATUS_LABELS[zaak.status] ?? zaak.status}
              </span>
              {zaak.debtor_type && (
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
                    zaak.debtor_type === "b2b"
                      ? "bg-indigo-50 text-indigo-700 ring-indigo-600/20"
                      : "bg-pink-50 text-pink-700 ring-pink-600/20"
                  }`}
                >
                  {zaak.debtor_type === "b2b" ? "B2B" : "B2C"}
                </span>
              )}
              {isIncasso && <VerjaringBadge dateOpened={zaak.date_opened} status={zaak.status} />}
            </div>
            <p className="text-sm text-muted-foreground mt-0.5">
              {TYPE_LABELS[zaak.case_type]} · Geopend{" "}
              {formatDate(zaak.date_opened)}
              {zaak.assigned_to && ` · ${zaak.assigned_to.full_name}`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleDelete}
            className="rounded-lg border border-destructive/20 p-2 text-destructive hover:bg-destructive/10 transition-colors"
            title="Verwijderen"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Phase Pipeline Stepper — only for incasso cases */}
      {isIncasso && (
        <div className="rounded-xl border border-border bg-card p-4 sm:p-5">
          <div className="flex items-center gap-1 overflow-x-auto pb-1">
            {PHASE_ORDER.map((phase, index) => {
              const isActive = phase === currentPhase;
              const isPast = currentPhaseIndex >= 0 && index < currentPhaseIndex;
              const PHASE_ACTIVE_CLASSES: Record<string, string> = {
                minnelijk: "bg-blue-500 text-white ring-4 ring-blue-500/20",
                regeling: "bg-amber-500 text-white ring-4 ring-amber-500/20",
                gerechtelijk: "bg-purple-500 text-white ring-4 ring-purple-500/20",
                executie: "bg-red-500 text-white ring-4 ring-red-500/20",
                afgerond: "bg-emerald-500 text-white ring-4 ring-emerald-500/20",
              };

              return (
                <div key={phase} className="flex items-center flex-1 min-w-0">
                  <div className="flex flex-col items-center gap-1.5 flex-1 min-w-0">
                    <div
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-all ${
                        isActive
                          ? PHASE_ACTIVE_CLASSES[phase] ?? "bg-slate-500 text-white"
                          : isPast
                            ? "bg-emerald-500 text-white"
                            : "border-2 border-border text-muted-foreground"
                      }`}
                    >
                      {isPast ? (
                        <CheckCircle2 className="h-4 w-4" />
                      ) : (
                        index + 1
                      )}
                    </div>
                    <span
                      className={`text-[10px] sm:text-xs font-medium text-center leading-tight ${
                        isActive
                          ? "text-foreground font-semibold"
                          : isPast
                            ? "text-emerald-600"
                            : "text-muted-foreground"
                      }`}
                    >
                      {PHASE_LABELS[phase]}
                    </span>
                  </div>
                  {index < PHASE_ORDER.length - 1 && (
                    <div
                      className={`hidden sm:block h-0.5 w-4 shrink-0 mx-0.5 ${
                        isPast ? "bg-emerald-400" : "bg-border"
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>

          {/* Status transition buttons */}
          {!isTerminal && (
            <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-border">
              <span className="text-xs text-muted-foreground self-center mr-1">
                Volgende stap:
              </span>
              {availableNextStatuses && availableNextStatuses.length > 0 ? (
                availableNextStatuses.map((nextStatus) => {
                  const isTerminalStatus = nextStatus.is_terminal;
                  return (
                    <button
                      key={nextStatus.slug}
                      onClick={() => handleStatusChange(nextStatus.slug)}
                      disabled={updateStatus.isPending}
                      className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                        isTerminalStatus
                          ? "border border-border hover:bg-muted text-muted-foreground"
                          : "bg-primary/10 text-primary hover:bg-primary/20"
                      }`}
                    >
                      <ArrowRight className="h-3 w-3" />
                      {nextStatus.label}
                    </button>
                  );
                })
              ) : (
                /* Fallback to hardcoded transitions when workflow API not available */
                NEXT_STATUSES[zaak.status]?.map((nextStatus) => (
                  <button
                    key={nextStatus}
                    onClick={() => handleStatusChange(nextStatus)}
                    disabled={updateStatus.isPending}
                    className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                      nextStatus === "betaald" || nextStatus === "afgesloten"
                        ? "border border-border hover:bg-muted text-muted-foreground"
                        : "bg-primary/10 text-primary hover:bg-primary/20"
                    }`}
                  >
                    <ArrowRight className="h-3 w-3" />
                    {STATUS_LABELS[nextStatus]}
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* T2: Workflow-suggestie banner */}
      {statusSuggestion && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/30 p-4 flex items-center justify-between gap-4 animate-fade-in">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-900/50">
              <FileText className="h-4 w-4 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">
                Status gewijzigd naar {STATUS_LABELS[statusSuggestion.status] ?? statusSuggestion.status}
              </p>
              <p className="text-xs text-muted-foreground">
                {statusSuggestion.templates.length === 1
                  ? `${getTemplateLabel(statusSuggestion.templates[0])} klaarzetten?`
                  : `${statusSuggestion.templates.map(getTemplateLabel).join(" of ")} klaarzetten?`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => {
                setActiveTab("documenten");
                setStatusSuggestion(null);
              }}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <FileText className="h-3 w-3" />
              Ga naar documenten
            </button>
            <button
              onClick={() => setStatusSuggestion(null)}
              className="rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              title="Later"
            >
              <XCircle className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className={`grid gap-4 sm:grid-cols-2 ${isIncasso ? "lg:grid-cols-4" : "lg:grid-cols-2"}`}>
        {isIncasso && (
          <>
            <div className="rounded-xl border border-border bg-card p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50">
                  <Euro className="h-4 w-4 text-blue-600" />
                </div>
                <span className="text-xs text-muted-foreground">Hoofdsom</span>
              </div>
              <p className="text-xl font-bold text-foreground tabular-nums">
                {formatCurrency(zaak.total_principal)}
              </p>
            </div>
            <div className="rounded-xl border border-border bg-card p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50">
                  <CreditCard className="h-4 w-4 text-emerald-600" />
                </div>
                <span className="text-xs text-muted-foreground">Betaald</span>
              </div>
              <p className="text-xl font-bold text-emerald-600 tabular-nums">
                {formatCurrency(zaak.total_paid)}
              </p>
            </div>
            <div className="rounded-xl border border-border bg-card p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50">
                  <CalendarDays className="h-4 w-4 text-amber-600" />
                </div>
                <span className="text-xs text-muted-foreground">Rente</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                {INTEREST_LABELS[zaak.interest_type] ?? zaak.interest_type}
              </p>
            </div>
          </>
        )}
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-violet-50">
              <Users className="h-4 w-4 text-violet-600" />
            </div>
            <span className="text-xs text-muted-foreground">Partijen</span>
          </div>
          <div className="space-y-1">
            {zaak.client && (
              <Link
                href={`/relaties/${zaak.client.id}`}
                className="text-sm font-medium text-foreground hover:text-primary transition-colors block truncate"
              >
                {zaak.client.name}
              </Link>
            )}
            {zaak.opposing_party && (
              <p className="text-xs text-muted-foreground truncate">
                vs. {zaak.opposing_party.name}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions Bar */}
      <div className="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          onClick={() => {
            const label = `${zaak.case_number}${zaak.client ? ` — ${zaak.client.name}` : ""}`;
            startTimer(zaak.id, label);
          }}
          disabled={timer.running && timer.caseId === zaak.id}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Clock className="h-3.5 w-3.5 text-emerald-500" />
          {timer.running && timer.caseId === zaak.id ? "Timer loopt..." : "Uren loggen"}
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("activiteiten")}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors"
        >
          <MessageSquare className="h-3.5 w-3.5 text-amber-500" />
          Notitie
        </button>
        <button
          type="button"
          onClick={() => {
            const now = new Date();
            const stamp = now.toLocaleString("nl-NL", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
            setPhoneNoteText(`📞 Telefoonnotitie ${stamp}\n\nGesprek met: \nOnderwerp: \n\n`);
            setActiveTab("overzicht");
            // Focus the textarea after state update
            setTimeout(() => {
              const ta = document.querySelector<HTMLTextAreaElement>('textarea[placeholder*="notitie"]');
              if (ta) { ta.focus(); ta.setSelectionRange(ta.value.indexOf("Gesprek met: ") + 13, ta.value.indexOf("Gesprek met: ") + 13); }
            }, 100);
          }}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors"
        >
          <Phone className="h-3.5 w-3.5 text-emerald-500" />
          Telefoonnotitie
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("documenten")}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors"
        >
          <FileText className="h-3.5 w-3.5 text-blue-500" />
          Document
        </button>
        <Link
          href={`/facturen/nieuw?case_id=${zaak.id}`}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors"
        >
          <Receipt className="h-3.5 w-3.5 text-violet-500" />
          Factuur
        </Link>
        {isIncasso && (
          <button
            type="button"
            onClick={() => setActiveTab("financieel")}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors"
          >
            <Euro className="h-3.5 w-3.5 text-orange-500" />
            Renteoverzicht
          </button>
        )}
      </div>

      {/* Tabs */}
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

      {/* Tab content */}
      {activeTab === "overzicht" && <OverzichtTab zaak={zaak} initialNoteText={phoneNoteText} onNoteTextConsumed={() => setPhoneNoteText("")} />}
      {activeTab === "taken" && <TakenTab caseId={id} />}
      {isIncasso && activeTab === "vorderingen" && <VorderingenTab caseId={id} />}
      {isIncasso && activeTab === "betalingen" && <BetalingenTab caseId={id} />}
      {isIncasso && activeTab === "financieel" && <FinancieelTab caseId={id} />}
      {isIncasso && activeTab === "derdengelden" && <DerdengeldenTab caseId={id} />}
      {activeTab === "facturen" && <FacturenTab caseId={id} clientId={zaak?.client?.id} />}
      {activeTab === "documenten" && <DocumentenTab caseId={id} caseNumber={zaak?.case_number} caseStatus={zaak?.status} debtorType={zaak?.debtor_type} opposingPartyName={zaak?.opposing_party?.name} />}
      {activeTab === "correspondentie" && <CorrespondentieTab caseId={id} />}
      {activeTab === "activiteiten" && <ActiviteitenTab zaak={zaak} />}
      {activeTab === "partijen" && <PartijenTab zaak={zaak} />}
    </div>
  );
}

// ── Overzicht Tab ─────────────────────────────────────────────────────────────

function OverzichtTab({ zaak, initialNoteText, onNoteTextConsumed }: { zaak: any; initialNoteText?: string; onNoteTextConsumed?: () => void }) {
  const [noteText, setNoteText] = useState("");
  const addActivity = useAddCaseActivity();

  // Apply phone note text from parent
  useEffect(() => {
    if (initialNoteText) {
      setNoteText(initialNoteText);
      onNoteTextConsumed?.();
    }
  }, [initialNoteText]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAddNote = async () => {
    const text = noteText.trim();
    if (!text) return;
    try {
      await addActivity.mutateAsync({
        caseId: zaak.id,
        data: {
          activity_type: "note",
          title: "Notitie toegevoegd",
          description: text,
        },
      });
      setNoteText("");
      toast.success("Notitie toegevoegd");
    } catch {
      toast.error("Kon notitie niet toevoegen");
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-5">
      {/* Left: Case details */}
      <div className="lg:col-span-3 space-y-6">
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-4 text-sm font-semibold text-card-foreground uppercase tracking-wider">
            Dossiergegevens
          </h2>
          <dl className="grid gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-xs text-muted-foreground mb-1">
                Beschrijving
              </dt>
              <dd className="text-sm text-foreground">
                {zaak.description || "-"}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground mb-1">
                Referentie
              </dt>
              <dd className="text-sm text-foreground font-mono">
                {zaak.reference || "-"}
              </dd>
            </div>
            {zaak.court_case_number && (
              <div>
                <dt className="text-xs text-muted-foreground mb-1">
                  Zaaknummer rechtbank
                </dt>
                <dd className="text-sm text-foreground font-mono">
                  {zaak.court_case_number}
                </dd>
              </div>
            )}
            {zaak.contractual_rate && (
              <div>
                <dt className="text-xs text-muted-foreground mb-1">
                  Contractueel rentepercentage
                </dt>
                <dd className="text-sm text-foreground">
                  {zaak.contractual_rate}%
                  {zaak.contractual_compound
                    ? " (samengesteld)"
                    : " (enkelvoudig)"}
                </dd>
              </div>
            )}
            {zaak.assigned_to && (
              <div>
                <dt className="text-xs text-muted-foreground mb-1">
                  Toegewezen aan
                </dt>
                <dd className="text-sm text-foreground">
                  {zaak.assigned_to.full_name}
                </dd>
              </div>
            )}
            {zaak.date_closed && (
              <div>
                <dt className="text-xs text-muted-foreground mb-1">
                  Datum gesloten
                </dt>
                <dd className="text-sm text-foreground">
                  {formatDate(zaak.date_closed)}
                </dd>
              </div>
            )}
          </dl>
        </div>

        {/* Partijen inline */}
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-4 text-sm font-semibold text-card-foreground uppercase tracking-wider">
            Partijen
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {zaak.client && (
              <Link
                href={`/relaties/${zaak.client.id}`}
                className="flex items-center gap-3 rounded-lg border border-border p-3 hover:border-primary/30 hover:bg-muted/50 transition-all"
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10">
                  <Building2 className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {zaak.client.name}
                  </p>
                  <p className="text-xs text-primary">Client</p>
                </div>
              </Link>
            )}
            {zaak.opposing_party && (
              <Link
                href={`/relaties/${zaak.opposing_party.id}`}
                className="flex items-center gap-3 rounded-lg border border-border p-3 hover:border-amber-300/50 hover:bg-muted/50 transition-all"
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-amber-50">
                  <User className="h-4 w-4 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {zaak.opposing_party.name}
                  </p>
                  <p className="text-xs text-amber-600">Wederpartij</p>
                </div>
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Right: Note + Recent Activity */}
      <div className="lg:col-span-2 space-y-6">
        {/* Quick note input — always visible */}
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center gap-2 mb-3">
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-card-foreground">
              Notitie
            </h2>
          </div>
          <textarea
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="Schrijf een notitie..."
            rows={3}
            className="w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors resize-none"
          />
          <div className="flex items-center justify-between mt-2">
            <p className="text-[10px] text-muted-foreground">
              **vet**, *cursief*, - opsomming
            </p>
            <button
              type="button"
              onClick={handleAddNote}
              disabled={!noteText.trim() || addActivity.isPending}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {addActivity.isPending ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Send className="h-3 w-3" />
              )}
              Opslaan
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card">
          <div className="flex items-center gap-2 px-5 py-4 border-b border-border">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-card-foreground">
              Recente activiteit
            </h2>
          </div>
          {zaak.recent_activities && zaak.recent_activities.length > 0 ? (
            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-[2.125rem] top-0 bottom-0 w-px bg-border" />
              {zaak.recent_activities.slice(0, 6).map((activity: any, idx: number) => {
                const Icon =
                  ACTIVITY_ICONS[activity.activity_type] ?? FileText;
                const colorClass =
                  ACTIVITY_COLORS[activity.activity_type] ?? "bg-muted text-muted-foreground";
                return (
                  <div
                    key={activity.id}
                    className="relative flex items-start gap-3 px-5 py-3.5"
                  >
                    <div
                      className={`relative z-10 mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${colorClass}`}
                    >
                      <Icon className="h-3.5 w-3.5" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-foreground">
                        {activity.title}
                      </p>
                      {activity.description && (
                        <p className="text-xs text-muted-foreground truncate">
                          {activity.description}
                        </p>
                      )}
                      <p className="text-xs text-muted-foreground/70 mt-0.5">
                        {formatRelativeTime(activity.created_at)}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="px-5 py-8 text-center">
              <Clock className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">
                Nog geen activiteiten
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Vorderingen Tab ───────────────────────────────────────────────────────────

function VorderingenTab({ caseId }: { caseId: string }) {
  const { data: claims, isLoading } = useClaims(caseId);
  const { data: interest } = useCaseInterest(caseId);
  const createClaim = useCreateClaim();
  const deleteClaim = useDeleteClaim();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    description: "",
    principal_amount: "",
    default_date: "",
    invoice_number: "",
    invoice_date: "",
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createClaim.mutateAsync({
        caseId,
        data: {
          description: form.description,
          principal_amount: parseFloat(form.principal_amount),
          default_date: form.default_date,
          ...(form.invoice_number && { invoice_number: form.invoice_number }),
          ...(form.invoice_date && { invoice_date: form.invoice_date }),
        },
      });
      toast.success("Vordering toegevoegd");
      setShowForm(false);
      setForm({
        description: "",
        principal_amount: "",
        default_date: "",
        invoice_number: "",
        invoice_date: "",
      });
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleDelete = async (claimId: string) => {
    if (!confirm("Vordering verwijderen?")) return;
    try {
      await deleteClaim.mutateAsync({ caseId, claimId });
      toast.success("Vordering verwijderd");
    } catch {
      toast.error("Kon niet verwijderen");
    }
  };

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">
          Vorderingen
        </h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          Vordering toevoegen
        </button>
      </div>

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
                onChange={(e) =>
                  setForm((f) => ({ ...f, description: e.target.value }))
                }
                className={inputClass}
                placeholder="Factuur nr. 2025-001"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Hoofdsom *
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={form.principal_amount}
                onChange={(e) =>
                  setForm((f) => ({ ...f, principal_amount: e.target.value }))
                }
                className={inputClass}
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Verzuimdatum *
              </label>
              <input
                type="date"
                required
                value={form.default_date}
                onChange={(e) =>
                  setForm((f) => ({ ...f, default_date: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Factuurnummer
              </label>
              <input
                type="text"
                value={form.invoice_number}
                onChange={(e) =>
                  setForm((f) => ({ ...f, invoice_number: e.target.value }))
                }
                className={inputClass}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createClaim.isPending}
              className="rounded-lg bg-primary px-4 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {createClaim.isPending ? "Opslaan..." : "Opslaan"}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-medium hover:bg-muted"
            >
              Annuleren
            </button>
          </div>
        </form>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg skeleton" />
          ))}
        </div>
      ) : claims && claims.length > 0 ? (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Beschrijving
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Hoofdsom
                </th>
                <th className="hidden sm:table-cell px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Verzuimdatum
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Rente
                </th>
                <th className="px-4 py-3 w-10" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {claims.map((claim) => {
                const claimInterest = interest?.claims.find(
                  (c) => c.claim_id === claim.id
                );
                return (
                  <tr
                    key={claim.id}
                    className="hover:bg-muted/30 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <p className="text-sm font-medium text-foreground">
                        {claim.description}
                      </p>
                      {claim.invoice_number && (
                        <p className="text-xs text-muted-foreground">
                          Factuur: {claim.invoice_number}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-sm font-semibold text-foreground tabular-nums">
                      {formatCurrency(claim.principal_amount)}
                    </td>
                    <td className="hidden sm:table-cell px-4 py-3 text-sm text-muted-foreground">
                      {formatDateShort(claim.default_date)}
                    </td>
                    <td className="hidden md:table-cell px-4 py-3 text-right text-sm text-accent font-medium tabular-nums">
                      {claimInterest
                        ? formatCurrency(claimInterest.total_interest)
                        : "-"}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleDelete(claim.id)}
                        className="rounded p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
            {interest && (
              <tfoot>
                <tr className="border-t-2 border-border bg-muted/20">
                  <td className="px-4 py-3 text-sm font-bold text-foreground">
                    Totaal
                  </td>
                  <td className="px-4 py-3 text-right text-sm font-bold text-foreground tabular-nums">
                    {formatCurrency(interest.total_principal)}
                  </td>
                  <td className="hidden sm:table-cell px-4 py-3" />
                  <td className="hidden md:table-cell px-4 py-3 text-right text-sm font-bold text-accent tabular-nums">
                    {formatCurrency(interest.total_interest)}
                  </td>
                  <td className="px-4 py-3" />
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <Euro className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">
            Nog geen vorderingen
          </p>
          <button
            onClick={() => setShowForm(true)}
            className="mt-2 text-sm text-primary hover:underline"
          >
            Voeg de eerste vordering toe
          </button>
        </div>
      )}
    </div>
  );
}

// ── Betalingen Tab ────────────────────────────────────────────────────────────

function BetalingenTab({ caseId }: { caseId: string }) {
  const { data: payments, isLoading } = usePayments(caseId);
  const createPayment = useCreatePayment();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    amount: "",
    payment_date: new Date().toISOString().split("T")[0],
    description: "",
    payment_method: "",
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createPayment.mutateAsync({
        caseId,
        data: {
          amount: parseFloat(form.amount),
          payment_date: form.payment_date,
          ...(form.description && { description: form.description }),
          ...(form.payment_method && { payment_method: form.payment_method }),
        },
      });
      toast.success("Betaling geregistreerd");
      setShowForm(false);
      setForm({
        amount: "",
        payment_date: new Date().toISOString().split("T")[0],
        description: "",
        payment_method: "",
      });
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">Betalingen</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          Betaling registreren
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-3"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-foreground">
                Bedrag *
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={form.amount}
                onChange={(e) =>
                  setForm((f) => ({ ...f, amount: e.target.value }))
                }
                className={inputClass}
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Datum *
              </label>
              <input
                type="date"
                required
                value={form.payment_date}
                onChange={(e) =>
                  setForm((f) => ({ ...f, payment_date: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Omschrijving
              </label>
              <input
                type="text"
                value={form.description}
                onChange={(e) =>
                  setForm((f) => ({ ...f, description: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Betaalwijze
              </label>
              <select
                value={form.payment_method}
                onChange={(e) =>
                  setForm((f) => ({ ...f, payment_method: e.target.value }))
                }
                className={inputClass}
              >
                <option value="">-</option>
                <option value="bank">Bankoverschrijving</option>
                <option value="cash">Contant</option>
                <option value="derdengelden">Via derdengelden</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createPayment.isPending}
              className="rounded-lg bg-primary px-4 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {createPayment.isPending ? "Opslaan..." : "Registreren"}
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-medium hover:bg-muted"
            >
              Annuleren
            </button>
          </div>
        </form>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg skeleton" />
          ))}
        </div>
      ) : payments && payments.length > 0 ? (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Datum
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Bedrag
                </th>
                <th className="hidden sm:table-cell px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Omschrijving
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Kosten
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Rente
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Hoofdsom
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {payments.map((payment) => (
                <tr
                  key={payment.id}
                  className="hover:bg-muted/30 transition-colors"
                >
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {formatDateShort(payment.payment_date)}
                  </td>
                  <td className="px-4 py-3 text-right text-sm font-semibold text-emerald-600 tabular-nums">
                    {formatCurrency(payment.amount)}
                  </td>
                  <td className="hidden sm:table-cell px-4 py-3 text-sm text-muted-foreground">
                    {payment.description || "-"}
                  </td>
                  <td className="hidden md:table-cell px-4 py-3 text-right text-xs text-muted-foreground tabular-nums">
                    {formatCurrency(payment.allocated_to_costs)}
                  </td>
                  <td className="hidden md:table-cell px-4 py-3 text-right text-xs text-muted-foreground tabular-nums">
                    {formatCurrency(payment.allocated_to_interest)}
                  </td>
                  <td className="hidden md:table-cell px-4 py-3 text-right text-xs text-muted-foreground tabular-nums">
                    {formatCurrency(payment.allocated_to_principal)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="border-t border-border bg-muted/20 px-4 py-2.5 text-xs text-muted-foreground">
            Art. 6:44 BW — Betalingen worden automatisch verdeeld: eerst kosten,
            dan rente, dan hoofdsom
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <Receipt className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">
            Nog geen betalingen
          </p>
        </div>
      )}
    </div>
  );
}

// ── Financieel Tab ────────────────────────────────────────────────────────────

function FinancieelTab({ caseId }: { caseId: string }) {
  const { data: summary, isLoading } = useFinancialSummary(caseId);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-28 rounded-xl skeleton" />
          ))}
        </div>
        <div className="h-6 rounded-lg skeleton" />
        <div className="h-48 rounded-xl skeleton" />
      </div>
    );
  }

  if (!summary) return null;

  const paidPercent = summary.grand_total > 0
    ? Math.min(100, Math.round((summary.total_paid / summary.grand_total) * 100))
    : 0;

  const rows = [
    { label: "Hoofdsom", total: summary.total_principal, paid: summary.total_paid_principal, open: summary.remaining_principal },
    { label: "Rente", total: summary.total_interest, paid: summary.total_paid_interest, open: summary.remaining_interest },
    {
      label: summary.bik_btw > 0 ? "BIK incl. BTW" : "BIK (art. 6:96 BW)",
      total: summary.total_bik,
      paid: summary.total_paid_costs,
      open: summary.remaining_costs,
    },
  ];

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-muted-foreground mb-1">
            <Receipt className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Totale vordering</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-foreground">
            {formatCurrency(summary.grand_total)}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Hoofdsom + rente + kosten
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-emerald-600 mb-1">
            <CheckCircle2 className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Betaald</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-emerald-600">
            {formatCurrency(summary.total_paid)}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {paidPercent}% van totaal
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-amber-600 mb-1">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Openstaand</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-amber-600">
            {formatCurrency(summary.total_outstanding)}
          </p>
          {summary.derdengelden_balance > 0 && (
            <p className="text-xs text-muted-foreground mt-1">
              Derdengelden: {formatCurrency(summary.derdengelden_balance)}
            </p>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-muted-foreground">Betalingsvoortgang</span>
          <span className="text-xs font-semibold text-foreground tabular-nums">{paidPercent}%</span>
        </div>
        <div className="h-2.5 rounded-full bg-muted overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              paidPercent >= 100 ? "bg-emerald-500" : paidPercent >= 50 ? "bg-emerald-500" : "bg-amber-500"
            }`}
            style={{ width: `${paidPercent}%` }}
          />
        </div>
        <div className="flex justify-between mt-1.5">
          <span className="text-[10px] text-emerald-600 tabular-nums">{formatCurrency(summary.total_paid)} betaald</span>
          <span className="text-[10px] text-muted-foreground tabular-nums">{formatCurrency(summary.grand_total)} totaal</span>
        </div>
      </div>

      {/* Breakdown table */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-2 px-5 py-3.5 border-b border-border bg-muted/30">
          <Euro className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Specificatie</h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Post</th>
              <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Totaal</th>
              <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Betaald</th>
              <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Openstaand</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((row) => {
              const rowPaid = row.total > 0 ? Math.round((row.paid / row.total) * 100) : 0;
              return (
                <tr key={row.label} className="hover:bg-muted/30 transition-colors">
                  <td className="px-5 py-3.5">
                    <p className="text-sm text-foreground">{row.label}</p>
                    <div className="mt-1 h-1 w-20 rounded-full bg-muted overflow-hidden">
                      <div className="h-full rounded-full bg-emerald-500" style={{ width: `${rowPaid}%` }} />
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-right text-sm font-medium tabular-nums">{formatCurrency(row.total)}</td>
                  <td className="px-5 py-3.5 text-right text-sm text-emerald-600 tabular-nums">{formatCurrency(row.paid)}</td>
                  <td className="px-5 py-3.5 text-right text-sm font-medium tabular-nums">
                    {row.open > 0 ? (
                      <span className="text-amber-600">{formatCurrency(row.open)}</span>
                    ) : (
                      <span className="text-emerald-600">{formatCurrency(0)}</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-border bg-muted/30">
              <td className="px-5 py-3.5 text-sm font-bold text-foreground">Totaal</td>
              <td className="px-5 py-3.5 text-right text-sm font-bold text-foreground tabular-nums">{formatCurrency(summary.grand_total)}</td>
              <td className="px-5 py-3.5 text-right text-sm font-bold text-emerald-600 tabular-nums">{formatCurrency(summary.total_paid)}</td>
              <td className="px-5 py-3.5 text-right text-sm font-bold text-amber-600 tabular-nums">{formatCurrency(summary.total_outstanding)}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <p className="text-xs text-muted-foreground">
        Berekening op {formatDate(summary.calculation_date)}. Rente wordt dagelijks bijgewerkt.
      </p>
    </div>
  );
}

// ── Derdengelden Tab ──────────────────────────────────────────────────────────

function DerdengeldenTab({ caseId }: { caseId: string }) {
  const { data: txData, isLoading } = useDerdengelden(caseId);
  const { data: balance } = useDerdengeldenBalance(caseId);
  const createTx = useCreateDerdengelden();
  const approveTx = useApproveTrustTransaction();
  const rejectTx = useRejectTrustTransaction();
  const [showForm, setShowForm] = useState<"deposit" | "disbursement" | null>(null);
  const [form, setForm] = useState({
    amount: "",
    description: "",
    payment_method: "",
    reference: "",
    beneficiary_name: "",
    beneficiary_iban: "",
  });

  const transactions = txData?.items || [];

  const resetForm = () => {
    setForm({ amount: "", description: "", payment_method: "", reference: "", beneficiary_name: "", beneficiary_iban: "" });
    setShowForm(null);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showForm) return;
    try {
      await createTx.mutateAsync({
        caseId,
        data: {
          transaction_type: showForm,
          amount: parseFloat(form.amount),
          description: form.description,
          ...(form.payment_method && { payment_method: form.payment_method }),
          ...(form.reference && { reference: form.reference }),
          ...(showForm === "disbursement" && form.beneficiary_name && { beneficiary_name: form.beneficiary_name }),
          ...(showForm === "disbursement" && form.beneficiary_iban && { beneficiary_iban: form.beneficiary_iban }),
        },
      });
      toast.success(showForm === "deposit" ? "Storting geregistreerd" : "Uitbetaling ingediend ter goedkeuring");
      resetForm();
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleApprove = async (txId: string) => {
    try {
      await approveTx.mutateAsync({ transactionId: txId, caseId });
      toast.success("Transactie goedgekeurd");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleReject = async (txId: string) => {
    try {
      await rejectTx.mutateAsync({ transactionId: txId, caseId });
      toast.success("Transactie afgewezen");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  const STATUS_BADGE: Record<string, { label: string; className: string }> = {
    approved: { label: "Goedgekeurd", className: "bg-emerald-50 text-emerald-700 ring-emerald-600/20" },
    pending_approval: { label: "Wacht op goedkeuring", className: "bg-amber-50 text-amber-700 ring-amber-600/20" },
    rejected: { label: "Afgewezen", className: "bg-red-50 text-red-700 ring-red-600/20" },
  };

  const pendingCount = transactions.filter((t) => t.status === "pending_approval").length;

  return (
    <div className="space-y-6">
      {/* Balance cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-muted-foreground mb-1">
            <Wallet className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Totaal saldo</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-foreground">
            {balance ? formatCurrency(balance.total_balance) : "€ 0,00"}
          </p>
          {balance && balance.total_deposits > 0 && (
            <p className="text-xs text-muted-foreground mt-1">
              {formatCurrency(balance.total_deposits)} ontvangen — {formatCurrency(balance.total_disbursements)} uitbetaald
            </p>
          )}
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-muted-foreground mb-1">
            <Clock className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wider">In afwachting</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-amber-600">
            {balance ? formatCurrency(balance.pending_disbursements) : "€ 0,00"}
          </p>
          {pendingCount > 0 && (
            <p className="text-xs text-amber-600 mt-1">
              {pendingCount} transactie{pendingCount > 1 ? "s" : ""} wacht{pendingCount === 1 ? "" : "en"} op goedkeuring
            </p>
          )}
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-muted-foreground mb-1">
            <CheckCircle2 className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Beschikbaar</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-emerald-600">
            {balance ? formatCurrency(balance.available) : "€ 0,00"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">Saldo minus openstaande uitbetalingen</p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setShowForm(showForm === "deposit" ? null : "deposit")}
          className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 transition-colors"
        >
          <ArrowDownLeft className="h-3.5 w-3.5" />
          Storting
        </button>
        <button
          onClick={() => setShowForm(showForm === "disbursement" ? null : "disbursement")}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <ArrowUpRight className="h-3.5 w-3.5" />
          Uitbetaling
        </button>
      </div>

      {/* Transaction form */}
      {showForm && (
        <form
          onSubmit={handleCreate}
          className={`rounded-xl border p-5 space-y-3 ${
            showForm === "deposit"
              ? "border-emerald-200 bg-emerald-50/50"
              : "border-primary/20 bg-primary/5"
          }`}
        >
          <h3 className="text-sm font-semibold text-foreground">
            {showForm === "deposit" ? "Storting registreren" : "Uitbetaling indienen"}
          </h3>
          {showForm === "disbursement" && (
            <div className="flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-200 p-3">
              <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
              <p className="text-xs text-amber-800">
                Uitbetalingen vereisen goedkeuring van twee directeuren (vier-ogenprincipe).
              </p>
            </div>
          )}
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-foreground">Bedrag *</label>
              <div className="relative mt-1.5">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">€</span>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  value={form.amount}
                  onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
                  className="w-full rounded-lg border border-input bg-background pl-7 pr-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                  placeholder="0,00"
                />
              </div>
              {showForm === "disbursement" && balance && parseFloat(form.amount || "0") > balance.available && (
                <p className="text-xs text-red-600 mt-1">Onvoldoende beschikbaar saldo</p>
              )}
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">Omschrijving *</label>
              <input
                type="text"
                required
                minLength={3}
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                className={inputClass}
                placeholder="Bijv. Storting advocaatkosten"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">Betalingsmethode</label>
              <select
                value={form.payment_method}
                onChange={(e) => setForm((f) => ({ ...f, payment_method: e.target.value }))}
                className={inputClass}
              >
                <option value="">— Kies —</option>
                <option value="bank">Bankoverschrijving</option>
                <option value="ideal">iDEAL</option>
                <option value="cash">Contant</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">Referentie</label>
              <input
                type="text"
                value={form.reference}
                onChange={(e) => setForm((f) => ({ ...f, reference: e.target.value }))}
                className={inputClass}
                placeholder="Bankreferentie / kenmerk"
              />
            </div>
            {showForm === "disbursement" && (
              <>
                <div>
                  <label className="block text-xs font-medium text-foreground">Begunstigde</label>
                  <input
                    type="text"
                    value={form.beneficiary_name}
                    onChange={(e) => setForm((f) => ({ ...f, beneficiary_name: e.target.value }))}
                    className={inputClass}
                    placeholder="Naam ontvanger"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-foreground">IBAN begunstigde</label>
                  <input
                    type="text"
                    value={form.beneficiary_iban}
                    onChange={(e) => setForm((f) => ({ ...f, beneficiary_iban: e.target.value }))}
                    className={inputClass}
                    placeholder="NL00 BANK 0000 0000 00"
                  />
                </div>
              </>
            )}
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createTx.isPending}
              className={`rounded-lg px-4 py-2 text-xs font-medium text-white disabled:opacity-50 transition-colors ${
                showForm === "deposit" ? "bg-emerald-600 hover:bg-emerald-700" : "bg-primary hover:bg-primary/90"
              }`}
            >
              {createTx.isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : showForm === "deposit" ? (
                "Storting registreren"
              ) : (
                "Uitbetaling indienen"
              )}
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="rounded-lg border border-border px-4 py-2 text-xs font-medium hover:bg-muted transition-colors"
            >
              Annuleren
            </button>
          </div>
        </form>
      )}

      {/* Transaction list */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg skeleton" />
          ))}
        </div>
      ) : transactions.length > 0 ? (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Datum
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Type
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Bedrag
                </th>
                <th className="hidden md:table-cell px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Omschrijving
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Status
                </th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Acties
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {transactions.map((tx) => {
                const badge = STATUS_BADGE[tx.status] || STATUS_BADGE.pending_approval;
                const isDeposit = tx.transaction_type === "deposit";
                return (
                  <tr key={tx.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 text-sm text-muted-foreground whitespace-nowrap">
                      {formatDateShort(tx.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
                          isDeposit
                            ? "bg-emerald-50 text-emerald-700 ring-emerald-600/20"
                            : "bg-blue-50 text-blue-700 ring-blue-600/20"
                        }`}
                      >
                        {isDeposit ? (
                          <ArrowDownLeft className="h-3 w-3" />
                        ) : (
                          <ArrowUpRight className="h-3 w-3" />
                        )}
                        {isDeposit ? "Storting" : "Uitbetaling"}
                      </span>
                    </td>
                    <td
                      className={`px-4 py-3 text-right text-sm font-semibold tabular-nums ${
                        isDeposit ? "text-emerald-600" : "text-foreground"
                      }`}
                    >
                      {isDeposit ? "+" : "-"}
                      {formatCurrency(tx.amount)}
                    </td>
                    <td className="hidden md:table-cell px-4 py-3">
                      <p className="text-sm text-foreground truncate max-w-[200px]" title={tx.description}>
                        {tx.description}
                      </p>
                      {tx.beneficiary_name && (
                        <p className="text-xs text-muted-foreground">→ {tx.beneficiary_name}</p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${badge.className}`}
                      >
                        {badge.label}
                      </span>
                      {tx.status === "pending_approval" && tx.approved_by_1 && !tx.approved_by_2 && (
                        <p className="text-[10px] text-muted-foreground mt-0.5">
                          1/2 goedgekeurd{tx.approver_1 ? ` door ${tx.approver_1.full_name}` : ""}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {tx.status === "pending_approval" && (
                        <div className="inline-flex items-center gap-1">
                          <button
                            onClick={() => handleApprove(tx.id)}
                            disabled={approveTx.isPending}
                            className="inline-flex items-center gap-1 rounded-md bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-200 transition-colors disabled:opacity-50"
                            title="Goedkeuren"
                          >
                            <ShieldCheck className="h-3 w-3" />
                            <span className="hidden lg:inline">Goedkeuren</span>
                          </button>
                          <button
                            onClick={() => handleReject(tx.id)}
                            disabled={rejectTx.isPending}
                            className="inline-flex items-center gap-1 rounded-md bg-red-100 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-200 transition-colors disabled:opacity-50"
                            title="Afwijzen"
                          >
                            <Ban className="h-3 w-3" />
                          </button>
                        </div>
                      )}
                      {tx.status === "approved" && (
                        <span className="text-xs text-emerald-600">
                          <CheckCircle2 className="h-3.5 w-3.5 inline" />
                        </span>
                      )}
                      {tx.status === "rejected" && (
                        <span className="text-xs text-red-500">
                          <XCircle className="h-3.5 w-3.5 inline" />
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <Wallet className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">
            Geen derdengelden transacties
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Registreer een storting of uitbetaling hierboven
          </p>
        </div>
      )}
    </div>
  );
}

// ── Simple markdown renderer for notes ───────────────────────────────────────

function renderSimpleMarkdown(text: string) {
  const lines = text.split("\n");
  return lines.map((line, i) => {
    // Bullet points
    const isBullet = /^[-*]\s+/.test(line);
    const content = isBullet ? line.replace(/^[-*]\s+/, "") : line;

    // Bold and italic inline formatting
    const parts = content.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
    const formatted = parts.map((part, j) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={j}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith("*") && part.endsWith("*")) {
        return <em key={j}>{part.slice(1, -1)}</em>;
      }
      return part;
    });

    if (isBullet) {
      return (
        <div key={i} className="flex items-start gap-1.5">
          <span className="mt-1.5 h-1 w-1 rounded-full bg-current shrink-0" />
          <span>{formatted}</span>
        </div>
      );
    }
    return <div key={i}>{formatted.length > 0 ? formatted : "\u00A0"}</div>;
  });
}

// ── Activiteiten Tab ──────────────────────────────────────────────────────────

const ACTIVITY_TYPE_LABELS: Record<string, string> = {
  status_change: "Statuswijziging",
  note: "Notitie",
  phone_call: "Telefoongesprek",
  email: "E-mail",
  document: "Document",
  payment: "Betaling",
};

function ActiviteitenTab({ zaak }: { zaak: any }) {
  const [page, setPage] = useState(1);
  const [noteText, setNoteText] = useState("");
  const [isAddingNote, setIsAddingNote] = useState(false);
  const { data, isLoading } = useCaseActivities(zaak.id, page);
  const addActivity = useAddCaseActivity();

  const handleAddNote = async () => {
    const text = noteText.trim();
    if (!text) return;

    try {
      await addActivity.mutateAsync({
        caseId: zaak.id,
        data: {
          activity_type: "note",
          title: "Notitie toegevoegd",
          description: text,
        },
      });
      setNoteText("");
      setIsAddingNote(false);
      setPage(1);
      toast.success("Notitie toegevoegd");
    } catch {
      toast.error("Kon notitie niet toevoegen");
    }
  };

  const activities = data?.items ?? [];
  const totalPages = data?.pages ?? 0;

  return (
    <div className="space-y-4">
      {/* Inline note input */}
      <div className="rounded-xl border border-border bg-card">
        {isAddingNote ? (
          <div className="p-4 space-y-3">
            <textarea
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              placeholder="Schrijf een notitie..."
              autoFocus
              rows={3}
              className="w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors resize-none"
            />
            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setIsAddingNote(false);
                  setNoteText("");
                }}
                className="rounded-lg border border-border px-3 py-1.5 text-xs hover:bg-muted transition-colors"
              >
                Annuleren
              </button>
              <button
                type="button"
                onClick={handleAddNote}
                disabled={!noteText.trim() || addActivity.isPending}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {addActivity.isPending ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Send className="h-3 w-3" />
                )}
                Opslaan
              </button>
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setIsAddingNote(true)}
            className="flex w-full items-center gap-3 px-5 py-3.5 text-left hover:bg-muted/50 transition-colors rounded-xl"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              <Plus className="h-4 w-4 text-primary" />
            </div>
            <span className="text-sm text-muted-foreground">
              Notitie toevoegen...
            </span>
          </button>
        )}
      </div>

      {/* Activity timeline */}
      <div className="rounded-xl border border-border bg-card">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-card-foreground">
              Alle activiteiten
            </h2>
            {data && (
              <span className="text-xs text-muted-foreground">
                ({data.total})
              </span>
            )}
          </div>
        </div>

        {isLoading ? (
          <div className="divide-y divide-border">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-start gap-3 px-5 py-4 animate-pulse">
                <div className="h-8 w-8 rounded-full bg-muted shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-2/3 rounded bg-muted" />
                  <div className="h-3 w-1/2 rounded bg-muted" />
                </div>
              </div>
            ))}
          </div>
        ) : activities.length > 0 ? (
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-[2.375rem] top-0 bottom-0 w-px bg-border" />

            {activities.map((activity: CaseActivity) => {
              const Icon =
                ACTIVITY_ICONS[activity.activity_type] ?? FileText;
              const colorClass =
                ACTIVITY_COLORS[activity.activity_type] ??
                "bg-muted text-muted-foreground";
              const typeLabel =
                ACTIVITY_TYPE_LABELS[activity.activity_type] ??
                activity.activity_type;

              return (
                <div
                  key={activity.id}
                  className="relative flex items-start gap-3 px-5 py-4 hover:bg-muted/30 transition-colors"
                >
                  <div
                    className={`relative z-10 mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${colorClass}`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-foreground">
                          {activity.title}
                        </p>
                        {activity.description && (
                          <div className="text-sm text-muted-foreground mt-0.5">
                            {activity.activity_type === "note"
                              ? renderSimpleMarkdown(activity.description)
                              : <p className="whitespace-pre-wrap">{activity.description}</p>
                            }
                          </div>
                        )}
                      </div>
                      <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
                        {typeLabel}
                      </span>
                    </div>
                    <div className="mt-1.5 flex items-center gap-2 text-xs text-muted-foreground/70">
                      <span>{formatRelativeTime(activity.created_at)}</span>
                      {activity.user && (
                        <>
                          <span>·</span>
                          <span>{activity.user.full_name}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="px-5 py-12 text-center">
            <Clock className="h-10 w-10 text-muted-foreground/20 mx-auto mb-3" />
            <p className="text-sm font-medium text-muted-foreground">
              Geen activiteiten
            </p>
            <p className="text-xs text-muted-foreground/70 mt-1">
              Voeg een notitie toe om de timeline te starten.
            </p>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-border px-5 py-3">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-30 transition-colors"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
              Vorige
            </button>
            <span className="text-xs text-muted-foreground">
              Pagina {page} van {totalPages}
            </span>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-30 transition-colors"
            >
              Volgende
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Partijen Tab ──────────────────────────────────────────────────────────────

function PartijenTab({ zaak }: { zaak: any }) {
  const { data: clientConflict } = useConflictCheck(
    zaak.client?.id || undefined,
    "client"
  );
  const { data: opponentConflict } = useConflictCheck(
    zaak.opposing_party?.id || undefined,
    "opposing_party"
  );

  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <h2 className="mb-4 text-sm font-semibold text-card-foreground uppercase tracking-wider">
        Partijen
      </h2>
      <div className="grid gap-3 sm:grid-cols-2">
        {zaak.client && (
          <Link
            href={`/relaties/${zaak.client.id}`}
            className="flex items-center gap-3 rounded-lg border border-border p-4 hover:border-primary/30 hover:bg-muted/50 transition-all"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
              <Building2 className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">
                {zaak.client.name}
              </p>
              <span className="text-xs font-medium text-primary">Client</span>
            </div>
          </Link>
        )}
        {zaak.opposing_party && (
          <Link
            href={`/relaties/${zaak.opposing_party.id}`}
            className="flex items-center gap-3 rounded-lg border border-border p-4 hover:border-amber-300/50 hover:bg-muted/50 transition-all"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-50">
              <User className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">
                {zaak.opposing_party.name}
              </p>
              <span className="text-xs font-medium text-amber-600">
                Wederpartij
              </span>
            </div>
          </Link>
        )}
        {zaak.parties &&
          zaak.parties.map((party: any) => (
            <Link
              key={party.id}
              href={`/relaties/${party.contact.id}`}
              className="flex items-center gap-3 rounded-lg border border-border p-4 hover:bg-muted/50 transition-all"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                <User className="h-5 w-5 text-muted-foreground" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">
                  {party.contact.name}
                </p>
                <span className="text-xs font-medium text-muted-foreground">
                  {party.role}
                </span>
                {party.external_reference && (
                  <p className="text-xs text-muted-foreground font-mono mt-0.5">
                    Ref: {party.external_reference}
                  </p>
                )}
              </div>
            </Link>
          ))}
      </div>

      {/* Conflict warnings */}
      {clientConflict?.has_conflict && (
        <div className="mt-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium text-amber-800">
                Conflict gedetecteerd — client
              </p>
              <p className="mt-0.5 text-xs text-amber-700">
                {zaak.client.name} is in {clientConflict.conflicts.length === 1 ? "een ander dossier" : `${clientConflict.conflicts.length} andere dossiers`} wederpartij:
              </p>
              <ul className="mt-1 space-y-0.5">
                {clientConflict.conflicts.map((c) => (
                  <li key={c.case_id} className="text-xs text-amber-700">
                    <span className="font-mono font-medium">{c.case_number}</span>
                    {" — wederpartij van "}
                    <span className="font-medium">{c.client_name}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
      {opponentConflict?.has_conflict && (
        <div className="mt-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium text-amber-800">
                Conflict gedetecteerd — wederpartij
              </p>
              <p className="mt-0.5 text-xs text-amber-700">
                {zaak.opposing_party.name} is in {opponentConflict.conflicts.length === 1 ? "een ander dossier" : `${opponentConflict.conflicts.length} andere dossiers`} client:
              </p>
              <ul className="mt-1 space-y-0.5">
                {opponentConflict.conflicts.map((c) => (
                  <li key={c.case_id} className="text-xs text-amber-700">
                    <span className="font-mono font-medium">{c.case_number}</span>
                    {" — cliënt"}
                    {c.opposing_party_name && (
                      <span> vs. {c.opposing_party_name}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Taken Tab ────────────────────────────────────────────────────────────────

const TASK_STATUS_BADGE: Record<string, string> = {
  pending: "bg-slate-50 text-slate-600 ring-slate-500/20",
  due: "bg-blue-50 text-blue-700 ring-blue-600/20",
  completed: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  skipped: "bg-slate-50 text-slate-500 ring-slate-400/20",
  overdue: "bg-red-50 text-red-700 ring-red-600/20",
};

function TakenTab({ caseId }: { caseId: string }) {
  const { data: tasksData, isLoading } = useWorkflowTasks({ case_id: caseId });
  const completeTask = useCompleteTask();
  const skipTask = useSkipTask();
  const createTask = useCreateTask();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    title: "",
    task_type: "custom",
    due_date: new Date().toISOString().split("T")[0],
    description: "",
  });

  const handleComplete = async (taskId: string) => {
    try {
      await completeTask.mutateAsync(taskId);
      toast.success("Taak afgerond");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleSkip = async (taskId: string) => {
    try {
      await skipTask.mutateAsync(taskId);
      toast.success("Taak overgeslagen");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createTask.mutateAsync({
        case_id: caseId,
        task_type: form.task_type,
        title: form.title,
        due_date: form.due_date,
        ...(form.description && { description: form.description }),
      });
      toast.success("Taak aangemaakt");
      setShowForm(false);
      setForm({
        title: "",
        task_type: "custom",
        due_date: new Date().toISOString().split("T")[0],
        description: "",
      });
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const tasks = tasksData?.items ?? [];
  const openTasks = tasks.filter(
    (t) => t.status === "pending" || t.status === "due" || t.status === "overdue"
  );
  const completedTasks = tasks.filter(
    (t) => t.status === "completed" || t.status === "skipped"
  );

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-foreground">Taken</h2>
          <p className="text-sm text-muted-foreground">
            {openTasks.length} openstaand
            {completedTasks.length > 0 &&
              ` · ${completedTasks.length} afgerond`}
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          Taak toevoegen
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <form
          onSubmit={handleCreate}
          className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-3"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-foreground">
                Titel *
              </label>
              <input
                type="text"
                required
                value={form.title}
                onChange={(e) =>
                  setForm((f) => ({ ...f, title: e.target.value }))
                }
                placeholder="Bijv. Bel debiteur voor betalingsherinnering"
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Type
              </label>
              <select
                value={form.task_type}
                onChange={(e) =>
                  setForm((f) => ({ ...f, task_type: e.target.value }))
                }
                className={inputClass}
              >
                {Object.entries(TASK_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Deadline *
              </label>
              <input
                type="date"
                required
                value={form.due_date}
                onChange={(e) =>
                  setForm((f) => ({ ...f, due_date: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-foreground">
                Omschrijving
              </label>
              <input
                type="text"
                value={form.description}
                onChange={(e) =>
                  setForm((f) => ({ ...f, description: e.target.value }))
                }
                className={inputClass}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createTask.isPending}
              className="rounded-lg bg-primary px-4 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              Aanmaken
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-medium hover:bg-muted"
            >
              Annuleren
            </button>
          </div>
        </form>
      )}

      {/* Loading */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg skeleton" />
          ))}
        </div>
      ) : tasks.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <CheckCircle2 className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">
            Geen taken voor dit dossier
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Taken worden automatisch aangemaakt bij statuswijzigingen
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Open tasks */}
          {openTasks.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Openstaand
              </h3>
              {openTasks.map((task) => (
                <div
                  key={task.id}
                  className={`flex items-start gap-3 rounded-lg border p-4 transition-colors ${
                    task.status === "overdue"
                      ? "border-red-200 bg-red-50/50"
                      : "border-border bg-card"
                  }`}
                >
                  <button
                    onClick={() => handleComplete(task.id)}
                    className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 border-border hover:border-primary hover:bg-primary/10 transition-colors"
                    title="Markeer als afgerond"
                  >
                    {completeTask.isPending ? (
                      <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
                    ) : null}
                  </button>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-medium text-foreground">
                        {task.title}
                      </p>
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${
                          TASK_STATUS_BADGE[task.status] ??
                          "bg-slate-50 text-slate-600 ring-slate-500/20"
                        }`}
                      >
                        {TASK_STATUS_LABELS[task.status] ?? task.status}
                      </span>
                    </div>
                    {task.description && (
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {task.description}
                      </p>
                    )}
                    <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Deadline: {formatDateShort(task.due_date)}
                      </span>
                      <span>
                        {TASK_TYPE_LABELS[task.task_type] ?? task.task_type}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => handleSkip(task.id)}
                    className="shrink-0 rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                    title="Overslaan"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Completed tasks */}
          {completedTasks.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Afgerond
              </h3>
              {completedTasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-start gap-3 rounded-lg border border-border bg-muted/30 p-4 opacity-60"
                >
                  <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-100">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-medium text-foreground line-through">
                        {task.title}
                      </p>
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${
                          TASK_STATUS_BADGE[task.status] ??
                          "bg-slate-50 text-slate-600 ring-slate-500/20"
                        }`}
                      >
                        {TASK_STATUS_LABELS[task.status] ?? task.status}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {task.completed_at
                        ? formatDateShort(task.completed_at)
                        : ""}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Documenten Tab ──────────────────────────────────────────────────────────

function FacturenTab({ caseId, clientId }: { caseId: string; clientId?: string }) {
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
                href={`/facturen/${inv.id}`}
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

function DocumentenTab({ caseId, caseNumber, caseStatus, debtorType, opposingPartyName }: { caseId: string; caseNumber?: string; caseStatus?: string; debtorType?: string | null; opposingPartyName?: string }) {
  const { data: templates, isLoading: templatesLoading } = useDocxTemplates();
  const { data: documents, isLoading: docsLoading } = useCaseDocuments(caseId);
  const generateDocx = useGenerateDocx(caseId);
  const deleteDocument = useDeleteDocument(caseId);
  const sendDocument = useSendDocument(caseId);

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
                  <button
                    onClick={() => deleteCaseFile.mutate(f.id)}
                    className="shrink-0 rounded-lg p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors opacity-0 group-hover:opacity-100"
                    title="Verwijderen"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
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
                    <p className="text-sm font-medium text-foreground">
                      {doc.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDateShort(doc.created_at)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
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
    </div>
  );
}

// ── Correspondentie Tab ──────────────────────────────────────────────────────

function CorrespondentieTab({ caseId }: { caseId: string }) {
  const { data: logs, isLoading } = useEmailLogs(caseId);

  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <h2 className="mb-1 text-base font-semibold text-foreground">
        Verzonden e-mails
      </h2>
      <p className="mb-4 text-sm text-muted-foreground">
        Overzicht van alle e-mails verstuurd vanuit dit dossier
      </p>

      {isLoading ? (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          E-mails laden...
        </div>
      ) : !logs?.length ? (
        <div className="rounded-lg border border-dashed border-border py-8 text-center">
          <Mail className="mx-auto h-8 w-8 text-muted-foreground/30" />
          <p className="mt-2 text-sm text-muted-foreground">
            Nog geen e-mails verstuurd voor dit dossier
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                <th className="pb-3 pr-4">Datum</th>
                <th className="pb-3 pr-4">Ontvanger</th>
                <th className="pb-3 pr-4">Onderwerp</th>
                <th className="pb-3 pr-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {logs.map((log: EmailLogEntry) => (
                <tr key={log.id} className="hover:bg-muted/30 transition-colors">
                  <td className="py-3 pr-4 whitespace-nowrap text-muted-foreground">
                    {formatDateShort(log.sent_at)}
                  </td>
                  <td className="py-3 pr-4">{log.recipient}</td>
                  <td className="py-3 pr-4">{log.subject}</td>
                  <td className="py-3 pr-4">
                    {log.status === "sent" ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-600">
                        <CheckCircle2 className="h-3 w-3" />
                        Verzonden
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-xs font-medium text-red-600">
                        <XCircle className="h-3 w-3" />
                        Mislukt
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
