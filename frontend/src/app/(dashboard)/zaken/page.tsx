"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Plus,
  Search,
  Briefcase,
  ArrowUpRight,
  Filter,
  MoreHorizontal,
  Eye,
  Pencil,
  Trash2,
  ChevronLeft,
  ChevronRight,
  CheckSquare,
  Square,
  Download,
  ArrowRight,
  X,
  Loader2,
} from "lucide-react";
import { useCases } from "@/hooks/use-cases";
import { useModules } from "@/hooks/use-modules";
import { useWorkflowStatuses } from "@/hooks/use-workflow";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import { QueryError } from "@/components/query-error";
import { api } from "@/lib/api";
import { toast } from "sonner";

const STATUS_LABELS: Record<string, string> = {
  nieuw: "Nieuw",
  "14_dagenbrief": "14-dagenbrief",
  sommatie: "Sommatie",
  dagvaarding: "Dagvaarding",
  vonnis: "Vonnis",
  executie: "Executie",
  betaald: "Betaald",
  afgesloten: "Afgesloten",
};

const STATUS_BADGE: Record<string, string> = {
  nieuw: "bg-blue-50 text-blue-700 ring-blue-600/20",
  "14_dagenbrief": "bg-sky-50 text-sky-700 ring-sky-600/20",
  sommatie: "bg-amber-50 text-amber-700 ring-amber-600/20",
  dagvaarding: "bg-red-50 text-red-700 ring-red-600/20",
  vonnis: "bg-purple-50 text-purple-700 ring-purple-600/20",
  executie: "bg-red-50 text-red-800 ring-red-700/20",
  betaald: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  afgesloten: "bg-slate-50 text-slate-600 ring-slate-500/20",
};

const TYPE_LABELS: Record<string, string> = {
  incasso: "Incasso",
  insolventie: "Insolventie",
  advies: "Advies",
  overig: "Overig",
};

const TYPE_BADGE: Record<string, string> = {
  incasso: "bg-blue-50 text-blue-600",
  insolventie: "bg-purple-50 text-purple-600",
  advies: "bg-teal-50 text-teal-600",
  overig: "bg-slate-50 text-slate-600",
};

