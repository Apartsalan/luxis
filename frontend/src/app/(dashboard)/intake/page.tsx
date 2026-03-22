"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Bot,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  Inbox,
} from "lucide-react";
import { useIntakes } from "@/hooks/use-intake";
import { formatCurrency, formatRelativeTime } from "@/lib/utils";
import { QueryError } from "@/components/query-error";
import { confidenceBgColor, confidenceTextColor as sharedConfidenceTextColor, confidenceLabelText } from "@/lib/confidence";

// ── Status config ────────────────────────────────────────────────────────────

const INTAKE_STATUS_CONFIG: Record<string, { label: string; badge: string }> = {
  detected: {
    label: "Gedetecteerd",
    badge: "bg-slate-50 text-slate-600 ring-slate-500/20",
  },
  processing: {
    label: "Verwerken...",
    badge: "bg-blue-50 text-blue-700 ring-blue-600/20",
  },
  pending_review: {
    label: "Te beoordelen",
    badge: "bg-amber-50 text-amber-700 ring-amber-600/20",
  },
  approved: {
    label: "Goedgekeurd",
    badge: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  },
  rejected: {
    label: "Afgewezen",
    badge: "bg-red-50 text-red-700 ring-red-600/20",
  },
  failed: {
    label: "Fout",
    badge: "bg-red-50 text-red-800 ring-red-700/20",
  },
};

const STATUS_TABS = [
  { value: "pending_review", label: "Te beoordelen" },
  { value: "detected", label: "Gedetecteerd" },
  { value: "processing", label: "Verwerken" },
  { value: "approved", label: "Goedgekeurd" },
  { value: "rejected", label: "Afgewezen" },
  { value: "failed", label: "Fout" },
  { value: "", label: "Alle" },
];

// ── Confidence helpers (use shared lib) ──────────────────────────────────────

const confidenceColor = confidenceBgColor;
const confidenceTextColor = sharedConfidenceTextColor;

// ── Page ─────────────────────────────────────────────────────────────────────

const PER_PAGE = 20;

export default function IntakePage() {
  const [statusFilter, setStatusFilter] = useState("pending_review");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, error, refetch } = useIntakes(
    statusFilter || undefined,
    page,
    PER_PAGE,
  );

  const items = data ?? [];
  const hasNextPage = items.length >= PER_PAGE;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary" />
            AI Intake
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Inkomende incassoverzoeken automatisch verwerkt door AI
          </p>
        </div>
      </div>

      {/* Status tabs */}
      <div className="flex flex-wrap gap-1.5">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => {
              setStatusFilter(tab.value);
              setPage(1);
            }}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              statusFilter === tab.value
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:bg-muted/80"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Error state */}
      {isError && (
        <QueryError
          message={error?.message ?? "Kon intake verzoeken niet laden"}
          onRetry={refetch}
        />
      )}

      {/* Table */}
      <div className="rounded-lg border bg-card">
        {/* Table header */}
        <div className="hidden md:grid grid-cols-[100px_1fr_1fr_140px_100px_90px_80px_40px] gap-2 px-4 py-2.5 border-b text-xs font-medium text-muted-foreground uppercase tracking-wider">
          <div>Ontvangen</div>
          <div>Afzender</div>
          <div>Onderwerp</div>
          <div>Debiteur</div>
          <div>Bedrag</div>
          <div>Vertrouwen</div>
          <div>Status</div>
          <div />
        </div>

        {/* Loading skeleton */}
        {isLoading && (
          <div className="divide-y">
            {[...Array(8)].map((_, i) => (
              <div
                key={i}
                className="grid grid-cols-[100px_1fr_1fr_140px_100px_90px_80px_40px] gap-2 px-4 py-3.5"
              >
                <div className="h-4 w-16 rounded bg-muted animate-pulse" />
                <div className="h-4 w-32 rounded bg-muted animate-pulse" />
                <div className="h-4 w-40 rounded bg-muted animate-pulse" />
                <div className="h-4 w-24 rounded bg-muted animate-pulse" />
                <div className="h-4 w-16 rounded bg-muted animate-pulse" />
                <div className="h-4 w-14 rounded bg-muted animate-pulse" />
                <div className="h-4 w-16 rounded bg-muted animate-pulse" />
                <div className="h-4 w-4 rounded bg-muted animate-pulse" />
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
              Geen intake verzoeken
            </h3>
            <p className="text-sm text-muted-foreground mt-1 max-w-sm">
              {statusFilter === "pending_review"
                ? "Er zijn geen verzoeken die wachten op beoordeling."
                : "Er zijn geen verzoeken met deze status."}
            </p>
          </div>
        )}

        {/* Rows */}
        {!isLoading && items.length > 0 && (
          <div className="divide-y">
            {items.map((item) => {
              const statusCfg =
                INTAKE_STATUS_CONFIG[item.status] ?? INTAKE_STATUS_CONFIG.detected;

              return (
                <Link
                  key={item.id}
                  href={`/intake/${item.id}`}
                  className="grid grid-cols-1 md:grid-cols-[100px_1fr_1fr_140px_100px_90px_80px_40px] gap-1 md:gap-2 px-4 py-3 hover:bg-muted/50 transition-colors group"
                >
                  {/* Ontvangen */}
                  <div className="text-sm text-muted-foreground">
                    {item.email_date
                      ? formatRelativeTime(item.email_date)
                      : "-"}
                  </div>

                  {/* Afzender */}
                  <div className="text-sm text-foreground truncate">
                    {item.email_from || "-"}
                  </div>

                  {/* Onderwerp */}
                  <div className="text-sm text-foreground truncate font-medium">
                    {item.email_subject || "-"}
                  </div>

                  {/* Debiteur */}
                  <div className="hidden md:block text-sm text-foreground truncate">
                    {item.debtor_name || (
                      <span className="text-muted-foreground italic">
                        Onbekend
                      </span>
                    )}
                  </div>

                  {/* Bedrag */}
                  <div className="hidden md:block text-sm text-foreground font-medium tabular-nums">
                    {item.principal_amount
                      ? formatCurrency(item.principal_amount)
                      : "-"}
                  </div>

                  {/* Vertrouwen */}
                  <div className="hidden md:flex items-center gap-1.5">
                    {item.ai_confidence != null ? (
                      <>
                        <div className="h-1.5 w-12 rounded-full bg-muted overflow-hidden">
                          <div
                            className={`h-full rounded-full ${confidenceColor(item.ai_confidence)}`}
                            style={{
                              width: `${Math.round(item.ai_confidence * 100)}%`,
                            }}
                          />
                        </div>
                        <span
                          className={`text-xs font-medium ${confidenceTextColor(item.ai_confidence)}`}
                        >
                          {confidenceLabelText(item.ai_confidence)}
                        </span>
                      </>
                    ) : (
                      <span className="text-xs text-muted-foreground">-</span>
                    )}
                  </div>

                  {/* Status */}
                  <div>
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset ${statusCfg.badge}`}
                    >
                      {statusCfg.label}
                    </span>
                  </div>

                  {/* Arrow */}
                  <div className="hidden md:flex items-center justify-end">
                    <ArrowUpRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {/* Pagination */}
      {!isLoading && items.length > 0 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Pagina {page}</span>
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
              disabled={!hasNextPage}
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
