"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  FileText,
  Plus,
  Search,
  Users,
  X,
} from "lucide-react";
import {
  useInvoices,
  useReceivables,
  INVOICE_STATUS_LABELS,
  INVOICE_STATUS_COLORS,
  type ContactReceivable,
} from "@/hooks/use-invoices";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import { QueryError } from "@/components/query-error";

export default function FacturenPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialContactId = searchParams.get("contact_id") || "";
  const initialContactName = searchParams.get("contact_name") || "";
  const initialStatus = searchParams.get("status") || "";

  const [activeTab, setActiveTab] = useState<"facturen" | "debiteuren">("facturen");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState(initialStatus);
  const [contactId, setContactId] = useState(initialContactId);
  const [contactName, setContactName] = useState(initialContactName);
  const [page, setPage] = useState(1);

  // When URL changes (e.g. clicking from debiteurenoverzicht), pick it up
  useEffect(() => {
    const newContactId = searchParams.get("contact_id") || "";
    const newContactName = searchParams.get("contact_name") || "";
    const newStatus = searchParams.get("status") || "";
    setContactId(newContactId);
    setContactName(newContactName);
    setStatus(newStatus);
    if (newContactId) {
      setActiveTab("facturen");
      setPage(1);
    }
  }, [searchParams]);

  const { data, isLoading, isError, error, refetch } = useInvoices({
    page,
    status: status || undefined,
    search: search || undefined,
    contact_id: contactId || undefined,
  });

  const { data: receivables, isLoading: recvLoading } = useReceivables();

  const activeFilters = [status, contactId].filter(Boolean).length;

  const clearContactFilter = () => {
    setContactId("");
    setContactName("");
    setPage(1);
    router.replace("/facturen");
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Facturen</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {activeTab === "facturen"
              ? data?.total
                ? `${data.total} ${data.total === 1 ? "factuur" : "facturen"}`
                : "Beheer je facturen"
              : "Openstaande vorderingen per relatie"}
          </p>
        </div>
        <Link
          href="/facturen/nieuw"
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span className="hidden sm:inline">Nieuwe factuur</span>
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg bg-muted/50 p-1">
        <button
          onClick={() => setActiveTab("facturen")}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "facturen"
              ? "bg-card text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <FileText className="mr-1.5 inline h-4 w-4" />
          Facturen
        </button>
        <button
          onClick={() => setActiveTab("debiteuren")}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "debiteuren"
              ? "bg-card text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <Users className="mr-1.5 inline h-4 w-4" />
          Debiteuren
          {receivables && receivables.total_overdue > 0 && (
            <span className="ml-1.5 inline-flex h-5 min-w-[20px] items-center justify-center rounded-full bg-red-100 px-1.5 text-[10px] font-semibold text-red-700">
              {formatCurrency(receivables.total_overdue)}
            </span>
          )}
        </button>
      </div>

      {/* Facturen tab */}
      {activeTab === "facturen" && (
        <>
          {/* Filters */}
          <div className="space-y-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Zoek op factuurnummer, dossier of relatie..."
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
                  value={status}
                  onChange={(e) => {
                    setStatus(e.target.value);
                    setPage(1);
                  }}
                  className="rounded-lg border border-input bg-card px-3 py-2.5 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                >
                  <option value="">Alle statussen</option>
                  <option value="sent,partially_paid,overdue">Alleen openstaand</option>
                  {Object.entries(INVOICE_STATUS_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
                {activeFilters > 0 && (
                  <button
                    onClick={() => {
                      setStatus("");
                      setSearch("");
                      clearContactFilter();
                    }}
                    className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-2.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
                  >
                    Wis filters
                  </button>
                )}
              </div>
            </div>

            {/* Active contact filter chip */}
            {contactId && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Gefilterd op:</span>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary ring-1 ring-inset ring-primary/20">
                  <Users className="h-3 w-3" />
                  {contactName || "Relatie"}
                  <button
                    onClick={clearContactFilter}
                    className="ml-1 rounded-full hover:bg-primary/20 p-0.5 transition-colors"
                    title="Filter verwijderen"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              </div>
            )}
          </div>

          {/* Table */}
          {isError ? (
            <QueryError message={error?.message} onRetry={() => refetch()} />
          ) : isLoading ? (
            <div className="rounded-xl border border-border bg-card">
              <div className="p-1">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="flex items-center gap-4 px-4 py-3.5">
                    <div className="h-4 w-24 rounded skeleton" />
                    <div className="h-5 w-20 rounded-full skeleton" />
                    <div className="hidden md:block h-4 w-32 rounded skeleton" />
                    <div className="hidden lg:block h-4 w-20 rounded skeleton" />
                    <div className="h-4 w-20 rounded skeleton ml-auto" />
                    <div className="h-4 w-20 rounded skeleton" />
                  </div>
                ))}
              </div>
            </div>
          ) : data?.items && data.items.length > 0 ? (
            <>
              {/* Mobile card view */}
              <div className="block sm:hidden space-y-3">
                {data.items.map((factuur) => (
                  <Link
                    key={factuur.id}
                    href={`/facturen/${factuur.id}`}
                    className="block rounded-xl border border-border bg-card p-4 hover:border-primary/30 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <p className={`font-mono text-sm font-semibold ${
                            factuur.invoice_type === "credit_note" ? "text-purple-700" : "text-foreground"
                          }`}>
                            {factuur.invoice_number}
                          </p>
                          {factuur.invoice_type === "credit_note" && (
                            <span className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium bg-purple-100 text-purple-600">
                              CN
                            </span>
                          )}
                        </div>
                        {factuur.contact_name && (
                          <p className="text-xs text-muted-foreground mt-0.5 truncate">
                            {factuur.contact_name}
                          </p>
                        )}
                      </div>
                      <span
                        className={`shrink-0 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          INVOICE_STATUS_COLORS[factuur.status] ?? "bg-gray-100 text-gray-700"
                        }`}
                      >
                        {INVOICE_STATUS_LABELS[factuur.status] ?? factuur.status}
                      </span>
                    </div>
                    <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                      <span>{formatDateShort(factuur.invoice_date)}</span>
                      <span className={`text-sm font-semibold tabular-nums ${
                        factuur.invoice_type === "credit_note" ? "text-red-600" : "text-foreground"
                      }`}>
                        {factuur.invoice_type === "credit_note" ? "-" : ""}
                        {formatCurrency(factuur.total)}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>

              {/* Desktop table view */}
              <div className="hidden sm:block overflow-x-auto rounded-xl border border-border bg-card">
                <table className="w-full min-w-[800px]">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Factuur
                      </th>
                      <th className="px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Status
                      </th>
                      <th className="px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Relatie
                      </th>
                      <th className="hidden lg:table-cell px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Dossier
                      </th>
                      <th className="hidden md:table-cell px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Datum
                      </th>
                      <th className="hidden lg:table-cell px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Vervaldatum
                      </th>
                      <th className="px-4 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Totaal
                      </th>
                      <th className="px-4 py-3.5 w-10" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {data.items.map((factuur) => (
                      <tr
                        key={factuur.id}
                        className="group hover:bg-muted/40 transition-colors"
                      >
                        <td className="px-4 py-3.5">
                          <div className="flex items-center gap-2">
                            <Link
                              href={`/facturen/${factuur.id}`}
                              className={`font-mono text-sm font-semibold hover:text-primary transition-colors ${
                                factuur.invoice_type === "credit_note"
                                  ? "text-purple-700"
                                  : "text-foreground"
                              }`}
                            >
                              {factuur.invoice_number}
                            </Link>
                            {factuur.invoice_type === "credit_note" && (
                              <span className="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium bg-purple-100 text-purple-600">
                                CN
                              </span>
                            )}
                          </div>
                          {factuur.invoice_type === "credit_note" && factuur.linked_invoice_number && (
                            <p className="text-[11px] text-muted-foreground mt-0.5">
                              bij {factuur.linked_invoice_number}
                            </p>
                          )}
                        </td>
                        <td className="px-4 py-3.5">
                          <span
                            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                              INVOICE_STATUS_COLORS[factuur.status] ??
                              "bg-gray-100 text-gray-700"
                            }`}
                          >
                            {INVOICE_STATUS_LABELS[factuur.status] ??
                              factuur.status}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 text-sm text-foreground">
                          <span className="truncate max-w-[200px] block">{factuur.contact_name ?? "-"}</span>
                        </td>
                        <td className="hidden lg:table-cell px-4 py-3.5 text-sm text-muted-foreground font-mono">
                          {factuur.case_id && factuur.case_number ? (
                            <Link
                              href={`/zaken/${factuur.case_id}`}
                              className="hover:text-primary hover:underline transition-colors"
                            >
                              {factuur.case_number}
                            </Link>
                          ) : (
                            "-"
                          )}
                        </td>
                        <td className="hidden md:table-cell px-4 py-3.5 text-sm text-muted-foreground">
                          {formatDateShort(factuur.invoice_date)}
                        </td>
                        <td className="hidden lg:table-cell px-4 py-3.5 text-sm text-muted-foreground">
                          {formatDateShort(factuur.due_date)}
                        </td>
                        <td className="px-4 py-3.5 text-right">
                          <span
                            className={`text-sm font-semibold tabular-nums ${
                              factuur.invoice_type === "credit_note"
                                ? "text-red-600"
                                : "text-foreground"
                            }`}
                          >
                            {factuur.invoice_type === "credit_note" ? "-" : ""}
                            {formatCurrency(factuur.total)}
                          </span>
                        </td>
                        <td className="px-4 py-3.5">
                          <Link
                            href={`/facturen/${factuur.id}`}
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
                    Pagina {page} van {data.pages} &middot; {data.total} facturen
                  </p>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border hover:bg-muted disabled:opacity-40 disabled:pointer-events-none transition-colors"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </button>
                    {Array.from(
                      { length: Math.min(data.pages, 5) },
                      (_, i) => {
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
                      }
                    )}
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
                <FileText className="h-8 w-8 text-muted-foreground/50" />
              </div>
              <p className="mt-5 text-base font-medium text-foreground">
                Geen facturen gevonden
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {search || status
                  ? "Probeer andere zoektermen of filters"
                  : "Begin met het aanmaken van je eerste factuur"}
              </p>
              <Link
                href="/facturen/nieuw"
                className="mt-5 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
              >
                <Plus className="h-4 w-4" />
                Nieuwe factuur aanmaken
              </Link>
            </div>
          )}
        </>
      )}

      {/* Debiteuren tab */}
      {activeTab === "debiteuren" && (
        <DebiteurenTab receivables={receivables} isLoading={recvLoading} />
      )}
    </div>
  );
}

