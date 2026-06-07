"use client";

import { Loader2, Clock, ArrowRight, FileText, Mail, Bot, User } from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { useCaseStepHistory, type CaseStepHistory } from "@/hooks/use-incasso";
import { formatDateTime } from "@/lib/utils";
import { STEP_CATEGORY_STYLES } from "@/lib/status-constants";

const TRIGGER_LABELS: Record<string, { label: string; icon: typeof User }> = {
  manual: { label: "Handmatig", icon: User },
  batch: { label: "Batch actie", icon: ArrowRight },
  auto: { label: "Automatisch", icon: Bot },
  seed: { label: "Standaard", icon: ArrowRight },
};

function formatDuration(entered: string, exited: string | null): string {
  const start = new Date(entered).getTime();
  const end = exited ? new Date(exited).getTime() : Date.now();
  const days = Math.floor((end - start) / (1000 * 60 * 60 * 24));
  if (days === 0) return "< 1 dag";
  return `${days} ${days === 1 ? "dag" : "dagen"}`;
}

export function StaphistorieTab({ caseId }: { caseId: string }) {
  const { data: history, isLoading } = useCaseStepHistory(caseId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!history || history.length === 0) {
    return (
      <EmptyState
        icon={Clock}
        title="Geen staphistorie"
        description="Dit dossier heeft nog geen stappen doorlopen."
      />
    );
  }

  const sorted = [...history].sort(
    (a, b) => new Date(b.entered_at).getTime() - new Date(a.entered_at).getTime()
  );

  return (
    <div className="space-y-1">
      <div className="relative pl-6">
        <div className="absolute left-[11px] top-2 bottom-2 w-0.5 bg-border" />

        {sorted.map((entry, i) => {
          const trigger = TRIGGER_LABELS[entry.trigger_type] || TRIGGER_LABELS.manual;
          const TriggerIcon = trigger.icon;
          const isActive = i === 0 && !entry.exited_at;

          return (
            <div key={entry.id} className="relative pb-6 last:pb-0">
              <div
                className={`absolute left-[-13px] top-1.5 h-3 w-3 rounded-full border-2 ${
                  isActive
                    ? "border-primary bg-primary"
                    : "border-border bg-background"
                }`}
              />

              <div className={`rounded-lg border p-4 ${isActive ? "border-primary/30 bg-primary/5" : "border-border"}`}>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm text-foreground">
                      {entry.step_name}
                    </span>
                    <span
                      className={`inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] font-semibold ${
                        STEP_CATEGORY_STYLES[entry.step_category] || STEP_CATEGORY_STYLES.administratief
                      }`}
                    >
                      {entry.step_category}
                    </span>
                    {isActive && (
                      <span className="inline-flex items-center rounded-md bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
                        Actief
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {formatDuration(entry.entered_at, entry.exited_at)}
                  </span>
                </div>

                <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDateTime(entry.entered_at, "short")}
                  </span>
                  {entry.exited_at && (
                    <span className="flex items-center gap-1">
                      <ArrowRight className="h-3 w-3" />
                      {formatDateTime(entry.exited_at, "short")}
                    </span>
                  )}
                  <span className="flex items-center gap-1">
                    <TriggerIcon className="h-3 w-3" />
                    {trigger.label}
                    {entry.triggered_by_name && ` — ${entry.triggered_by_name}`}
                  </span>
                </div>

                <div className="mt-1.5 flex items-center gap-3 text-xs text-muted-foreground">
                  {entry.template_sent && (
                    <span className="flex items-center gap-1 text-blue-600">
                      <FileText className="h-3 w-3" />
                      Brief gegenereerd
                    </span>
                  )}
                  {entry.email_sent && (
                    <span className="flex items-center gap-1 text-emerald-600">
                      <Mail className="h-3 w-3" />
                      E-mail verzonden
                    </span>
                  )}
                </div>

                {entry.notes && (
                  <p className="mt-2 text-sm text-muted-foreground border-t border-border pt-2">
                    {entry.notes}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
