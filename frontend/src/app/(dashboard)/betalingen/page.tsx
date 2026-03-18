"use client";

import { useState, useCallback, useRef } from "react";
import Link from "next/link";
import {
  Banknote,
  Upload,
  Inbox,
  ChevronLeft,
  ChevronRight,
  ArrowUpRight,
  Check,
  X,
  Clock,
  Play,
  RefreshCw,
  FileSpreadsheet,
  AlertTriangle,
  CheckCircle2,
  Zap,
} from "lucide-react";
import {
  useImports,
  useUploadCSV,
  useRematchImport,
  usePaymentMatches,
  usePaymentMatchStats,
  useApproveAndExecuteMatch,
  useRejectMatch,
  useApproveAllMatches,
} from "@/hooks/use-payment-matching";
import { formatCurrency } from "@/lib/utils";
import { QueryError } from "@/components/query-error";
import { toast } from "sonner";

// ── Config ───────────────────────────────────────────────────────────────────

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

const MATCH_STATUS_TABS = [
  { value: "pending", label: "Openstaand" },
  { value: "approved", label: "Goedgekeurd" },
  { value: "executed", label: "Uitgevoerd" },
  { value: "rejected", label: "Afgewezen" },
  { value: "", label: "Alle" },
];

function confidenceBadge(confidence: number) {
  if (confidence >= 90)
    return "bg-emerald-50 text-emerald-700 ring-emerald-600/20";
  if (confidence >= 70)
    return "bg-amber-50 text-amber-700 ring-amber-600/20";
  return "bg-red-50 text-red-700 ring-red-600/20";
}

const PER_PAGE = 20;

// ── Main tabs ────────────────────────────────────────────────────────────────

type MainTab = "upload" | "matches";

// ── Page ─────────────────────────────────────────────────────────────────────

export default function BetalingenPage() {
  const [mainTab, setMainTab] = useState<MainTab>("matches");
  const uploadFileRef = useRef<HTMLInputElement>(null);
  const upload = useUploadCSV();

  const handleQuickUpload = useCallback(
    (file: File) => {
      if (!file.name.endsWith(".csv")) {
        toast.error("Alleen CSV-bestanden worden ondersteund");
        return;
      }
      upload.mutate(file, {
        onSuccess: (result) => {
          toast.success(
            `${result.credit_count} inkomende transacties geïmporteerd, ${result.matched_count} gematcht`,
          );
          setMainTab("matches");
        },
        onError: (err) => {
          toast.error(err.message || "Upload mislukt");
        },
      });
    },
    [upload],
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground flex items-center gap-2">
            <Banknote className="h-5 w-5 text-primary" />
            Betalingen
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Bankafschriften importeren en betalingen automatisch matchen aan
            dossiers
          </p>
        </div>
        <div>
          <input
            ref={uploadFileRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleQuickUpload(file);
              e.target.value = "";
            }}
          />
          <button
            onClick={() => uploadFileRef.current?.click()}
            disabled={upload.isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors shadow-sm"
          >
            <Upload className="h-4 w-4" />
            {upload.isPending ? "Importeren..." : "CSV uploaden"}
          </button>
        </div>
      </div>

      {/* Main tabs */}
      <div className="flex gap-1.5">
        <button
          onClick={() => setMainTab("matches")}
          className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
            mainTab === "matches"
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          }`}
        >
          Matches
        </button>
        <button
          onClick={() => setMainTab("upload")}
          className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
            mainTab === "upload"
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          }`}
        >
          Importgeschiedenis
        </button>
      </div>

      {mainTab === "upload" ? <UploadSection /> : <MatchSection />}
    </div>
  );
}

// ── Upload Section ───────────────────────────────────────────────────────────

