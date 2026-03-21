"use client";

import { useState } from "react";
import { GripVertical, ToggleLeft, ToggleRight, ChevronRight, Clock, AlertTriangle, GitBranch } from "lucide-react";
import { toast } from "sonner";
import {
  useWorkflowStatuses,
  useWorkflowTransitions,
  useWorkflowRules,
  useUpdateWorkflowRule,
  PHASE_LABELS,
  PHASE_ORDER,
  ACTION_TYPE_LABELS,
  type WorkflowStatus as WFStatus,
  type WorkflowRule,
} from "@/hooks/use-workflow";

const PHASE_BADGE_CLASSES: Record<string, string> = {
  minnelijk: "bg-blue-50 text-blue-700 ring-blue-600/20",
  regeling: "bg-amber-50 text-amber-700 ring-amber-600/20",
  gerechtelijk: "bg-purple-50 text-purple-700 ring-purple-600/20",
  executie: "bg-red-50 text-red-700 ring-red-600/20",
  afgerond: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
};

const DEBTOR_TYPE_LABELS: Record<string, string> = {
  b2b: "B2B",
  b2c: "B2C",
  both: "Beide",
};

export function WorkflowTab() {
  const { data: statuses, isLoading: loadingStatuses } = useWorkflowStatuses();
  const { data: transitions, isLoading: loadingTransitions } =
    useWorkflowTransitions();
  const { data: rules, isLoading: loadingRules } = useWorkflowRules();
  const updateRule = useUpdateWorkflowRule();
  const [activeSection, setActiveSection] = useState<
    "statuses" | "rules"
  >("statuses");

  if (loadingStatuses || loadingTransitions || loadingRules) {
    return (
      <div className="space-y-6">
        <div className="flex gap-2">
          <div className="h-9 w-36 rounded-lg skeleton" />
          <div className="h-9 w-44 rounded-lg skeleton" />
        </div>
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center gap-3 rounded-lg border border-border bg-card p-4">
              <div className="h-4 w-4 rounded skeleton" />
              <div className="h-4 w-32 rounded skeleton" />
              <div className="h-5 w-20 rounded-full skeleton ml-auto" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const sections = [
    { id: "statuses" as const, label: "Statussen & Fases" },
    { id: "rules" as const, label: "Automatiseringsregels" },
  ];

  return (
    <div className="space-y-6">
      {/* Section toggle */}
      <div className="flex gap-1 rounded-lg bg-muted p-1">
        {sections.map((section) => (
          <button
            key={section.id}
            onClick={() => setActiveSection(section.id)}
            className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-all ${
              activeSection === section.id
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {section.label}
          </button>
        ))}
      </div>

      {activeSection === "statuses" && (
        <StatusesSection statuses={statuses ?? []} transitions={transitions ?? []} />
      )}
      {activeSection === "rules" && (
        <RulesSection
          rules={rules ?? []}
          statuses={statuses ?? []}
          onToggleRule={(id, active) =>
            updateRule.mutate(
              { id, data: { is_active: active } },
              {
                onSuccess: () =>
                  toast.success(
                    active ? "Regel geactiveerd" : "Regel gedeactiveerd"
                  ),
              }
            )
          }
        />
      )}
    </div>
  );
}

// ── Statuses Section ────────────────────────────────────────────────────────

function StatusesSection({
  statuses,
  transitions,
}: {
  statuses: WFStatus[];
  transitions: { from_status_id: string; to_status_id: string; debtor_type: string; is_active: boolean }[];
}) {
  // Group statuses by phase
  const groupedByPhase: Record<string, WFStatus[]> = {};
  for (const phase of PHASE_ORDER) {
    groupedByPhase[phase] = statuses
      .filter((s) => s.phase === phase && s.is_active)
      .sort((a, b) => a.sort_order - b.sort_order);
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-foreground">
              Incasso fases & statussen
            </h2>
            <p className="text-sm text-muted-foreground">
              Statussen gegroepeerd per fase van het incassotraject
            </p>
          </div>
        </div>

        <div className="space-y-4">
          {PHASE_ORDER.map((phase) => {
            const phaseStatuses = groupedByPhase[phase] ?? [];
            if (phaseStatuses.length === 0) return null;

            return (
              <div key={phase} className="rounded-lg border border-border">
                <div className="flex items-center gap-2 border-b border-border bg-muted/30 px-4 py-2.5">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
                      PHASE_BADGE_CLASSES[phase] ?? "bg-slate-50 text-slate-600 ring-slate-500/20"
                    }`}
                  >
                    {PHASE_LABELS[phase]}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {phaseStatuses.length} status{phaseStatuses.length !== 1 ? "sen" : ""}
                  </span>
                </div>
                <div className="divide-y divide-border">
                  {phaseStatuses.map((status) => {
                    // Count outgoing transitions for this status
                    const outgoing = transitions.filter(
                      (t) => t.from_status_id === status.id && t.is_active
                    );
                    return (
                      <div
                        key={status.id}
                        className="flex items-center justify-between px-4 py-3"
                      >
                        <div className="flex items-center gap-3">
                          <GripVertical className="h-4 w-4 text-muted-foreground/40" />
                          <div>
                            <p className="text-sm font-medium text-foreground">
                              {status.label}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {status.slug}
                              {status.is_initial && " · Startpunt"}
                              {status.is_terminal && " · Eindpunt"}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {outgoing.length > 0 && (
                            <span className="text-xs text-muted-foreground">
                              {outgoing.length} transitie{outgoing.length !== 1 ? "s" : ""}
                            </span>
                          )}
                          <div
                            className={`h-3 w-3 rounded-full bg-${status.color}-500`}
                            title={`Kleur: ${status.color}`}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Transition overview */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold text-foreground mb-2">
          Toegestane transities
        </h2>
        <p className="text-sm text-muted-foreground mb-4">
          Welke statusovergangen zijn mogelijk
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="py-2 px-3 text-left font-medium text-muted-foreground">
                  Van
                </th>
                <th className="py-2 px-3 text-center font-medium text-muted-foreground">
                  →
                </th>
                <th className="py-2 px-3 text-left font-medium text-muted-foreground">
                  Naar
                </th>
                <th className="py-2 px-3 text-left font-medium text-muted-foreground">
                  Type
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {transitions
                .filter((t) => t.is_active)
                .map((t, idx) => {
                  const fromStatus = statuses.find(
                    (s) => s.id === t.from_status_id
                  );
                  const toStatus = statuses.find(
                    (s) => s.id === t.to_status_id
                  );
                  if (!fromStatus || !toStatus) return null;
                  return (
                    <tr key={idx} className="hover:bg-muted/50">
                      <td className="py-2 px-3 text-foreground">
                        {fromStatus.label}
                      </td>
                      <td className="py-2 px-3 text-center text-muted-foreground">
                        <ChevronRight className="h-4 w-4 inline" />
                      </td>
                      <td className="py-2 px-3 text-foreground">
                        {toStatus.label}
                      </td>
                      <td className="py-2 px-3">
                        <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset bg-slate-50 text-slate-600 ring-slate-500/20">
                          {DEBTOR_TYPE_LABELS[t.debtor_type] ?? t.debtor_type}
                        </span>
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Rules Section ───────────────────────────────────────────────────────────

function RulesSection({
  rules,
  statuses,
  onToggleRule,
}: {
  rules: WorkflowRule[];
  statuses: WFStatus[];
  onToggleRule: (id: string, active: boolean) => void;
}) {
  const getStatusLabel = (id: string) =>
    statuses.find((s) => s.id === id)?.label ?? "Onbekend";

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-foreground">
              Automatiseringsregels
            </h2>
            <p className="text-sm text-muted-foreground">
              Regels die automatisch taken aanmaken bij statuswijzigingen
            </p>
          </div>
        </div>

        {rules.length === 0 ? (
          <div className="py-8 text-center">
            <AlertTriangle className="mx-auto h-8 w-8 text-muted-foreground/30" />
            <p className="mt-2 text-sm text-muted-foreground">
              Geen regels geconfigureerd
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {rules
              .sort((a, b) => a.sort_order - b.sort_order)
              .map((rule) => (
                <div
                  key={rule.id}
                  className={`rounded-lg border p-4 transition-colors ${
                    rule.is_active
                      ? "border-border bg-background"
                      : "border-border/50 bg-muted/30 opacity-60"
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="text-sm font-medium text-foreground">
                          {rule.name}
                        </p>
                        <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset bg-slate-50 text-slate-600 ring-slate-500/20">
                          {DEBTOR_TYPE_LABELS[rule.debtor_type] ?? rule.debtor_type}
                        </span>
                        {rule.auto_execute && (
                          <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset bg-amber-50 text-amber-700 ring-amber-600/20">
                            Auto
                          </span>
                        )}
                      </div>
                      {rule.description && (
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {rule.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <GitBranch className="h-3 w-3" />
                          Bij: {getStatusLabel(rule.trigger_status_id)}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Na {rule.days_delay} dag{rule.days_delay !== 1 ? "en" : ""}
                        </span>
                        <span>
                          Actie: {ACTION_TYPE_LABELS[rule.action_type] ?? rule.action_type}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => onToggleRule(rule.id, !rule.is_active)}
                      className="shrink-0 mt-0.5"
                      title={rule.is_active ? "Deactiveren" : "Activeren"}
                    >
                      {rule.is_active ? (
                        <ToggleRight className="h-6 w-6 text-primary" />
                      ) : (
                        <ToggleLeft className="h-6 w-6 text-muted-foreground" />
                      )}
                    </button>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
