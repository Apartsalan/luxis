"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Zap,
  Inbox,
  ChevronLeft,
  ChevronRight,
  ArrowUpRight,
  Check,
  X,
  Play,
  AlertTriangle,
  Clock,
} from "lucide-react";
import {
  useFollowupRecommendations,
  useFollowupStats,
  useApproveAndExecuteFollowup,
  useRejectFollowup,
} from "@/hooks/use-followup";
import { formatCurrency } from "@/lib/utils";
import { QueryError } from "@/components/query-error";
import { toast } from "sonner";

// ── Status config ────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<string, { label: string; badge: string }> = {
  pending: {
    label: "Openstaand",
    badge: "bg-amber-50 text-amber-700 ring-amber-600/20",
  },
  approved: {
    label: "Goedgekeurd",
    badge: "bg-blue-50 text-blue-700 ring-blue-600/20",
  },
  executed: {
    label: "Uitgevoerd",
    badge: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  },
  rejected: {
    label: "Afgewezen",
    badge: "bg-slate-50 text-slate-600 ring-slate-500/20",
  },
};

const URGENCY_CONFIG: Record<string, { label: string; badge: string; icon: typeof Clock }> = {
  normal: {
    label: "Klaar",
    badge: "bg-amber-50 text-amber-700 ring-amber-600/20",
    icon: Clock,
  },
  overdue: {
    label: "Te laat",
    badge: "bg-red-50 text-red-700 ring-red-600/20",
    icon: AlertTriangle,
  },
};

const STATUS_TABS = [
  { value: "pending", label: "Openstaand" },
  { value: "approved", label: "Goedgekeurd" },
  { value: "executed", label: "Uitgevoerd" },
  { value: "rejected", label: "Afgewezen" },
  { value: "", label: "Alle" },
];

const ACTION_LABELS: Record<string, string> = {
  generate_document: "Document genereren",
  send_reminder: "Herinnering sturen",
  escalate: "Handmatige review",
  advance_step: "Volgende stap",
};

// ── Page ─────────────────────────────────────────────────────────────────────

const PER_PAGE = 20;