export default function ZakenPage() {
  const [search, setSearch] = useState("");
  const [caseType, setCaseType] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkAction, setBulkAction] = useState<"" | "status" | "export">("");
  const [bulkStatus, setBulkStatus] = useState("");
  const [bulkLoading, setBulkLoading] = useState(false);
  const { hasModule } = useModules();
  const { data: workflowStatuses } = useWorkflowStatuses();

  // Build status labels from workflow API, fallback to hardcoded
  const dynamicStatusLabels: Record<string, string> = workflowStatuses
    ? Object.fromEntries(workflowStatuses.map((s) => [s.slug, s.label]))
    : STATUS_LABELS;

  const dynamicStatusBadge: Record<string, string> = workflowStatuses
    ? Object.fromEntries(
        workflowStatuses.map((s) => [
          s.slug,
          STATUS_BADGE[s.slug] ?? "bg-slate-50 text-slate-600 ring-slate-500/20",
        ])
      )
    : STATUS_BADGE;

  const { data, isLoading, isError, error, refetch } = useCases({
    page,
    case_type: caseType || undefined,
    status: status || undefined,
    search: search || undefined,
  });

  const activeFilters = [caseType, status].filter(Boolean).length;
  const allIds = data?.items?.map((z) => z.id) ?? [];
  const allSelected = allIds.length > 0 && allIds.every((id) => selectedIds.has(id));
  const someSelected = selectedIds.size > 0;

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(allIds));
    }
  };

  const handleBulkStatusChange = async () => {
    if (!bulkStatus || selectedIds.size === 0) return;
    setBulkLoading(true);
    try {
      const res = await api("/api/cases/bulk/status", {
        method: "PUT",
        body: JSON.stringify({
          case_ids: Array.from(selectedIds),
          status: bulkStatus,
        }),
      });
      if (!res.ok) throw new Error("Statuswijziging mislukt");
      const result = await res.json();
      toast.success(`${result.updated ?? selectedIds.size} dossiers bijgewerkt`);
      setSelectedIds(new Set());
      setBulkAction("");
      setBulkStatus("");
      refetch();
    } catch (err: any) {
      toast.error(err.message || "Er ging iets mis");
    } finally {
      setBulkLoading(false);
    }
  };

  const handleExport = async () => {
    setBulkLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedIds.size > 0) {
        params.set("ids", Array.from(selectedIds).join(","));
      } else {
        if (caseType) params.set("case_type", caseType);
        if (status) params.set("status", status);
        if (search) params.set("search", search);
      }
      const res = await api(`/api/cases/export?${params.toString()}`);
      if (!res.ok) throw new Error("Export mislukt");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `luxis-dossiers-${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Export gedownload");
      setBulkAction("");
    } catch (err: any) {
      toast.error(err.message || "Export mislukt");
    } finally {
      setBulkLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Dossiers</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {data?.total
              ? `${data.total} ${data.total === 1 ? "dossier" : "dossiers"}`
              : "Beheer je dossiers"}
          </p>
        </div>
        <Link
          href="/zaken/nieuw"
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span className="hidden sm:inline">Nieuw dossier</span>
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Zoek op dossiernummer, beschrijving of client..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full rounded-lg border border-input bg-card pl-10 pr-4 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
          />
        </div>
        <div className="flex gap-2">
          <select
            value={caseType}
            onChange={(e) => {
              setCaseType(e.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-input bg-card px-3 py-2.5 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
          >
            <option value="">Alle types</option>
            <option value="incasso">Incasso</option>
            <option value="insolventie">Insolventie</option>
            <option value="advies">Advies</option>
            <option value="overig">Overig</option>
          </select>
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="rounded-lg border border-input bg-card px-3 py-2.5 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
          >
            <option value="">Alle statussen</option>
            {Object.entries(dynamicStatusLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          {activeFilters > 0 && (
            <button
              onClick={() => {
                setCaseType("");
                setStatus("");
                setSearch("");
                setPage(1);
              }}
              className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-2.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
            >
              Wis filters
            </button>
          )}
        </div>
      </div>

      {/* Bulk action toolbar */}
      {someSelected && (
        <div className="flex items-center gap-3 rounded-lg border border-primary/20 bg-primary/5 px-4 py-3">
          <span className="text-sm font-medium text-primary">
            {selectedIds.size} {selectedIds.size === 1 ? "dossier" : "dossiers"} geselecteerd
          </span>
          <div className="h-4 w-px bg-primary/20" />
          <button
            onClick={() => setBulkAction(bulkAction === "status" ? "" : "status")}
            className="inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium text-primary hover:bg-primary/10 transition-colors"
          >
            <ArrowRight className="h-3.5 w-3.5" />
            Status wijzigen
          </button>
          <button
            onClick={handleExport}
            disabled={bulkLoading}
            className="inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium text-primary hover:bg-primary/10 transition-colors"
          >
            {bulkLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
            Exporteren
          </button>
          <button
            onClick={() => { setSelectedIds(new Set()); setBulkAction(""); }}
            className="ml-auto rounded-md p-1 text-primary/60 hover:text-primary transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Bulk status change inline */}
      {bulkAction === "status" && (
        <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-3">
          <span className="text-sm text-muted-foreground">Nieuwe status:</span>
          <select
            value={bulkStatus}
            onChange={(e) => setBulkStatus(e.target.value)}
            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            <option value="">Kies status...</option>
            {Object.entries(dynamicStatusLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
          <button
            onClick={handleBulkStatusChange}
            disabled={!bulkStatus || bulkLoading}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {bulkLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Toepassen"}
          </button>
          <button
            onClick={() => setBulkAction("")}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Annuleren
          </button>
        </div>
      )}

      {/* Export all (when nothing selected) */}
      {!someSelected && data?.items && data.items.length > 0 && (
        <div className="flex justify-end">
          <button
            onClick={handleExport}
            disabled={bulkLoading}
            className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
          >
            {bulkLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
            Exporteer {data.total} dossiers (CSV)
          </button>
        </div>
      )}

      {/* Table */}
      {isError ? (
        <QueryError
          message={error?.message}
          onRetry={() => refetch()}
        />
      ) : isLoading ? (
        <div className="rounded-xl border border-border bg-card">
          <div className="p-1">
            {[...Array(8)].map((_, i) => (
              <div
                key={i}
                className="flex items-center gap-4 px-4 py-3.5"
              >
                <div className="h-4 w-20 rounded skeleton" />
                <div className="h-5 w-16 rounded-full skeleton" />
                <div className="h-5 w-20 rounded-full skeleton" />
                <div className="hidden md:block h-4 w-32 rounded skeleton" />
                <div className="hidden lg:block h-4 w-24 rounded skeleton" />
                <div className="hidden md:block h-4 w-16 rounded skeleton ml-auto" />
                <div className="h-4 w-16 rounded skeleton" />
              </div>
            ))}
          </div>
        </div>
      ) : data?.items && data.items.length > 0 ? (
        <>
          <div className="overflow-x-auto rounded-xl border border-border bg-card">
            <table className="w-full min-w-[700px]">
              <thead>
                <tr className="border-b border-border">
                  <th className="w-10 px-4 py-3.5">
                    <button onClick={toggleSelectAll} className="text-muted-foreground hover:text-foreground transition-colors">
                      {allSelected ? <CheckSquare className="h-4 w-4 text-primary" /> : <Square className="h-4 w-4" />}
                    </button>
                  </th>
                  <th className="px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Dossier
                  </th>
                  <th className="px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Type
                  </th>
                  <th className="px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Status
                  </th>
                  <th className="hidden md:table-cell px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Client
                  </th>
                  <th className="hidden lg:table-cell px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Wederpartij
                  </th>
                  {hasModule("incasso") && (
                    <th className="hidden md:table-cell px-4 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Hoofdsom
                    </th>
                  )}
                  <th className="px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Geopend
                  </th>
                  <th className="px-4 py-3.5 w-10" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.items.map((zaak) => (
                  <tr
                    key={zaak.id}
                    className="group hover:bg-muted/40 transition-colors relative"
                    onMouseEnter={() => setHoveredRow(zaak.id)}
                    onMouseLeave={() => setHoveredRow(null)}
                  >
                    <td className="w-10 px-4 py-3.5">
                      <button
                        onClick={(e) => { e.stopPropagation(); toggleSelect(zaak.id); }}
                        className="text-muted-foreground hover:text-foreground transition-colors"
                      >
                        {selectedIds.has(zaak.id) ? <CheckSquare className="h-4 w-4 text-primary" /> : <Square className="h-4 w-4" />}
                      </button>
                    </td>
                    <td className="px-4 py-3.5">
                      <Link
                        href={`/zaken/${zaak.id}`}
                        className="font-mono text-sm font-semibold text-foreground hover:text-primary transition-colors"
                      >
                        {zaak.case_number}
                      </Link>
                      {zaak.description && (
                        <p className="text-xs text-muted-foreground mt-0.5 truncate max-w-[160px]">
                          {zaak.description}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3.5">
                      <span
                        className={`inline-flex rounded-md px-2 py-0.5 text-xs font-medium ${
                          TYPE_BADGE[zaak.case_type] ??
                          "bg-slate-50 text-slate-600"
                        }`}
                      >
                        {TYPE_LABELS[zaak.case_type] ?? zaak.case_type}
                      </span>
                    </td>
                    <td className="px-4 py-3.5">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
                          dynamicStatusBadge[zaak.status] ??
                          "bg-slate-50 text-slate-600 ring-slate-500/20"
                        }`}
                      >
                        {dynamicStatusLabels[zaak.status] ?? zaak.status}
                      </span>
                    </td>
                    <td className="hidden md:table-cell px-4 py-3.5">
                      {zaak.client ? (
                        <Link
                          href={`/relaties/${zaak.client.id}`}
                          className="text-sm text-foreground hover:text-primary transition-colors"
                        >
                          {zaak.client.name}
                        </Link>
                      ) : (
                        <span className="text-sm text-muted-foreground">-</span>
                      )}
                    </td>
                    <td className="hidden lg:table-cell px-4 py-3.5">
                      {zaak.opposing_party ? (
                        <Link
                          href={`/relaties/${zaak.opposing_party.id}`}
                          className="text-sm text-muted-foreground hover:text-primary transition-colors"
                        >
                          {zaak.opposing_party.name}
                        </Link>
                      ) : (
                        <span className="text-sm text-muted-foreground">-</span>
                      )}
                    </td>
                    {hasModule("incasso") && (
                      <td className="hidden md:table-cell px-4 py-3.5 text-right">
                        <span className="text-sm font-semibold text-foreground tabular-nums">
                          {formatCurrency(zaak.total_principal)}
                        </span>
                      </td>
                    )}
                    <td className="px-4 py-3.5 text-sm text-muted-foreground">
                      {formatDateShort(zaak.date_opened)}
                    </td>
                    <td className="px-4 py-3.5">
                      <Link
                        href={`/zaken/${zaak.id}`}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground opacity-0 group-hover:opacity-100 hover:bg-muted hover:text-foreground transition-all"
                        title="Bekijken"
                      >
                        <ArrowUpRight className="h-4 w-4" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data.pages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Pagina {page} van {data.pages} &middot; {data.total} dossiers
              </p>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border hover:bg-muted disabled:opacity-40 disabled:pointer-events-none transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                {Array.from({ length: Math.min(data.pages, 5) }, (_, i) => {
                  const pageNum =
                    data.pages <= 5
                      ? i + 1
                      : page <= 3
                        ? i + 1
                        : page >= data.pages - 2
                          ? data.pages - 4 + i
                          : page - 2 + i;
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setPage(pageNum)}
                      className={`inline-flex h-9 w-9 items-center justify-center rounded-lg text-sm font-medium transition-colors ${
                        pageNum === page
                          ? "bg-primary text-primary-foreground"
                          : "hover:bg-muted text-muted-foreground"
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
                <button
                  onClick={() =>
                    setPage((p) => Math.min(data.pages, p + 1))
                  }
                  disabled={page === data.pages}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border hover:bg-muted disabled:opacity-40 disabled:pointer-events-none transition-colors"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/50 py-20">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
            <Briefcase className="h-8 w-8 text-muted-foreground/50" />
          </div>
          <p className="mt-5 text-base font-medium text-foreground">
            Geen dossiers gevonden
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            {search || caseType || status
              ? "Probeer andere zoektermen of filters"
              : "Begin met het aanmaken van je eerste dossier"}
          </p>
          <Link
            href="/zaken/nieuw"
            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Nieuw dossier aanmaken
          </Link>
        </div>
      )}
    </div>
  );
}
