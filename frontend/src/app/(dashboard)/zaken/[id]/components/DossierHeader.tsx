"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  Briefcase,
  CalendarDays,
  CheckCircle2,
  Clock,
  CreditCard,
  Euro,
  FileText,
  Mail,
  MessageSquare,
  Phone,
  Receipt,
  Trash2,
  Users,
  XCircle,
  AlertTriangle,
} from "lucide-react";
import {
  STATUS_LABELS,
  STATUS_BADGE,
  NEXT_STATUSES,
  TYPE_LABELS,
  INTEREST_LABELS,
} from "../types";
import {
  getTemplateLabel,
  getTemplatesForStatus,
} from "@/hooks/use-documents";
import {
  PHASE_LABELS,
  PHASE_ORDER,
  getPhaseForStatus,
  getAvailableTransitions,
} from "@/hooks/use-workflow";
import { formatCurrency, formatDate } from "@/lib/utils";
import { RenteoverzichtDialog } from "./RenteoverzichtDialog";
import { useIncassoPipelineSteps } from "@/hooks/use-incasso";
import { useUpdateCase } from "@/hooks/use-cases";
import { toast } from "sonner";

// ── VerjaringBadge ──────────────────────────────────────────────────────────

function VerjaringBadge({
  dateOpened,
  status,
}: {
  dateOpened: string;
  status: string;
}) {
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

// ── DossierHeader Props ─────────────────────────────────────────────────────

interface DossierHeaderProps {
  zaak: any;
  isIncasso: boolean;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  handleStatusChange: (newStatus: string) => void;
  handleDelete: () => void;
  updateStatusPending: boolean;
  statusSuggestion: { status: string; templates: string[] } | null;
  setStatusSuggestion: (v: { status: string; templates: string[] } | null) => void;
  workflowStatuses: any;
  workflowTransitions: any;
  timer: any;
  startTimer: (caseId: string, label: string) => void;
  setCaseEmailOpen: (v: boolean) => void;
  setPhoneNoteText: (v: string) => void;
}

export default function DossierHeader({
  zaak,
  isIncasso,
  activeTab,
  setActiveTab,
  handleStatusChange,
  handleDelete,
  updateStatusPending,
  statusSuggestion,
  setStatusSuggestion,
  workflowStatuses,
  workflowTransitions,
  timer,
  startTimer,
  setCaseEmailOpen,
  setPhoneNoteText,
}: DossierHeaderProps) {
  const [renteDialogOpen, setRenteDialogOpen] = useState(false);

  // DF2-09: Pipeline step selector for incasso cases
  const { data: pipelineSteps } = useIncassoPipelineSteps(true);
  const updateCase = useUpdateCase();
  const activeSteps = pipelineSteps?.filter((s: any) => s.is_active) ?? [];

  const handleStepChange = async (stepId: string) => {
    try {
      await updateCase.mutateAsync({
        id: zaak.id,
        data: {
          incasso_step_id: stepId || null,
          incasso_step_entered_at: stepId ? new Date().toISOString() : null,
        },
      });
      const stepName = activeSteps.find((s: any) => s.id === stepId)?.name ?? "Geen";
      toast.success(`Incassostap gewijzigd naar: ${stepName}`);
    } catch {
      toast.error("Kon incassostap niet wijzigen");
    }
  };

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
    <>
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

          {/* DF2-09: Pipeline step selector */}
          {activeSteps.length > 0 && (
            <div className="flex items-center gap-3 mt-4 pt-4 border-t border-border">
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                Incassostap:
              </span>
              <select
                value={zaak.incasso_step_id ?? ""}
                onChange={(e) => handleStepChange(e.target.value)}
                disabled={updateCase.isPending}
                className="rounded-md border border-input bg-background px-3 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20"
              >
                <option value="">Niet toegewezen</option>
                {activeSteps.map((step: any) => (
                  <option key={step.id} value={step.id}>
                    {step.name}
                  </option>
                ))}
              </select>
            </div>
          )}

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
                      disabled={updateStatusPending}
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
                NEXT_STATUSES[zaak.status]?.map((nextStatus) => (
                  <button
                    key={nextStatus}
                    onClick={() => handleStatusChange(nextStatus)}
                    disabled={updateStatusPending}
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
          <div className="space-y-1 min-w-0">
            {zaak.client && (
              <Link
                href={`/relaties/${zaak.client.id}`}
                className="text-sm font-medium text-foreground hover:text-primary transition-colors block break-words"
              >
                {zaak.client.name}
              </Link>
            )}
            {zaak.opposing_party && (
              <p className="text-xs text-muted-foreground break-words">
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
        <button
          type="button"
          onClick={() => setCaseEmailOpen(true)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-xs font-medium text-blue-700 hover:bg-blue-100 hover:border-blue-300 transition-colors"
        >
          <Mail className="h-3.5 w-3.5" />
          E-mail versturen
        </button>
        {isIncasso && (
          <>
            <button
              type="button"
              onClick={() => setRenteDialogOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors"
            >
              <Euro className="h-3.5 w-3.5 text-orange-500" />
              Renteoverzicht
            </button>
            <RenteoverzichtDialog
              caseId={zaak.id}
              open={renteDialogOpen}
              onOpenChange={setRenteDialogOpen}
            />
          </>
        )}
      </div>
    </>
  );
}
