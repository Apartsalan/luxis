"use client";

import { Loader2, Clock, ArrowRight, FileText, Mail, Bot, User } from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { useCaseStepHistory, type CaseStepHistory } from "@/hooks/use-incasso";

const CATEGORY_STYLES: Record<string, string> = {
  minnelijk: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  gerechtelijk: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  executie: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  regeling: "bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400",
  administratief: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  afsluiting: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
};

const TRIGGER_LABELS: Record<string, { label: string; icon: typeof User }> = {
  manual: { label: "Handmatig", icon: User },
  batch: { label: "Batch actie", icon: ArrowRight },
  auto: { label: "Automatisch", icon: Bot },
  seed: { label: "Standaard", icon: ArrowRight },
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("nl-NL", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

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
                        CATEGORY_STYLES[entry.step_category] || CATEGORY_STYLES.administratief
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
                    {formatDate(entry.entered_at)}
                  </span>
                  {entry.exited_at && (
                    <span className="flex items-center gap-1">
                      <ArrowRight className="h-3 w-3" />
                      {formatDate(entry.exited_at)}
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
                    <span className="flex items-center gap-1 text-blue-600 dark:text-blue-400">
                      <FileText className="h-3 w-3" />
                      Brief gegenereerd
                    </span>
                  )}
                  {entry.email_sent && (
                    <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
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