function AgingBar({
  current,
  days31,
  days61,
  days90,
  total,
}: {
  current: number;
  days31: number;
  days61: number;
  days90: number;
  total: number;
}) {
  if (total <= 0) return null;
  const pCurrent = (current / total) * 100;
  const p31 = (days31 / total) * 100;
  const p61 = (days61 / total) * 100;
  const p90 = (days90 / total) * 100;

  return (
    <div className="flex h-2 w-full overflow-hidden rounded-full bg-muted">
      {pCurrent > 0 && (
        <div
          className="bg-emerald-400 transition-all"
          style={{ width: `${pCurrent}%` }}
          title={`0-30 dagen: ${formatCurrency(current)}`}
        />
      )}
      {p31 > 0 && (
        <div
          className="bg-amber-400 transition-all"
          style={{ width: `${p31}%` }}
          title={`31-60 dagen: ${formatCurrency(days31)}`}
        />
      )}
      {p61 > 0 && (
        <div
          className="bg-orange-400 transition-all"
          style={{ width: `${p61}%` }}
          title={`61-90 dagen: ${formatCurrency(days61)}`}
        />
      )}
      {p90 > 0 && (
        <div
          className="bg-red-500 transition-all"
          style={{ width: `${p90}%` }}
          title={`90+ dagen: ${formatCurrency(days90)}`}
        />
      )}
    </div>
  );
}

