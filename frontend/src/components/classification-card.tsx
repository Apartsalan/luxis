"use client";

import { useCallback, useState } from "react";
import {
  Bot,
  CalendarClock,
  Check,
  ChevronDown,
  ChevronUp,
  Copy,
  Loader2,
  MessageSquareReply,
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
  useSmartReplies,
  type Classification,
  type SmartReply,
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

// ── Sentiment badge ─────────────────────────────────────────────────────────

const SENTIMENT_CONFIG: Record<string, { label: string; className: string }> = {
  positief: {
    label: "Positief",
    className: "bg-emerald-500/10 text-emerald-600",
  },
  neutraal: {
    label: "Neutraal",
    className: "bg-slate-500/10 text-slate-600",
  },
  negatief: {
    label: "Negatief",
    className: "bg-red-500/10 text-red-600",
  },
  dreigend: {
    label: "Dreigend",
    className: "bg-red-600/15 text-red-700",
  },
};

function SentimentBadge({ sentiment }: { sentiment: string }) {
  const config = SENTIMENT_CONFIG[sentiment] ?? {
    label: sentiment,
    className: "bg-muted text-muted-foreground",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${config.className}`}
    >
      {config.label}
    </span>
  );
}

// ── Tone labels ─────────────────────────────────────────────────────────────

const TONE_CONFIG: Record<string, { label: string; emoji: string; className: string }> = {
  mild: {
    label: "Mild",
    emoji: "🤝",
    className: "border-emerald-200 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-950",
  },
  zakelijk: {
    label: "Zakelijk",
    emoji: "📋",
    className: "border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950",
  },
  streng: {
    label: "Streng",
    emoji: "⚖️",
    className: "border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950",
  },
};

// ── Smart Reply Card ────────────────────────────────────────────────────────

function SmartReplyCard({ reply }: { reply: SmartReply }) {
  const [expanded, setExpanded] = useState(false);
  const config = TONE_CONFIG[reply.tone] ?? {
    label: reply.tone,
    emoji: "💬",
    className: "border-border bg-muted/30",
  };

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(
      `Onderwerp: ${reply.subject}\n\n${reply.body}`
    );
    toast.success("Gekopieerd naar klembord");
  }, [reply]);

  return (
    <div
      className={`rounded-md border p-2.5 ${config.className}`}
    >
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1.5 text-xs font-medium text-foreground"
        >
          <span>{config.emoji}</span>
          <span>{config.label}</span>
          {expanded ? (
            <ChevronUp className="h-3 w-3 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-3 w-3 text-muted-foreground" />
          )}
        </button>
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
          aria-label="Kopieer antwoord"
        >
          <Copy className="h-3 w-3" />
          Kopieer
        </button>
      </div>

      {expanded && (
        <div className="mt-2 space-y-1.5">
          <p className="text-[11px] font-medium text-foreground">
            {reply.subject}
          </p>
          <p className="whitespace-pre-wrap text-[11px] leading-relaxed text-muted-foreground">
            {reply.body}
          </p>
        </div>
      )}
    </div>
  );
}

// ── Main card ────────────────────────────────────────────────────────────────

function ClassificationCardInner({ c }: { c: Classification }) {
  const [expanded, setExpanded] = useState(false);
  const [showReplies, setShowReplies] = useState(false);
  const approve = useApproveClassification();
  const reject = useRejectClassification();
  const execute = useExecuteClassification();
  const smartReplies = useSmartReplies(c.id);

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

  const handleSmartReplies = useCallback(() => {
    setShowReplies(true);
    smartReplies.refetch();
  }, [smartReplies]);

  const isPending = c.status === "pending";
  const isApproved = c.status === "approved";
  const isActing =
    approve.isPending || reject.isPending || execute.isPending;

  return (
    <div className="rounded-lg border border-border bg-muted/30 p-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Bot className="h-3.5 w-3.5 shrink-0 text-primary" aria-hidden="true" />
          <span className="text-xs font-semibold text-foreground truncate">
            {c.category_label}
          </span>
          <ConfidenceLabel confidence={c.confidence} />
          {c.sentiment && <SentimentBadge sentiment={c.sentiment} />}
        </div>
        <StatusBadge status={c.status} />
      </div>

      {/* Payment promise (AUDIT-18) */}
      {c.category === "belofte_tot_betaling" &&
        (c.promise_date || c.promise_amount) && (
          <div className="mt-2 flex items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-2.5 py-1.5 dark:border-emerald-800 dark:bg-emerald-950">
            <CalendarClock className="h-3.5 w-3.5 shrink-0 text-emerald-600" aria-hidden="true" />
            <div className="flex items-center gap-3 text-xs">
              {c.promise_date && (
                <span className="text-emerald-700 dark:text-emerald-300">
                  <span className="font-medium">Datum:</span>{" "}
                  {new Date(c.promise_date).toLocaleDateString("nl-NL", {
                    weekday: "short",
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  })}
                </span>
              )}
              {c.promise_amount && (
                <span className="text-emerald-700 dark:text-emerald-300">
                  <span className="font-medium">Bedrag:</span>{" "}
                  {new Intl.NumberFormat("nl-NL", {
                    style: "currency",
                    currency: "EUR",
                  }).format(Number(c.promise_amount))}
                </span>
              )}
            </div>
          </div>
        )}

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

          {/* Smart replies button (AUDIT-25) */}
          <button
            type="button"
            onClick={handleSmartReplies}
            disabled={smartReplies.isFetching}
            className="inline-flex items-center gap-1 rounded-md border border-border bg-background px-2.5 py-1 text-[11px] font-medium text-muted-foreground hover:bg-muted/50 transition-colors disabled:opacity-50"
          >
            {smartReplies.isFetching ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <MessageSquareReply className="h-3 w-3" />
            )}
            Concept-antwoord
          </button>
        </div>
      )}

      {/* Smart replies panel (AUDIT-25) */}
      {showReplies && (
        <div className="mt-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
              Concept-antwoorden
            </span>
            <button
              type="button"
              onClick={() => setShowReplies(false)}
              className="text-[10px] text-muted-foreground hover:text-foreground"
            >
              Verberg
            </button>
          </div>

          {smartReplies.isFetching && (
            <div className="flex items-center gap-2 rounded-md border border-border bg-muted/20 p-3" role="status" aria-label="Antwoorden genereren">
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
              <span className="text-xs text-muted-foreground">
                AI genereert 3 concept-antwoorden...
              </span>
            </div>
          )}

          {smartReplies.data?.map((reply) => (
            <SmartReplyCard key={reply.tone} reply={reply} />
          ))}

          {smartReplies.isError && (
            <p className="text-xs text-red-600">
              Kon geen suggesties genereren. Probeer opnieuw.
            </p>
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
      <div className="rounded-lg border border-border bg-muted/30 p-3" role="status" aria-label="Classificatie laden">
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
            <Bot className="h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
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
