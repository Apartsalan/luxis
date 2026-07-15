"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Briefcase,
  CheckCircle2,
  Clock,
  Euro,
  FileText,
  Mail,
  MessageSquare,
  Phone,
  Receipt,
  RotateCcw,
  Trash2,
  XCircle,
  AlertTriangle,
} from "lucide-react";
import {
  STATUS_LABELS,
  STATUS_BADGE,
  TYPE_LABELS,
} from "../types";
import {
  getTemplateLabel,
} from "@/hooks/use-documents";
import { formatCurrency, formatDate, formatDateShort } from "@/lib/utils";
import { useWorkflowTasks } from "@/hooks/use-workflow";
import { useTimeEntrySummary } from "@/hooks/use-time-entries";
import { CASE_STATUS_BADGE_FALLBACK, DEBTOR_TYPE_BADGE } from "@/lib/status-constants";
import { TONES } from "@/lib/tones";
import { RenteoverzichtDialog } from "./RenteoverzichtDialog";
import { BackButton } from "@/components/back-button";
import type { NoteMode } from "./NoteDialog";
import { useIncassoPipelineSteps } from "@/hooks/use-incasso";
import type { PipelineStep } from "@/hooks/use-incasso";
import { useUpdateCase } from "@/hooks/use-cases";
import { useFinancialSummary } from "@/hooks/use-collections";
import type { CaseDetail } from "@/hooks/use-cases";
import type { TimerState } from "@/hooks/use-timer";
import { toast } from "sonner";

const PHASE_ORDER = [
  "minnelijk",
  "gerechtelijk",
  "regeling",
  "administratief",
  "afsluiting",
];

const PHASE_LABELS: Record<string, string> = {
  minnelijk: "Minnelijk",
  gerechtelijk: "Gerechtelijk",
  regeling: "Regeling",
  administratief: "Administratief",
  afsluiting: "Afsluiting",
};

const PHASE_ACTIVE_CLASSES: Record<string, string> = {
  minnelijk: `ring-4 ${TONES.info.stepper}`,
  gerechtelijk: `ring-4 ${TONES.legal.stepper}`,
  regeling: `ring-4 ${TONES.warning.stepper}`,
  administratief: `ring-4 ${TONES.neutral.solid} text-white ring-slate-500/20`,
  afsluiting: `ring-4 ${TONES.success.stepper}`,
};

// ── VerjaringBadge ──────────────────────────────────────────────────────────