function DebiteurenTab({
  receivables,
  isLoading,
}: {
  receivables: ReturnType<typeof useReceivables>["data"];
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-xl border border-border bg-card p-6">
            <div className="flex items-center gap-4">
              <div className="h-10 w-10 rounded-lg skeleton" />
              <div className="space-y-2 flex-1">
                <div className="h-4 w-32 rounded skeleton" />
                <div className="h-3 w-48 rounded skeleton" />
              </div>
              <div className="h-6 w-24 rounded skeleton" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!receivables || receivables.contacts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/50 py-20">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-50">
          <Users className="h-8 w-8 text-emerald-400" />
        </div>
        <p className="mt-5 text-base font-medium text-foreground">
          Geen openstaande facturen
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          Alle facturen zijn betaald
        </p>
      </div>
    );
  }

  const { total_outstanding, total_overdue, current, days_31_60, days_61_90, days_90_plus, contacts } = receivables;

  return (
    <div className="space-y-6">
      {/* Summary KPIs */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Totaal openstaand
          </p>
          <p className="mt-1 text-xl font-bold text-foreground tabular-nums">
            {formatCurrency(total_outstanding)}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs font-medium text-emerald-600 uppercase tracking-wider">
            0-30 dagen
          </p>
          <p className="mt-1 text-xl font-bold text-foreground tabular-nums">
            {formatCurrency(current.total)}
          </p>
          <p className="text-xs text-muted-foreground">
            {current.count} factuur{current.count !== 1 ? "en" : ""}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs font-medium text-amber-600 uppercase tracking-wider">
            31-60 dagen
          </p>
          <p className="mt-1 text-xl font-bold text-foreground tabular-nums">
            {formatCurrency(days_31_60.total)}
          </p>
          <p className="text-xs text-muted-foreground">
            {days_31_60.count} factuur{days_31_60.count !== 1 ? "en" : ""}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs font-medium text-orange-600 uppercase tracking-wider">
            61-90 dagen
          </p>
          <p className="mt-1 text-xl font-bold text-foreground tabular-nums">
            {formatCurrency(days_61_90.total)}
          </p>
          <p className="text-xs text-muted-foreground">
            {days_61_90.count} factuur{days_61_90.count !== 1 ? "en" : ""}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs font-medium text-red-600 uppercase tracking-wider">
            90+ dagen
          </p>
          <p className="mt-1 text-xl font-bold text-foreground tabular-nums">
            {formatCurrency(days_90_plus.total)}
          </p>
          <p className="text-xs text-muted-foreground">
            {days_90_plus.count} factuur{days_90_plus.count !== 1 ? "en" : ""}
          </p>
        </div>
      </div>

      {/* Overall aging bar */}
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-medium text-foreground">Aging verdeling</p>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" /> 0-30d
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-amber-400" /> 31-60d
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-orange-400" /> 61-90d
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-red-500" /> 90+d
            </span>
          </div>
        </div>
        <AgingBar
          current={current.total}
          days31={days_31_60.total}
          days61={days_61_90.total}
          days90={days_90_plus.total}
          total={total_outstanding}
        />
      </div>

      {/* Per-contact table */}
      <div className="overflow-x-auto rounded-xl border border-border bg-card">
        <table className="w-full min-w-[800px]">
          <thead>
            <tr className="border-b border-border">
              <th className="px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Relatie
              </th>
              <th className="px-4 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Facturen
              </th>
              <th className="px-4 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-emerald-600">
                0-30d
              </th>
              <th className="px-4 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-amber-600">
                31-60d
              </th>
              <th className="px-4 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-orange-600">
                61-90d
              </th>
              <th className="px-4 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-red-600">
                90+d
              </th>
              <th className="px-4 py-3.5 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Totaal
              </th>
              <th className="px-4 py-3.5 w-48 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Verdeling
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {contacts.map((contact) => (
              <tr key={contact.contact_id} className="hover:bg-muted/40 transition-colors">
                <td className="px-4 py-3.5">
                  <Link
                    href={`/facturen?contact_id=${contact.contact_id}&contact_name=${encodeURIComponent(contact.contact_name)}&status=sent,partially_paid,overdue`}
                    className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                    title="Bekijk openstaande facturen"
                  >
                    {contact.contact_name}
                  </Link>
                  <p className="text-xs text-muted-foreground">
                    Oudste: {formatDateShort(contact.oldest_due_date)}
                  </p>
                </td>
                <td className="px-4 py-3.5 text-right text-sm tabular-nums text-muted-foreground">
                  {contact.invoice_count}
                </td>
                <td className="px-4 py-3.5 text-right text-sm tabular-nums">
                  {contact.current.total > 0 ? formatCurrency(contact.current.total) : (
                    <span className="text-muted-foreground/40">-</span>
                  )}
                </td>
                <td className="px-4 py-3.5 text-right text-sm tabular-nums">
                  {contact.days_31_60.total > 0 ? (
                    <span className="text-amber-700">{formatCurrency(contact.days_31_60.total)}</span>
                  ) : (
                    <span className="text-muted-foreground/40">-</span>
                  )}
                </td>
                <td className="px-4 py-3.5 text-right text-sm tabular-nums">
                  {contact.days_61_90.total > 0 ? (
                    <span className="text-orange-700">{formatCurrency(contact.days_61_90.total)}</span>
                  ) : (
                    <span className="text-muted-foreground/40">-</span>
                  )}
                </td>
                <td className="px-4 py-3.5 text-right text-sm tabular-nums">
                  {contact.days_90_plus.total > 0 ? (
                    <span className="font-medium text-red-700">{formatCurrency(contact.days_90_plus.total)}</span>
                  ) : (
                    <span className="text-muted-foreground/40">-</span>
                  )}
                </td>
                <td className="px-4 py-3.5 text-right">
                  <span className="text-sm font-semibold text-foreground tabular-nums">
                    {formatCurrency(contact.total_outstanding)}
                  </span>
                </td>
                <td className="px-4 py-3.5">
                  <AgingBar
                    current={contact.current.total}
                    days31={contact.days_31_60.total}
                    days61={contact.days_61_90.total}
                    days90={contact.days_90_plus.total}
                    total={contact.total_outstanding}
                  />
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-border bg-muted/20">
              <td className="px-4 py-3.5 text-sm font-semibold text-foreground">
                Totaal
              </td>
              <td className="px-4 py-3.5 text-right text-sm font-semibold tabular-nums text-foreground">
                {contacts.reduce((sum, c) => sum + c.invoice_count, 0)}
              </td>
              <td className="px-4 py-3.5 text-right text-sm font-semibold tabular-nums text-foreground">
                {current.total > 0 ? formatCurrency(current.total) : "-"}
              </td>
              <td className="px-4 py-3.5 text-right text-sm font-semibold tabular-nums text-amber-700">
                {days_31_60.total > 0 ? formatCurrency(days_31_60.total) : "-"}
              </td>
              <td className="px-4 py-3.5 text-right text-sm font-semibold tabular-nums text-orange-700">
                {days_61_90.total > 0 ? formatCurrency(days_61_90.total) : "-"}
              </td>
              <td className="px-4 py-3.5 text-right text-sm font-semibold tabular-nums text-red-700">
                {days_90_plus.total > 0 ? formatCurrency(days_90_plus.total) : "-"}
              </td>
              <td className="px-4 py-3.5 text-right text-sm font-bold tabular-nums text-foreground">
                {formatCurrency(total_outstanding)}
              </td>
              <td className="px-4 py-3.5">
                <AgingBar
                  current={current.total}
                  days31={days_31_60.total}
                  days61={days_61_90.total}
                  days90={days_90_plus.total}
                  total={total_outstanding}
                />
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Overdue warning */}
      {total_overdue > 0 && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-amber-800">
              {formatCurrency(total_overdue)} aan achterstallige facturen
            </p>
            <p className="text-sm text-amber-700 mt-0.5">
              {days_90_plus.count > 0 && (
                <>
                  {days_90_plus.count} factuur{days_90_plus.count !== 1 ? "en" : ""} ouder dan 90 dagen.{" "}
                </>
              )}
              Overweeg een herinnering of incassoprocedure.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