export default function FollowupPage() {
  const [statusFilter, setStatusFilter] = useState("pending");
  const [page, setPage] = useState(1);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectNote, setRejectNote] = useState("");

  const { data, isLoading, isError, error, refetch } = useFollowupRecommendations(
    statusFilter || undefined,
    page,
    PER_PAGE,
  );
  const { data: stats } = useFollowupStats();
  const approveAndExecute = useApproveAndExecuteFollowup();
  const reject = useRejectFollowup();

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / PER_PAGE);

  function handleApproveAndExecute(id: string, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    approveAndExecute.mutate(
      { id },
      {
        onSuccess: () => {
          toast.success("Aanbeveling goedgekeurd en uitgevoerd");
        },
        onError: (err) => {
          toast.error(err.message || "Goedkeuren en uitvoeren mislukt");
        },
      },
    );
  }

  function handleReject(id: string) {
    reject.mutate(
      { id, note: rejectNote || undefined },
      {
        onSuccess: () => {
          setRejectingId(null);
          setRejectNote("");
          toast.success("Aanbeveling afgewezen");
        },
        onError: (err) => {
          toast.error(err.message || "Afwijzen mislukt");
        },
      },
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            Follow-up Advisor
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Aanbevelingen voor dossiers die actie nodig hebben
          </p>
        </div>
      </div>

      {/* Stats badges */}
      {stats && (
        <div className="flex flex-wrap gap-3">
          {stats.pending > 0 && (
            <div className="flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-600/20">
              <Clock className="h-3 w-3" />
              {stats.pending} openstaand
            </div>
          )}
          {stats.approved > 0 && (
            <div className="flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-600/20">
              <Check className="h-3 w-3" />
              {stats.approved} goedgekeurd
            </div>
          )}
          {stats.executed > 0 && (
            <div className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
              <Play className="h-3 w-3" />
              {stats.executed} uitgevoerd
            </div>
          )}
        </div>
      )}

      {/* Status tabs */}
      <div className="flex flex-wrap gap-1.5">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => {
              setStatusFilter(tab.value);
              setPage(1);
              setExpandedId(null);
            }}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              statusFilter === tab.value
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:bg-muted/80"
            }`}
          >
            {tab.label}
            {tab.value === "pending" && stats && stats.pending > 0 && (
              <span className="ml-1">({stats.pending})</span>
            )}
          </button>
        ))}
      </div>

      {/* Error state */}
      {isError && (
        <QueryError
          message={error?.message ?? "Kon aanbevelingen niet laden"}
          onRetry={refetch}
        />
      )}

      {/* Table */}
      <div className="rounded-lg border bg-card">
        {/* Table header */}
        <div className="hidden md:grid grid-cols-[1fr_160px_160px_80px_90px_100px_80px_120px] gap-2 px-4 py-2.5 border-b text-xs font-medium text-muted-foreground uppercase tracking-wider">
          <div>Dossier</div>
          <div>Stap</div>
          <div>Actie</div>
          <div>Dagen</div>
          <div>Bedrag</div>
          <div>Urgentie</div>
          <div>Status</div>
          <div />
        </div>

        {/* Loading skeleton */}
        {isLoading && (
          <div className="divide-y">
            {[...Array(8)].map((_, i) => (
              <div
                key={i}
                className="grid grid-cols-[1fr_160px_160px_80px_90px_100px_80px_120px] gap-2 px-4 py-3.5"
              >
                <div className="h-4 w-32 rounded bg-muted animate-pulse" />
                <div className="h-4 w-24 rounded bg-muted animate-pulse" />
                <div className="h-4 w-28 rounded bg-muted animate-pulse" />
                <div className="h-4 w-10 rounded bg-muted animate-pulse" />
                <div className="h-4 w-16 rounded bg-muted animate-pulse" />
                <div className="h-4 w-14 rounded bg-muted animate-pulse" />
                <div className="h-4 w-16 rounded bg-muted animate-pulse" />
                <div className="h-4 w-20 rounded bg-muted animate-pulse" />
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !isError && items.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted mb-3">
              <Inbox className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="text-sm font-medium text-foreground">
              Geen aanbevelingen
            </h3>
            <p className="text-sm text-muted-foreground mt-1 max-w-md">
              {statusFilter === "pending"
                ? "Er zijn geen openstaande aanbevelingen. Alle dossiers zijn up-to-date."
                : "Er zijn geen aanbevelingen met deze status."}
            </p>
            {statusFilter === "pending" && (
              <p className="text-xs text-muted-foreground/70 mt-3 max-w-md">
                Follow-up analyseert automatisch je incassodossiers en stelt acties voor
                zoals herinneringen versturen, rente herberekenen of de volgende stap zetten.
              </p>
            )}
          </div>
        )}

        {/* Rows */}
        {!isLoading && items.length > 0 && (
          <div className="divide-y">
            {items.map((item) => {
              const statusCfg = STATUS_CONFIG[item.status] ?? STATUS_CONFIG.pending;
              const urgencyCfg = URGENCY_CONFIG[item.urgency] ?? URGENCY_CONFIG.normal;
              const isExpanded = expandedId === item.id;
              const isRejecting = rejectingId === item.id;

              return (
                <div key={item.id}>
                  {/* Main row */}
                  <div
                    onClick={() => setExpandedId(isExpanded ? null : item.id)}
                    className="grid grid-cols-1 md:grid-cols-[1fr_160px_160px_80px_90px_100px_80px_120px] gap-1 md:gap-2 px-4 py-3 hover:bg-muted/50 transition-colors cursor-pointer group"
                  >
                    {/* Dossier */}
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-foreground">
                        {item.case_number}
                      </span>
                      <span className="text-xs text-muted-foreground truncate">
                        {item.opposing_party_name ?? item.client_name ?? ""}
                      </span>
                    </div>

                    {/* Stap */}
                    <div className="hidden md:block text-sm text-foreground truncate">
                      {item.step_name}
                    </div>

                    {/* Actie */}
                    <div className="hidden md:block text-sm text-foreground">
                      {item.action_label || ACTION_LABELS[item.recommended_action] || item.recommended_action}
                    </div>

                    {/* Dagen */}
                    <div className="hidden md:block text-sm text-foreground tabular-nums">
                      {item.days_in_step}d
                    </div>

                    {/* Bedrag */}
                    <div className="hidden md:block text-sm text-foreground font-medium tabular-nums">
                      {formatCurrency(item.outstanding_amount)}
                    </div>

                    {/* Urgentie */}
                    <div className="hidden md:block">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset ${urgencyCfg.badge}`}
                      >
                        <urgencyCfg.icon className="h-3 w-3" />
                        {item.urgency_label || urgencyCfg.label}
                      </span>
                    </div>

                    {/* Status */}
                    <div className="hidden md:block">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset ${statusCfg.badge}`}
                      >
                        {statusCfg.label}
                      </span>
                    </div>

                    {/* Actions */}
                    <div className="hidden md:flex items-center justify-end gap-1">
                      {item.status === "pending" && (
                        <>
                          <button
                            onClick={(e) => handleApproveAndExecute(item.id, e)}
                            disabled={approveAndExecute.isPending}
                            className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                            title="Goedkeuren & Uitvoeren"
                          >
                            <Check className="h-3 w-3" />
                            Uitvoeren
                          </button>
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              setRejectingId(isRejecting ? null : item.id);
                              setRejectNote("");
                            }}
                            className="inline-flex items-center rounded-md border px-2 py-1 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
                            title="Afwijzen"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </>
                      )}
                      {item.status !== "pending" && (
                        <Link
                          href={`/zaken/${item.case_id}`}
                          onClick={(e) => e.stopPropagation()}
                          className="text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <ArrowUpRight className="h-4 w-4" />
                        </Link>
                      )}
                    </div>
                  </div>

                  {/* Reject input */}
                  {isRejecting && (
                    <div
                      className="px-4 pb-3 flex items-center gap-2"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        type="text"
                        value={rejectNote}
                        onChange={(e) => setRejectNote(e.target.value)}
                        placeholder="Reden (optioneel)..."
                        className="flex-1 rounded-md border px-3 py-1.5 text-sm bg-background focus:outline-none focus:ring-1 focus:ring-primary"
                        autoFocus
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleReject(item.id);
                          if (e.key === "Escape") {
                            setRejectingId(null);
                            setRejectNote("");
                          }
                        }}
                      />
                      <button
                        onClick={() => handleReject(item.id)}
                        disabled={reject.isPending}
                        className="rounded-md bg-destructive px-3 py-1.5 text-xs font-medium text-destructive-foreground hover:bg-destructive/90 disabled:opacity-50"
                      >
                        Afwijzen
                      </button>
                      <button
                        onClick={() => {
                          setRejectingId(null);
                          setRejectNote("");
                        }}
                        className="rounded-md border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted"
                      >
                        Annuleren
                      </button>
                    </div>
                  )}

                  {/* Expanded detail */}
                  {isExpanded && (
                    <div
                      className="px-4 pb-4 bg-muted/30 border-t border-dashed"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3">
                        <div>
                          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1.5">
                            Reden
                          </h4>
                          <p className="text-sm text-foreground">
                            {item.reasoning}
                          </p>
                        </div>
                        <div className="space-y-2">
                          <div>
                            <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                              Dossier
                            </h4>
                            <Link
                              href={`/zaken/${item.case_id}`}
                              className="text-sm text-primary hover:underline inline-flex items-center gap-1"
                            >
                              {item.case_number}
                              {item.opposing_party_name && ` — ${item.opposing_party_name}`}
                              <ArrowUpRight className="h-3 w-3" />
                            </Link>
                          </div>
                          {item.review_note && (
                            <div>
                              <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                                Notitie
                              </h4>
                              <p className="text-sm text-foreground">
                                {item.review_note}
                              </p>
                            </div>
                          )}
                          {item.executed_at && (
                            <div>
                              <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                                Uitgevoerd op
                              </h4>
                              <p className="text-sm text-foreground">
                                {new Date(item.executed_at).toLocaleString("nl-NL")}
                              </p>
                            </div>
                          )}

                          {/* Mobile actions */}
                          {item.status === "pending" && (
                            <div className="flex items-center gap-2 pt-2 md:hidden">
                              <button
                                onClick={(e) => handleApproveAndExecute(item.id, e)}
                                disabled={approveAndExecute.isPending}
                                className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                              >
                                <Check className="h-3 w-3" />
                                Goedkeuren & Uitvoeren
                              </button>
                              <button
                                onClick={(e) => {
                                  e.preventDefault();
                                  setRejectingId(isRejecting ? null : item.id);
                                  setRejectNote("");
                                }}
                                className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted"
                              >
                                <X className="h-3 w-3" />
                                Afwijzen
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Pagination */}
      {!isLoading && total > 0 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            {total} resultaten — pagina {page} van {totalPages || 1}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:opacity-50 disabled:pointer-events-none"
            >
              <ChevronLeft className="h-4 w-4" />
              Vorige
            </button>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= totalPages}
              className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:opacity-50 disabled:pointer-events-none"
            >
              Volgende
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