function VerjaringBadge({
  dateOpened,
  serverVerjaringDate,
  status,
}: {
  dateOpened: string;
  // B2 — server-berekende verjaringsdatum (zelfde bron + jaarrekenwerk als de
  // monitor; JS setFullYear wijkt af rond 29 februari). Terugval: zelf rekenen
  // vanaf de openingsdatum.
  serverVerjaringDate?: string | null;
  status: string;
}) {
  const VERJARING_YEARS = 5;
  const terminalStatuses = ["betaald", "afgesloten", "oninbaar", "schikking"];
  if (terminalStatuses.includes(status)) return null;

  let verjaringDate: Date;
  if (serverVerjaringDate) {
    verjaringDate = new Date(serverVerjaringDate);
  } else {
    verjaringDate = new Date(dateOpened);
    verjaringDate.setFullYear(verjaringDate.getFullYear() + VERJARING_YEARS);
  }

  const now = new Date();
  const daysLeft = Math.ceil(
    (verjaringDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
  );

  if (daysLeft <= 0) {
    return (
      <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${TONES.danger.badge}`}>
        <AlertTriangle className="h-3 w-3" />
        Verjaard
      </span>
    );
  }

  if (daysLeft <= 30) {
    return (
      <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${TONES.danger.badge}`}>
        <AlertTriangle className="h-3 w-3" />
        Verjaring: {daysLeft}d
      </span>
    );
  }

  if (daysLeft <= 90) {
    return (
      <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${TONES.warning.badge}`}>
        <Clock className="h-3 w-3" />
        Verjaring: {daysLeft}d
      </span>
    );
  }

  return null;
}

// ── DossierHeader Props ─────────────────────────────────────────────────────

interface DossierHeaderProps {
  zaak: CaseDetail;
  isIncasso: boolean;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  handleStatusChange: (newStatus: string) => void;
  handleDelete: () => void;
  updateStatusPending: boolean;
  statusSuggestion: { status: string; templates: string[] } | null;
  setStatusSuggestion: (v: { status: string; templates: string[] } | null) => void;
  timer: TimerState;
  startTimer: (caseId: string, label: string) => void;
  setCaseEmailOpen: (v: boolean) => void;
  onOpenNote: (mode: NoteMode) => void;
  onGenerateDraft: () => Promise<void> | void;
  isGeneratingDraft: boolean;
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
  timer,
  startTimer,
  setCaseEmailOpen,
  onOpenNote,
  onGenerateDraft,
  isGeneratingDraft,
}: DossierHeaderProps) {
  const [renteDialogOpen, setRenteDialogOpen] = useState(false);
  const { data: financials } = useFinancialSummary(isIncasso ? zaak.id : undefined);
  // S216 blok 3: sturing + geldstrook voor een gewone (niet-incasso) zaak.
  // Beide queries delen de cache met het takenblok + de zijbalk → geen extra call.
  const { data: tasks } = useWorkflowTasks({ case_id: zaak.id });
  const { data: timeSummary } = useTimeEntrySummary({ case_id: zaak.id });
  const openTasks = (tasks ?? []).filter((t) =>
    ["pending", "due", "overdue"].includes(t.status)
  );
  const nextTask =
    [...openTasks]
      .filter((t) => t.due_date)
      .sort(
        (a, b) => new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
      )[0] ?? openTasks[0];
  const ohwAmount = timeSummary?.total_amount ?? 0;

  // DF2-09: Pipeline step selector for incasso cases.
  // S166 (punt 4, "B2C anders dan B2B"): toon alleen de stappen die gelden voor het
  // debiteurtype van dit dossier — een B2C-dossier ziet de 14-dagenbrief (en niet de
  // B2B-only faillissement-stappen), een B2B-dossier andersom. "both"-stappen gelden
  // voor allebei. Zonder debtor_type tonen we alles.
  const { data: pipelineSteps } = useIncassoPipelineSteps(true);
  const updateCase = useUpdateCase();
  const activeSteps =
    pipelineSteps?.filter(
      (s: PipelineStep) =>
        s.is_active &&
        (!zaak.debtor_type ||
          s.debtor_type === "both" ||
          s.debtor_type === zaak.debtor_type)
    ) ?? [];

  const handleStepChange = async (stepId: string) => {
    try {
      await updateCase.mutateAsync({
        id: zaak.id,
        data: {
          incasso_step_id: stepId || null,
        },
      });
      const stepName = activeSteps.find((s: PipelineStep) => s.id === stepId)?.name ?? "Geen";
      toast.success(`Incassostap gewijzigd naar: ${stepName}`);
    } catch {
      toast.error("Kon incassostap niet wijzigen");
    }
  };

  // S199: de actuele pijplijnstap is de enige bron voor de dossierfase.
  const currentStep = pipelineSteps?.find(
    (step: PipelineStep) => step.id === zaak.incasso_step_id
  );
  const currentPhase =
    currentStep && PHASE_ORDER.includes(currentStep.step_category)
      ? currentStep.step_category
      : null;
  const currentPhaseIndex = currentPhase
    ? PHASE_ORDER.indexOf(currentPhase)
    : -1;
  const isTerminal =
    zaak.status === "betaald" || zaak.status === "afgesloten";

  return (
    <>
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <BackButton
            fallbackHref="/zaken"
            className="mt-1 rounded-lg p-2 hover:bg-muted transition-colors"
          />
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold text-foreground">
                {zaak.case_number}
              </h1>
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
                  STATUS_BADGE[zaak.status] ??
                  CASE_STATUS_BADGE_FALLBACK
                }`}
              >
                {STATUS_LABELS[zaak.status] ?? zaak.status}
              </span>
              {zaak.debtor_type && (
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
                    zaak.debtor_type === "b2b"
                      ? DEBTOR_TYPE_BADGE.b2b
                      : DEBTOR_TYPE_BADGE.b2c
                  }`}
                >
                  {zaak.debtor_type === "b2b" ? "B2B" : "B2C"}
                </span>
              )}
              {isIncasso && (
                <VerjaringBadge
                  dateOpened={zaak.date_opened}
                  serverVerjaringDate={zaak.verjaring_date}
                  status={zaak.status}
                />
              )}
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
          {currentPhase && (
            <div className="flex items-center gap-1 overflow-x-auto pb-1">
            {PHASE_ORDER.map((phase, index) => {
              const isActive = phase === currentPhase;
              const isPast = currentPhaseIndex >= 0 && index < currentPhaseIndex;
              return (
                <div key={phase} className="flex items-center flex-1 min-w-0">
                  <div className="flex flex-col items-center gap-1.5 flex-1 min-w-0">
                    <div
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-all ${
                        isActive
                          ? PHASE_ACTIVE_CLASSES[phase] ?? `${TONES.neutral.solid} text-white`
                          : isPast
                            ? `${TONES.success.solid} text-white`
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
                            ? TONES.success.text
                            : "text-muted-foreground"
                      }`}
                    >
                      {PHASE_LABELS[phase]}
                    </span>
                  </div>
                  {index < PHASE_ORDER.length - 1 && (
                    <div
                      className={`hidden sm:block h-0.5 w-4 shrink-0 mx-0.5 ${
                        isPast ? TONES.success.solidSoft : "bg-border"
                      }`}
                    />
                  )}
                </div>
              );
            })}
            </div>
          )}

          {/* DF2-09: Pipeline step selector */}
          {activeSteps.length > 0 && (
            <div
              className={`flex items-center gap-3 flex-wrap ${
                currentPhase ? "mt-4 border-t border-border pt-4" : ""
              }`}
            >
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
                {activeSteps.map((step: PipelineStep) => (
                  <option key={step.id} value={step.id}>
                    {step.name}
                  </option>
                ))}
              </select>
              {zaak.incasso_step_id && (
                <button
                  type="button"
                  onClick={() => { void onGenerateDraft(); }}
                  disabled={isGeneratingDraft}
                  className="inline-flex items-center gap-1.5 rounded-md bg-primary/10 text-primary px-3 py-1.5 text-xs font-medium hover:bg-primary/20 disabled:opacity-50"
                  title="AI genereert concept-email voor de huidige stap"
                >
                  {isGeneratingDraft ? "Bezig..." : "Concept genereren"}
                </button>
              )}
            </div>
          )}

          {/* Afsluiten / Heropenen (B3, S198): de pijplijn-stap stuurt het werk;
              hier alleen het dossier sluiten of weer heropenen. */}
          <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-border">
            {!isTerminal ? (
              <button
                onClick={() => handleStatusChange("afgesloten")}
                disabled={updateStatusPending}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
              >
                <CheckCircle2 className="h-3 w-3" />
                Dossier afsluiten
              </button>
            ) : (
              <button
                onClick={() =>
                  handleStatusChange(zaak.incasso_step_id ? "in_behandeling" : "nieuw")
                }
                disabled={updateStatusPending}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary/10 text-primary px-3 py-1.5 text-xs font-medium hover:bg-primary/20 transition-colors disabled:opacity-50"
              >
                <RotateCcw className="h-3 w-3" />
                Dossier heropenen
              </button>
            )}
          </div>
        </div>
      )}

      {/* S216 blok 3: sturing voor een gewone zaak — geen incasso-fasebalk, wel
          de eerstvolgende openstaande taak + afsluiten/heropenen (die knop zat
          voorheen alleen in de incasso-fasebalk, dus een advieszaak was niet af
          te sluiten). */}
      {!isIncasso && (
        <div className="rounded-xl border border-border bg-card p-4">
          {nextTask ? (
            <div className="flex items-center justify-between gap-3">
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                  <CheckCircle2 className="h-4 w-4 text-primary" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs text-muted-foreground">Volgende stap</p>
                  <p className="truncate text-sm font-medium text-foreground">
                    {nextTask.title}
                  </p>
                </div>
              </div>
              {nextTask.due_date && (
                <span className="shrink-0 text-xs font-medium text-muted-foreground">
                  {formatDateShort(nextTask.due_date)}
                </span>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Geen openstaande stap — voeg een taak toe op het Overzicht.
            </p>
          )}
          <div className="mt-4 flex flex-wrap gap-2 border-t border-border pt-4">
            {!isTerminal ? (
              <button
                onClick={() => handleStatusChange("afgesloten")}
                disabled={updateStatusPending}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
              >
                <CheckCircle2 className="h-3 w-3" />
                Dossier afsluiten
              </button>
            ) : (
              <button
                onClick={() => handleStatusChange("in_behandeling")}
                disabled={updateStatusPending}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary/10 text-primary px-3 py-1.5 text-xs font-medium hover:bg-primary/20 transition-colors disabled:opacity-50"
              >
                <RotateCcw className="h-3 w-3" />
                Dossier heropenen
              </button>
            )}
          </div>
        </div>
      )}

      {/* T2: Workflow-suggestie banner */}
      {statusSuggestion && (
        <div className={`rounded-xl border ${TONES.warning.border} ${TONES.warning.surface} p-4 flex items-center justify-between gap-4 animate-fade-in`}>
          <div className="flex items-center gap-3">
            <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${TONES.warning.iconBox}`}>
              <FileText className={`h-4 w-4 ${TONES.warning.text}`} />
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

      {/* Geldstrook (S216 blok 2): compacte band i.p.v. 4 losse kaarten die het
          hele scherm vulden. Openstaand — het sturende getal — stond nergens in
          de kop. De losse Rente- en Partijen-kaart vervallen (rente staat in de
          zijbalk + Debiteurinstellingen; partijen in de zijbalk + Overzicht). */}
      {isIncasso && (
        <div className="grid grid-cols-3 divide-x divide-border overflow-hidden rounded-xl border border-border bg-card">
          <div className="px-4 py-3">
            <p className="text-xs text-muted-foreground">Hoofdsom</p>
            <p className="mt-0.5 text-lg font-bold text-foreground tabular-nums">
              {formatCurrency(zaak.total_principal)}
            </p>
          </div>
          <div className="px-4 py-3">
            <p className="text-xs text-muted-foreground">Betaald</p>
            <p className={`mt-0.5 text-lg font-bold ${TONES.success.text} tabular-nums`}>
              {formatCurrency(zaak.total_paid)}
            </p>
          </div>
          <div className="px-4 py-3">
            <p className="text-xs text-muted-foreground">Openstaand</p>
            <p className="mt-0.5 text-lg font-bold text-foreground tabular-nums">
              {financials ? formatCurrency(financials.total_outstanding) : "—"}
            </p>
          </div>
        </div>
      )}

      {/* S216 blok 3: geldstrook voor een gewone zaak — onderhanden werk (uren ×
          tarief) + budget. Alleen tonen als er iets te tonen is (anders leeg). */}
      {!isIncasso && (ohwAmount > 0 || (zaak.budget != null && zaak.budget > 0)) && (
        <div className="grid grid-cols-2 divide-x divide-border overflow-hidden rounded-xl border border-border bg-card">
          <div className="px-4 py-3">
            <p className="text-xs text-muted-foreground">Onderhanden werk</p>
            <p className="mt-0.5 text-lg font-bold text-foreground tabular-nums">
              {formatCurrency(ohwAmount)}
            </p>
          </div>
          <div className="px-4 py-3">
            <p className="text-xs text-muted-foreground">Budget</p>
            <p className="mt-0.5 text-lg font-bold text-foreground tabular-nums">
              {zaak.budget != null && zaak.budget > 0
                ? formatCurrency(zaak.budget)
                : "—"}
            </p>
          </div>
        </div>
      )}

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
          <Clock className={`h-3.5 w-3.5 ${TONES.success.textMuted}`} />
          {timer.running && timer.caseId === zaak.id ? "Timer loopt..." : "Uren loggen"}
        </button>
        <button
          type="button"
          onClick={() => onOpenNote("note")}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors"
        >
          <MessageSquare className={`h-3.5 w-3.5 ${TONES.warning.textMuted}`} />
          Notitie
        </button>
        <button
          type="button"
          onClick={() => onOpenNote("phone")}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors"
        >
          <Phone className={`h-3.5 w-3.5 ${TONES.success.textMuted}`} />
          Telefoonnotitie
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("documenten")}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors"
        >
          <FileText className={`h-3.5 w-3.5 ${TONES.info.textMuted}`} />
          Document
        </button>
        <Link
          href={`/facturen/nieuw?case_id=${zaak.id}`}
          className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3 py-2 text-xs font-medium text-foreground hover:bg-muted transition-colors"
        >
          <Receipt className={`h-3.5 w-3.5 ${TONES.ai.textMuted}`} />
          Factuur
        </Link>
        <button
          type="button"
          onClick={() => setCaseEmailOpen(true)}
          className={`inline-flex items-center gap-1.5 rounded-lg border ${TONES.info.outlineButton} px-3 py-2 text-xs font-medium transition-colors`}
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