function UploadSection() {
  const [importPage, setImportPage] = useState(1);
  const { data: imports, isLoading, isError, error, refetch } = useImports(importPage);
  const upload = useUploadCSV();
  const rematch = useRematchImport();

  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      if (!file.name.endsWith(".csv")) {
        toast.error("Alleen CSV-bestanden worden ondersteund");
        return;
      }
      upload.mutate(file, {
        onSuccess: (result) => {
          toast.success(
            `${result.credit_count} inkomende transacties geïmporteerd, ${result.matched_count} gematcht`,
          );
        },
        onError: (err) => {
          toast.error(err.message || "Upload mislukt");
        },
      });
    },
    [upload],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const items = imports?.items ?? [];
  const total = imports?.total ?? 0;
  const totalPages = Math.ceil(total / PER_PAGE);

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed py-12 transition-colors cursor-pointer ${
          dragOver
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/30"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
            e.target.value = "";
          }}
        />
        {upload.isPending ? (
          <>
            <RefreshCw className="h-8 w-8 text-primary animate-spin mb-2" />
            <p className="text-sm font-medium text-foreground">
              Bezig met importeren...
            </p>
          </>
        ) : (
          <>
            <Upload className="h-8 w-8 text-muted-foreground mb-2" />
            <p className="text-sm font-medium text-foreground">
              Sleep een CSV-bestand hierheen
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              of klik om te bladeren — Rabobank CSV-formaat
            </p>
          </>
        )}
      </div>

      {/* Error state */}
      {isError && (
        <QueryError
          message={error?.message ?? "Kon imports niet laden"}
          onRetry={refetch}
        />
      )}

      {/* Import history */}
      <div className="rounded-lg border bg-card">
        <div className="px-4 py-3 border-b">
          <h2 className="text-sm font-medium text-foreground">
            Import geschiedenis
          </h2>
        </div>

        {/* Table header */}
        <div className="hidden md:grid grid-cols-[1fr_100px_80px_80px_80px_100px_120px] gap-2 px-4 py-2.5 border-b text-xs font-medium text-muted-foreground uppercase tracking-wider">
          <div>Bestand</div>
          <div>Bank</div>
          <div>Inkomend</div>
          <div>Gematcht</div>
          <div>Status</div>
          <div>Datum</div>
          <div />
        </div>

        {/* Loading skeleton */}
        {isLoading && (
          <div className="divide-y">
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                className="grid grid-cols-[1fr_100px_80px_80px_80px_100px_120px] gap-2 px-4 py-3.5"
              >
                <div className="h-4 w-40 rounded bg-muted animate-pulse" />
                <div className="h-4 w-16 rounded bg-muted animate-pulse" />
                <div className="h-4 w-10 rounded bg-muted animate-pulse" />
                <div className="h-4 w-10 rounded bg-muted animate-pulse" />
                <div className="h-4 w-14 rounded bg-muted animate-pulse" />
                <div className="h-4 w-20 rounded bg-muted animate-pulse" />
                <div className="h-4 w-16 rounded bg-muted animate-pulse" />
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !isError && items.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted mb-3">
              <FileSpreadsheet className="h-6 w-6 text-muted-foreground" />
            </div>
            <h3 className="text-sm font-medium text-foreground">
              Geen imports
            </h3>
            <p className="text-sm text-muted-foreground mt-1 max-w-sm">
              Upload een bankafschrift CSV-bestand om te beginnen.
            </p>
          </div>
        )}

        {/* Rows */}
        {!isLoading && items.length > 0 && (
          <div className="divide-y">
            {items.map((imp) => (
              <div
                key={imp.id}
                className="grid grid-cols-1 md:grid-cols-[1fr_100px_80px_80px_80px_100px_120px] gap-1 md:gap-2 px-4 py-3 hover:bg-muted/50 transition-colors"
              >
                {/* Filename */}
                <div className="flex items-center gap-2">
                  <FileSpreadsheet className="h-4 w-4 text-muted-foreground shrink-0" />
                  <span className="text-sm font-medium text-foreground truncate">
                    {imp.filename}
                  </span>
                </div>

                {/* Bank */}
                <div className="hidden md:block text-sm text-foreground capitalize">
                  {imp.bank}
                </div>

                {/* Credit count */}
                <div className="hidden md:block text-sm text-foreground tabular-nums">
                  {imp.credit_count}
                </div>

                {/* Matched */}
                <div className="hidden md:block text-sm text-foreground tabular-nums">
                  {imp.matched_count}
                </div>

                {/* Status */}
                <div className="hidden md:block">
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset ${
                      imp.status === "completed"
                        ? "bg-emerald-50 text-emerald-700 ring-emerald-600/20"
                        : imp.status === "error"
                          ? "bg-red-50 text-red-700 ring-red-600/20"
                          : "bg-amber-50 text-amber-700 ring-amber-600/20"
                    }`}
                  >
                    {imp.status === "completed" ? (
                      <CheckCircle2 className="h-3 w-3" />
                    ) : imp.status === "error" ? (
                      <AlertTriangle className="h-3 w-3" />
                    ) : (
                      <Clock className="h-3 w-3" />
                    )}
                    {imp.status === "completed"
                      ? "Klaar"
                      : imp.status === "error"
                        ? "Fout"
                        : imp.status}
                  </span>
                </div>

                {/* Date */}
                <div className="hidden md:block text-sm text-muted-foreground tabular-nums">
                  {new Date(imp.created_at).toLocaleDateString("nl-NL")}
                </div>

                {/* Actions */}
                <div className="hidden md:flex items-center justify-end gap-1">
                  {imp.credit_count > imp.matched_count && (
                    <button
                      onClick={() =>
                        rematch.mutate(imp.id, {
                          onSuccess: (r) =>
                            toast.success(
                              `${r.matched} nieuwe matches gevonden`,
                            ),
                          onError: (err) =>
                            toast.error(err.message || "Rematch mislukt"),
                        })
                      }
                      disabled={rematch.isPending}
                      className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
                      title="Opnieuw matchen"
                    >
                      <RefreshCw className="h-3 w-3" />
                      Rematch
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {!isLoading && total > PER_PAGE && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            {total} imports — pagina {importPage} van {totalPages || 1}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setImportPage((p) => Math.max(1, p - 1))}
              disabled={importPage <= 1}
              className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:opacity-50 disabled:pointer-events-none"
            >
              <ChevronLeft className="h-4 w-4" />
              Vorige
            </button>
            <button
              onClick={() => setImportPage((p) => p + 1)}
              disabled={importPage >= totalPages}
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

// ── Match Section ────────────────────────────────────────────────────────────

function MatchSection() {
  const [statusFilter, setStatusFilter] = useState("pending");
  const [page, setPage] = useState(1);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectNote, setRejectNote] = useState("");

  const { data, isLoading, isError, error, refetch } = usePaymentMatches(
    statusFilter || undefined,
    page,
    PER_PAGE,
  );
  const { data: stats } = usePaymentMatchStats();
  const approveAndExecute = useApproveAndExecuteMatch();
  const reject = useRejectMatch();
  const approveAll = useApproveAllMatches();

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
          toast.success("Betaling goedgekeurd en verwerkt");
        },
        onError: (err) => {
          toast.error(err.message || "Goedkeuren mislukt");
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
          toast.success("Match afgewezen");
        },
        onError: (err) => {
          toast.error(err.message || "Afwijzen mislukt");
        },
      },
    );
  }

  function handleApproveAll() {
    approveAll.mutate(
      { minConfidence: 85 },
      {
        onSuccess: (r) => {
          toast.success(`${r.executed} matches goedgekeurd en verwerkt`);
        },
        onError: (err) => {
          toast.error(err.message || "Bulk goedkeuren mislukt");
        },
      },
    );
  }

  return (
    <div className="space-y-4">
      {/* Stats badges */}
      {stats && (
        <div className="flex flex-wrap gap-3">
          {stats.pending > 0 && (
            <div className="flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-600/20">
              <Clock className="h-3 w-3" />
              {stats.pending} openstaand
            </div>
          )}
          {stats.executed > 0 && (
            <div className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
              <Play className="h-3 w-3" />
              {stats.executed} verwerkt
            </div>
          )}
          {Number(stats.total_amount_pending) > 0 && (
            <div className="flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-600/20">
              <Banknote className="h-3 w-3" />
              {formatCurrency(stats.total_amount_pending)} openstaand
            </div>
          )}
        </div>
      )}

      {/* Status tabs + bulk action */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-1.5">
          {MATCH_STATUS_TABS.map((tab) => (
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

        {/* Bulk approve */}
        {statusFilter === "pending" && stats && stats.pending > 0 && (
          <button
            onClick={handleApproveAll}
            disabled={approveAll.isPending}
            className="inline-flex items-center gap-1.5 rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50 transition-colors"
          >
            <Zap className="h-3 w-3" />
            {approveAll.isPending
              ? "Bezig..."
              : `Alles goedkeuren (≥85%)`}
          </button>
        )}
      </div>

      {/* Error state */}
      {isError && (
        <QueryError
          message={error?.message ?? "Kon matches niet laden"}
          onRetry={refetch}
        />
      )}

      {/* Match table */}
      <div className="rounded-lg border bg-card">
        {/* Table header */}
        <div className="hidden md:grid grid-cols-[120px_1fr_120px_90px_100px_80px_80px_130px] gap-2 px-4 py-2.5 border-b text-xs font-medium text-muted-foreground uppercase tracking-wider">
          <div>Datum</div>
          <div>Tegenpartij</div>
          <div>Bedrag</div>
          <div>Dossier</div>
          <div>Methode</div>
          <div>Score</div>
          <div>Status</div>
          <div />
        </div>

        {/* Loading skeleton */}
        {isLoading && (
          <div className="divide-y">
            {[...Array(8)].map((_, i) => (
              <div
                key={i}
                className="grid grid-cols-[120px_1fr_120px_90px_100px_80px_80px_130px] gap-2 px-4 py-3.5"
              >
                <div className="h-4 w-20 rounded bg-muted animate-pulse" />
                <div className="h-4 w-32 rounded bg-muted animate-pulse" />
                <div className="h-4 w-16 rounded bg-muted animate-pulse" />
                <div className="h-4 w-20 rounded bg-muted animate-pulse" />
                <div className="h-4 w-16 rounded bg-muted animate-pulse" />
                <div className="h-4 w-10 rounded bg-muted animate-pulse" />
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
              Geen matches
            </h3>
            <p className="text-sm text-muted-foreground mt-1 max-w-sm">
              {statusFilter === "pending"
                ? "Er zijn geen openstaande matches. Upload een bankafschrift om te beginnen."
                : "Er zijn geen matches met deze status."}
            </p>
          </div>
        )}

        {/* Rows */}
        {!isLoading && items.length > 0 && (
          <div className="divide-y">
            {items.map((match) => {
              const statusCfg =
                STATUS_CONFIG[match.status] ?? STATUS_CONFIG.pending;
              const isExpanded = expandedId === match.id;
              const isRejecting = rejectingId === match.id;

              return (
                <div key={match.id}>
                  {/* Main row */}
                  <div
                    onClick={() =>
                      setExpandedId(isExpanded ? null : match.id)
                    }
                    className="grid grid-cols-1 md:grid-cols-[120px_1fr_120px_90px_100px_80px_80px_130px] gap-1 md:gap-2 px-4 py-3 hover:bg-muted/50 transition-colors cursor-pointer group"
                  >
                    {/* Date */}
                    <div className="text-sm text-foreground tabular-nums">
                      {new Date(match.transaction_date).toLocaleDateString(
                        "nl-NL",
                      )}
                    </div>

                    {/* Counterparty */}
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-foreground truncate">
                        {match.counterparty_name ?? "Onbekend"}
                      </span>
                      <span className="text-xs text-muted-foreground truncate">
                        {match.description ?? match.counterparty_iban ?? ""}
                      </span>
                    </div>

                    {/* Amount */}
                    <div className="hidden md:block text-sm font-medium text-foreground tabular-nums">
                      {formatCurrency(match.amount)}
                    </div>

                    {/* Case */}
                    <div className="hidden md:block text-sm text-foreground truncate">
                      {match.case_number}
                    </div>

                    {/* Method */}
                    <div className="hidden md:block text-xs text-muted-foreground truncate">
                      {match.match_method_label}
                    </div>

                    {/* Confidence */}
                    <div className="hidden md:block">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ring-inset tabular-nums ${confidenceBadge(match.confidence)}`}
                      >
                        {match.confidence}%
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
                      {match.status === "pending" && (
                        <>
                          <button
                            onClick={(e) =>
                              handleApproveAndExecute(match.id, e)
                            }
                            disabled={approveAndExecute.isPending}
                            className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                            title="Goedkeuren & Verwerken"
                          >
                            <Check className="h-3 w-3" />
                            Verwerken
                          </button>
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              setRejectingId(isRejecting ? null : match.id);
                              setRejectNote("");
                            }}
                            className="inline-flex items-center rounded-md border px-2 py-1 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
                            title="Afwijzen"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </>
                      )}
                      {match.status !== "pending" && (
                        <Link
                          href={`/zaken/${match.case_id}`}
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
                          if (e.key === "Enter") handleReject(match.id);
                          if (e.key === "Escape") {
                            setRejectingId(null);
                            setRejectNote("");
                          }
                        }}
                      />
                      <button
                        onClick={() => handleReject(match.id)}
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
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-3">
                        {/* Transaction details */}
                        <div className="space-y-2">
                          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                            Transactie
                          </h4>
                          <div className="text-sm text-foreground">
                            <p>
                              <span className="text-muted-foreground">
                                Bedrag:{" "}
                              </span>
                              <span className="font-medium">
                                {formatCurrency(match.amount)}
                              </span>
                            </p>
                            <p>
                              <span className="text-muted-foreground">
                                Datum:{" "}
                              </span>
                              {new Date(
                                match.transaction_date,
                              ).toLocaleDateString("nl-NL")}
                            </p>
                            {match.counterparty_iban && (
                              <p>
                                <span className="text-muted-foreground">
                                  IBAN:{" "}
                                </span>
                                <span className="font-mono text-xs">
                                  {match.counterparty_iban}
                                </span>
                              </p>
                            )}
                            {match.description && (
                              <p className="mt-1">
                                <span className="text-muted-foreground">
                                  Omschrijving:{" "}
                                </span>
                                {match.description}
                              </p>
                            )}
                          </div>
                        </div>

                        {/* Match details */}
                        <div className="space-y-2">
                          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                            Match
                          </h4>
                          <div className="text-sm text-foreground">
                            <p>
                              <span className="text-muted-foreground">
                                Methode:{" "}
                              </span>
                              {match.match_method_label}
                            </p>
                            <p>
                              <span className="text-muted-foreground">
                                Zekerheid:{" "}
                              </span>
                              <span
                                className={`font-semibold ${
                                  match.confidence >= 90
                                    ? "text-emerald-600"
                                    : match.confidence >= 70
                                      ? "text-amber-600"
                                      : "text-red-600"
                                }`}
                              >
                                {match.confidence}%
                              </span>
                            </p>
                            {match.match_details && (
                              <p>
                                <span className="text-muted-foreground">
                                  Details:{" "}
                                </span>
                                {match.match_details}
                              </p>
                            )}
                          </div>
                        </div>

                        {/* Case details */}
                        <div className="space-y-2">
                          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                            Dossier
                          </h4>
                          <div className="text-sm text-foreground">
                            <Link
                              href={`/zaken/${match.case_id}`}
                              className="text-primary hover:underline inline-flex items-center gap-1"
                            >
                              {match.case_number}
                              <ArrowUpRight className="h-3 w-3" />
                            </Link>
                            {match.opposing_party_name && (
                              <p className="text-muted-foreground">
                                {match.opposing_party_name}
                              </p>
                            )}
                            {match.client_name && (
                              <p className="text-muted-foreground">
                                Cliënt: {match.client_name}
                              </p>
                            )}
                          </div>

                          {match.review_note && (
                            <div className="mt-2">
                              <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                                Notitie
                              </h4>
                              <p className="text-sm text-foreground">
                                {match.review_note}
                              </p>
                            </div>
                          )}

                          {match.executed_at && (
                            <div className="mt-2">
                              <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                                Verwerkt op
                              </h4>
                              <p className="text-sm text-foreground">
                                {new Date(match.executed_at).toLocaleString(
                                  "nl-NL",
                                )}
                              </p>
                            </div>
                          )}

                          {/* Mobile actions */}
                          {match.status === "pending" && (
                            <div className="flex items-center gap-2 pt-2 md:hidden">
                              <button
                                onClick={(e) =>
                                  handleApproveAndExecute(match.id, e)
                                }
                                disabled={approveAndExecute.isPending}
                                className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                              >
                                <Check className="h-3 w-3" />
                                Goedkeuren & Verwerken
                              </button>
                              <button
                                onClick={(e) => {
                                  e.preventDefault();
                                  setRejectingId(
                                    isRejecting ? null : match.id,
                                  );
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
