"use client";

import { useState } from "react";
import {
  Bot,
  Check,
  ChevronDown,
  ChevronUp,
  Loader2,
  Play,
  X,
} from "lucide-react";
import { toast } from "sonner";
import {
  useEmailClassification,
  useApproveClassification,
  useRejectClassification,
  useExecuteClassification,
  useClassifyEmail,
  type Classification,
} from "@/hooks/use-ai-agent";

// ── Status badge ─────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  pending: {
    label: "Wacht op review",
    className: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
  },
  approved: {
    label: "Goedgekeurd",
    className: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  },
  rejected: {
    label: "Afgewezen",
    className: "bg-red-500/10 text-red-600 dark:text-red-400",
  },
  executed: {
    label: "Uitgevoerd",
    className: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  },
};

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] ?? {
    label: status,
    className: "bg-muted text-muted-foreground",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${config.className}`}
    >
      {config.label}
    </span>
  );
}

// ── Confidence indicator ─────────────────────────────────────────────────────

import { confidenceLabelText, confidenceBadgeClasses } from "@/lib/confidence";

function ConfidenceLabel({ confidence }: { confidence: number }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset ${confidenceBadgeClasses(confidence)}`}
    >
      {confidenceLabelText(confidence)}
    </span>
  );
}

// ── Main card ────────────────────────────────────────────────────────────────

function ClassificationCardInner({ c }: { c: Classification }) {
  const [expanded, setExpanded] = useState(false);
  const approve = useApproveClassification();
  const reject = useRejectClassification();
  const execute = useExecuteClassification();

  const handleApprove = async () => {
    try {
      await approve.mutateAsync({ id: c.id });
      toast.success("Classificatie goedgekeurd");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Goedkeuren mislukt");
    }
  };

  const handleReject = async () => {
    try {
      await reject.mutateAsync({ id: c.id });
      toast.success("Classificatie afgewezen");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Afwijzen mislukt");
    }
  };

  const handleExecute = async () => {
    try {
      await execute.mutateAsync({ id: c.id });
      toast.success("Actie uitgevoerd");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Uitvoeren mislukt");
    }
  };

  const isPending = c.status === "pending";
  const isApproved = c.status === "approved";
  const isActing =
    approve.isPending || reject.isPending || execute.isPending;

  return (
    <div className="rounded-lg border border-border bg-muted/30 p-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Bot className="h-3.5 w-3.5 shrink-0 text-primary" />
          <span className="text-xs font-semibold text-foreground truncate">
            {c.category_label}
          </span>
          <ConfidenceLabel confidence={c.confidence} />
        </div>
        <StatusBadge status={c.status} />
      </div>

      {/* Suggested action */}
      <div className="mt-2 flex items-center gap-1.5">
        <span className="text-[10px] font-medium text-muted-foreground">
          Suggestie:
        </span>
        <span className="text-xs text-foreground">
          {c.suggested_action_label}
        </span>
        {c.suggested_template_name && (
          <span className="text-[10px] text-muted-foreground">
            ({c.suggested_template_name})
          </span>
        )}
        {c.suggested_reminder_days && (
          <span className="text-[10px] text-muted-foreground">
            &middot; herinnering over {c.suggested_reminder_days} dagen
          </span>
        )}
      </div>

      {/* Expandable reasoning */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="mt-1.5 flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
      >
        {expanded ? (
          <ChevronUp className="h-3 w-3" />
        ) : (
          <ChevronDown className="h-3 w-3" />
        )}
        {expanded ? "Verberg redenering" : "Toon redenering"}
      </button>

      {expanded && (
        <p className="mt-1 rounded-md bg-muted/50 px-2 py-1.5 text-[11px] text-muted-foreground leading-relaxed">
          {c.reasoning}
        </p>
      )}

      {/* Review info */}
      {c.reviewed_by_name && (
        <p className="mt-1.5 text-[10px] text-muted-foreground">
          {c.status === "approved" ? "Goedgekeurd" : "Afgewezen"} door{" "}
          {c.reviewed_by_name}
          {c.review_note && ` — "${c.review_note}"`}
        </p>
      )}

      {/* Execution result */}
      {c.execution_result && (
        <p className="mt-1 text-[10px] text-muted-foreground">
          Resultaat: {c.execution_result}
        </p>
      )}

      {/* Action buttons */}
      {(isPending || isApproved) && (
        <div className="mt-2.5 flex items-center gap-1.5">
          {isPending && (
            <>
              <button
                type="button"
                onClick={handleApprove}
                disabled={isActing}
                className="inline-flex items-center gap-1 rounded-md bg-emerald-600 px-2.5 py-1 text-[11px] font-medium text-white hover:bg-emerald-700 transition-colors disabled:opacity-50"
              >
                {approve.isPending ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Check className="h-3 w-3" />
                )}
                Akkoord
              </button>
              <button
                type="button"
                onClick={handleReject}
                disabled={isActing}
                className="inline-flex items-center gap-1 rounded-md border border-border bg-background px-2.5 py-1 text-[11px] font-medium text-muted-foreground hover:bg-muted/50 transition-colors disabled:opacity-50"
              >
                {reject.isPending ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <X className="h-3 w-3" />
                )}
                Afwijzen
              </button>
            </>
          )}
          {isApproved && (
            <button
              type="button"
              onClick={handleExecute}
              disabled={isActing}
              className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1 text-[11px] font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {execute.isPending ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Play className="h-3 w-3" />
              )}
              Uitvoeren
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ── Public component ─────────────────────────────────────────────────────────

/**
 * Shows the AI classification for a synced email.
 * Fetches classification data by email ID.
 * If no classification exists, shows a "classify" trigger button.
 */
export function ClassificationCard({ syncedEmailId }: { syncedEmailId: string }) {
  const { data: classification, isLoading } = useEmailClassification(syncedEmailId);
  const classifyEmail = useClassifyEmail();

  const handleClassify = async () => {
    try {
      await classifyEmail.mutateAsync({ emailId: syncedEmailId });
      toast.success("E-mail geclassificeerd");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Classificatie mislukt");
    }
  };

  if (isLoading) {
    return (
      <div className="rounded-lg border border-border bg-muted/30 p-3">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Loader2 className="h-3 w-3 animate-spin" />
          Classificatie laden...
        </div>
      </div>
    );
  }

  if (!classification) {
    return (
      <div className="rounded-lg border border-dashed border-border bg-muted/20 p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">
              Geen AI-classificatie
            </span>
          </div>
          <button
            type="button"
            onClick={handleClassify}
            disabled={classifyEmail.isPending}
            className="inline-flex items-center gap-1 rounded-md border border-border bg-background px-2 py-1 text-[11px] font-medium text-foreground hover:bg-muted/50 transition-colors disabled:opacity-50"
          >
            {classifyEmail.isPending ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Bot className="h-3 w-3" />
            )}
            Classificeer
          </button>
        </div>
      </div>
    );
  }

  return <ClassificationCardInner c={classification} />;
}
