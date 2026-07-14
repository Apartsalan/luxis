"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowUpDown,
  ArrowUpRight,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Filter,
  FileText,
  List,
  Paperclip,
  Plus,
  Receipt,
  Search,
  Users,
  X,
} from "lucide-react";
import { toast } from "sonner";
import {
  useInvoices,
  useReceivables,
  useClaims,
  useClaimClients,
  INVOICE_STATUS_LABELS,
  INVOICE_STATUS_COLORS,
  type ClaimSortField,
  type ClaimSortDir,
} from "@/hooks/use-invoices";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import { AGING_TONES, CREDIT_NOTE_TONE, TONES } from "@/lib/tones";
import { QueryError } from "@/components/query-error";
import { useDebounce } from "@/hooks/use-debounce";
import { tokenStore } from "@/lib/token-store";

const CLAIM_SORT_FIELDS: ReadonlySet<ClaimSortField> = new Set([
  "invoice_date",
  "principal_amount",
]);

export default function FacturenPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialContactId = searchParams.get("contact_id") || "";
  const initialContactName = searchParams.get("contact_name") || "";
  const initialStatus = searchParams.get("status") || "";

  const [activeTab, setActiveTab] = useState<"facturen" | "vorderingen">(
    () => (searchParams.get("tab") === "vorderingen" ? "vorderingen" : "facturen")
  );
  // Weergave binnen Kantoorfacturen: platte lijst of per-klant-samenvatting
  // (het voormalige Debiteuren-tabblad).
  const [kantoorView, setKantoorView] = useState<"lijst" | "per_klant">(
    () => (searchParams.get("view") === "per_klant" ? "per_klant" : "lijst")
  );
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const [status, setStatus] = useState(initialStatus);
  const [contactId, setContactId] = useState(initialContactId);
  const [contactName, setContactName] = useState(initialContactName);
  const [page, setPage] = useState(1);

  const switchTab = (tab: "facturen" | "vorderingen") => {
    setActiveTab(tab);
    const params = new URLSearchParams(searchParams.toString());
    if (tab === "vorderingen") params.set("tab", "vorderingen");
    else params.delete("tab");
    router.replace(`/facturen${params.toString() ? `?${params}` : ""}`, { scroll: false });
  };

  const switchKantoorView = (view: "lijst" | "per_klant") => {
    setKantoorView(view);
    const params = new URLSearchParams(searchParams.toString());
    if (view === "per_klant") params.set("view", "per_klant");
    else params.delete("view");
    router.replace(`/facturen${params.toString() ? `?${params}` : ""}`, { scroll: false });
  };

  // When URL changes (e.g. clicking from debiteurenoverzicht, or browser-back), pick it up
  useEffect(() => {
    const newContactId = searchParams.get("contact_id") || "";
    const newContactName = searchParams.get("contact_name") || "";
    const newStatus = searchParams.get("status") || "";
    setContactId(newContactId);
    setContactName(newContactName);
    setStatus(newStatus);
    setActiveTab(searchParams.get("tab") === "vorderingen" ? "vorderingen" : "facturen");
    setKantoorView(searchParams.get("view") === "per_klant" ? "per_klant" : "lijst");
    if (newContactId) {
      setActiveTab("facturen");
      setKantoorView("lijst");
      setPage(1);
    }
  }, [searchParams]);

  const { data, isLoading, isError, error, refetch } = useInvoices({
    page,
    status: status || undefined,
    search: debouncedSearch || undefined,
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
              ? "Facturen die het kantoor zelf naar opdrachtgevers stuurt"
              : "Facturen van opdrachtgevers op hun debiteuren (op de dossiers)"}
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
          onClick={() => switchTab("facturen")}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "facturen"
              ? "bg-card text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <FileText className="mr-1.5 inline h-4 w-4" />
          Kantoorfacturen
        </button>
        <button
          onClick={() => switchTab("vorderingen")}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "vorderingen"
              ? "bg-card text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <Receipt className="mr-1.5 inline h-4 w-4" />
          Vorderingen
        </button>
      </div>

      {/* Facturen tab */}
      {activeTab === "facturen" && (
        <>
          {/* Weergave-schakelaar: platte lijst ↔ per-klant-samenvatting */}
          <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-1 w-fit">
            <button
              onClick={() => switchKantoorView("lijst")}
              className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                kantoorView === "lijst"
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <List className="h-3.5 w-3.5" />
              Lijst
            </button>
            <button
              onClick={() => switchKantoorView("per_klant")}
              className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                kantoorView === "per_klant"
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Users className="h-3.5 w-3.5" />
              Per klant
              {receivables && receivables.total_overdue > 0 && (
                <span className={`ml-0.5 inline-flex h-5 min-w-[20px] items-center justify-center rounded-full px-1.5 text-[10px] font-semibold ${TONES.danger.chip}`}>
                  {formatCurrency(receivables.total_overdue)}
                </span>
              )}
            </button>
          </div>

          {kantoorView === "per_klant" ? (
            <DebiteurenTab receivables={receivables} isLoading={recvLoading} />
          ) : (
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
                            factuur.invoice_type === "credit_note" ? CREDIT_NOTE_TONE.text : "text-foreground"
                          }`}>
                            {factuur.invoice_number}
                          </p>
                          {factuur.invoice_type === "credit_note" && (
                            <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium ${CREDIT_NOTE_TONE.chip}`}>
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
                          INVOICE_STATUS_COLORS[factuur.status] ?? TONES.gray.chip
                        }`}
                      >
                        {INVOICE_STATUS_LABELS[factuur.status] ?? factuur.status}
                      </span>
                    </div>
                    <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                      <span>{formatDateShort(factuur.invoice_date)}</span>
                      <span className={`text-sm font-semibold tabular-nums ${
                        factuur.invoice_type === "credit_note" ? TONES.danger.text : "text-foreground"
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
                                  ? CREDIT_NOTE_TONE.text
                                  : "text-foreground"
                              }`}
                            >
                              {factuur.invoice_number}
                            </Link>
                            {factuur.invoice_type === "credit_note" && (
                              <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium ${CREDIT_NOTE_TONE.chip}`}>
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
                              TONES.gray.chip
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
                                ? TONES.danger.text
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
                            className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground max-sm:opacity-100 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 hover:bg-muted hover:text-foreground transition-all"
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
                <FileText className="h-8 w-8 text-muted-foreground" />
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
        </>
      )}

      {/* Vorderingen tab */}
      {activeTab === "vorderingen" && <VorderingenTab />}
    </div>
  );
}

function ClaimSortHeader({
  label,
  field,
  activeField,
  direction,
  onToggle,
  align = "left",
}: {
  label: string;
  field: ClaimSortField;
  activeField: ClaimSortField | undefined;
  direction: ClaimSortDir;
  onToggle: (field: ClaimSortField) => void;
  align?: "left" | "right";
}) {
  const active = activeField === field;
  const Icon = active ? (direction === "asc" ? ChevronUp : ChevronDown) : ArrowUpDown;
  return (
    <button
      type="button"
      onClick={() => onToggle(field)}
      className={`inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider transition-colors ${
        active ? "text-foreground" : "text-muted-foreground hover:text-foreground"
      } ${align === "right" ? "flex-row-reverse" : ""}`}
    >
      <span>{label}</span>
      <Icon className={`h-3.5 w-3.5 ${active ? "opacity-100" : "opacity-50"}`} />
    </button>
  );
}

function VorderingenTab() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Zoeken blijft lokaal (typ-responsief + debounce), net als op de dossierpagina.
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const [page, setPage] = useState(1);

  // Discrete filters + sortering uit de URL (drill-downs en terug-knop landen op de
  // gefilterde lijst — patroon CONN-8 / DF139-sort van zaken/page.tsx).
  const [clientId, setClientId] = useState(() => searchParams.get("client_id") ?? "");
  const [onlyOpen, setOnlyOpen] = useState(() => searchParams.get("only_open") === "true");
  const [dateFrom, setDateFrom] = useState(() => searchParams.get("date_from") ?? "");
  const [dateTo, setDateTo] = useState(() => searchParams.get("date_to") ?? "");
  const [hasFile, setHasFile] = useState<"" | "yes" | "no">(() => {
    const v = searchParams.get("has_file");
    return v === "yes" || v === "no" ? v : "";
  });
  const [showMoreFilters, setShowMoreFilters] = useState(
    () => !!(searchParams.get("date_from") || searchParams.get("date_to") || searchParams.get("has_file"))
  );

  const sortByRaw = searchParams.get("sort_by") as ClaimSortField | null;
  const sortBy: ClaimSortField | undefined =
    sortByRaw && CLAIM_SORT_FIELDS.has(sortByRaw) ? sortByRaw : undefined;
  const sortDir: ClaimSortDir = searchParams.get("sort_dir") === "asc" ? "asc" : "desc";

  const { data: clients } = useClaimClients();

  // Merge één of meer filter/sort-waarden in de URL, met behoud van tab= en de
  // Kantoorfacturen-parameters. Leeg/null = verwijderen.
  const patchUrl = (patch: Record<string, string | null>) => {
    const params = new URLSearchParams(searchParams.toString());
    for (const [k, v] of Object.entries(patch)) {
      if (v === null || v === "") params.delete(k);
      else params.set(k, v);
    }
    router.replace(`/facturen?${params.toString()}`, { scroll: false });
  };

  const toggleSort = (field: ClaimSortField) => {
    const newDir: ClaimSortDir = sortBy === field && sortDir === "desc" ? "asc" : "desc";
    patchUrl({ sort_by: field, sort_dir: newDir });
    setPage(1);
  };

  const clearFilters = () => {
    setClientId("");
    setOnlyOpen(false);
    setDateFrom("");
    setDateTo("");
    setHasFile("");
    setSearch("");
    setShowMoreFilters(false);
    setPage(1);
    patchUrl({ client_id: null, only_open: null, date_from: null, date_to: null, has_file: null });
  };

  const { data, isLoading, isError, error, refetch } = useClaims({
    page,
    search: debouncedSearch || undefined,
    only_open: onlyOpen,
    client_id: clientId || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    has_file: hasFile,
    sort_by: sortBy,
    sort_dir: sortDir,
  });

  const activeFilters = [clientId, onlyOpen, dateFrom, dateTo, hasFile].filter(Boolean).length;

  const openPdf = async (caseId: string, fileId: string) => {
    try {
      const token = tokenStore.getAccess();
      const res = await fetch(`/api/cases/${caseId}/files/${fileId}/preview`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Kan de factuur-PDF niet openen");
      const blob = await res.blob();
      window.open(URL.createObjectURL(blob), "_blank");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Kan de factuur-PDF niet openen");
    }
  };

  return (
    <div className="space-y-3">
      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Zoek op factuurnummer, dossier of debiteur..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full rounded-lg border border-input bg-card pl-10 pr-4 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <select
            value={clientId}
            onChange={(e) => {
              setClientId(e.target.value);
              setPage(1);
              patchUrl({ client_id: e.target.value || null });
            }}
            aria-label="Filter op opdrachtgever"
            className="rounded-lg border border-input bg-card px-3 py-2.5 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors max-w-[220px]"
          >
            <option value="">Alle opdrachtgevers</option>
            {clients?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
          <label className="inline-flex items-center gap-2 rounded-lg border border-input bg-card px-3 py-2.5 text-sm text-foreground cursor-pointer select-none">
            <input
              type="checkbox"
              checked={onlyOpen}
              onChange={(e) => {
                setOnlyOpen(e.target.checked);
                setPage(1);
                patchUrl({ only_open: e.target.checked ? "true" : null });
              }}
              className="h-4 w-4 rounded border-input"
            />
            Alleen lopende dossiers
          </label>
          <button
            onClick={() => setShowMoreFilters(!showMoreFilters)}
            className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-2.5 text-xs font-medium transition-colors ${
              showMoreFilters || dateFrom || dateTo || hasFile
                ? "border-primary/30 bg-primary/5 text-primary"
                : "border-border text-muted-foreground hover:bg-muted"
            }`}
          >
            <Filter className="h-3.5 w-3.5" />
            Meer filters
            {(dateFrom || dateTo || hasFile) && (
              <span className="ml-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] text-primary-foreground">
                {[dateFrom, dateTo, hasFile].filter(Boolean).length}
              </span>
            )}
          </button>
          {activeFilters > 0 && (
            <button
              onClick={clearFilters}
              className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-2.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
            >
              <X className="h-3 w-3" />
              Wis filters
            </button>
          )}
        </div>
      </div>

      {/* Uitgebreide filters */}
      {showMoreFilters && (
        <div className="flex flex-wrap gap-3 rounded-lg border border-border bg-card px-4 py-3 animate-fade-in">
          <div className="flex flex-col gap-1">
            <label htmlFor="v-datum-vanaf" className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">Factuurdatum vanaf</label>
            <input
              id="v-datum-vanaf"
              type="date"
              value={dateFrom}
              onChange={(e) => { setDateFrom(e.target.value); setPage(1); patchUrl({ date_from: e.target.value || null }); }}
              className="rounded-md border border-input bg-background px-3 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="v-datum-tm" className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">Factuurdatum t/m</label>
            <input
              id="v-datum-tm"
              type="date"
              value={dateTo}
              onChange={(e) => { setDateTo(e.target.value); setPage(1); patchUrl({ date_to: e.target.value || null }); }}
              className="rounded-md border border-input bg-background px-3 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label htmlFor="v-pdf" className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">Factuur-PDF</label>
            <select
              id="v-pdf"
              value={hasFile}
              onChange={(e) => {
                const v = e.target.value as "" | "yes" | "no";
                setHasFile(v);
                setPage(1);
                patchUrl({ has_file: v || null });
              }}
              className="rounded-md border border-input bg-background px-3 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 min-w-[160px]"
            >
              <option value="">Maakt niet uit</option>
              <option value="yes">Wel gekoppeld</option>
              <option value="no">Niet gekoppeld</option>
            </select>
          </div>
        </div>
      )}

      {isError ? (
        <QueryError message={error?.message} onRetry={() => refetch()} />
      ) : isLoading ? (
        <div className="rounded-xl border border-border bg-card p-1">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="flex items-center gap-4 px-4 py-3.5">
              <div className="h-4 w-24 rounded skeleton" />
              <div className="hidden md:block h-4 w-40 rounded skeleton" />
              <div className="hidden lg:block h-4 w-20 rounded skeleton" />
              <div className="h-4 w-20 rounded skeleton ml-auto" />
            </div>
          ))}
        </div>
      ) : data && data.items.length > 0 ? (
        <>
          <div className="overflow-x-auto rounded-xl border border-border bg-card">
            <table className="w-full min-w-[800px]">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Factuurnr.</th>
                  <th className="px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Debiteur</th>
                  <th className="hidden lg:table-cell px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Dossier</th>
                  <th className="hidden md:table-cell px-4 py-3.5 text-left">
                    <ClaimSortHeader label="Factuurdatum" field="invoice_date" activeField={sortBy} direction={sortDir} onToggle={toggleSort} />
                  </th>
                  <th className="px-4 py-3.5 text-right">
                    <ClaimSortHeader label="Hoofdsom" field="principal_amount" activeField={sortBy} direction={sortDir} onToggle={toggleSort} align="right" />
                  </th>
                  <th className="px-4 py-3.5 w-10 text-center text-xs font-semibold uppercase tracking-wider text-muted-foreground" title="Factuur-PDF aanwezig">PDF</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.items.map((v) => (
                  <tr key={v.id} className="hover:bg-muted/40 transition-colors">
                    <td className="px-4 py-3.5">
                      <Link href={`/zaken/${v.case_id}`} className="font-mono text-sm font-semibold text-foreground hover:text-primary transition-colors">
                        {v.invoice_number || "—"}
                      </Link>
                    </td>
                    <td className="px-4 py-3.5 text-sm text-foreground">
                      <span className="truncate max-w-[220px] block">{v.debtor_name ?? "—"}</span>
                    </td>
                    <td className="hidden lg:table-cell px-4 py-3.5 text-sm text-muted-foreground font-mono">
                      <Link href={`/zaken/${v.case_id}`} className="hover:text-primary hover:underline transition-colors">
                        {v.case_number}
                      </Link>
                    </td>
                    <td className="hidden md:table-cell px-4 py-3.5 text-sm text-muted-foreground">
                      {v.invoice_date ? formatDateShort(v.invoice_date) : "—"}
                    </td>
                    <td className="px-4 py-3.5 text-right text-sm font-semibold tabular-nums text-foreground">
                      {formatCurrency(Number(v.principal_amount))}
                    </td>
                    <td className="px-4 py-3.5 text-center">
                      {v.has_invoice_file && v.invoice_file_id ? (
                        <button
                          type="button"
                          onClick={() => openPdf(v.case_id, v.invoice_file_id!)}
                          title="Open de factuur-PDF"
                          className="inline-flex text-muted-foreground hover:text-primary transition-colors"
                        >
                          <Paperclip className="h-4 w-4" />
                        </button>
                      ) : (
                        <span className="text-muted-foreground/30" title="Geen factuur-PDF gekoppeld">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Totaal + pagination */}
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              {data.total} {data.total === 1 ? "vordering" : "vorderingen"} &middot; totale hoofdsom{" "}
              <span className="font-semibold text-foreground tabular-nums">{formatCurrency(Number(data.total_principal))}</span>
            </p>
            {data.pages > 1 && (
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border hover:bg-muted disabled:opacity-40 disabled:pointer-events-none transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="px-2 text-sm text-muted-foreground">
                  {page} / {data.pages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                  disabled={page === data.pages}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border hover:bg-muted disabled:opacity-40 disabled:pointer-events-none transition-colors"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/50 py-20">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
            <Receipt className="h-8 w-8 text-muted-foreground" />
          </div>
          <p className="mt-5 text-base font-medium text-foreground">Geen vorderingen gevonden</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {search || activeFilters > 0 ? "Probeer andere zoektermen of filters" : "Vorderingen ontstaan op de dossiers"}
          </p>
        </div>
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
          className={`${AGING_TONES.d0_30.dot} transition-all`}
          style={{ width: `${pCurrent}%` }}
          title={`0-30 dagen: ${formatCurrency(current)}`}
        />
      )}
      {p31 > 0 && (
        <div
          className={`${AGING_TONES.d31_60.dot} transition-all`}
          style={{ width: `${p31}%` }}
          title={`31-60 dagen: ${formatCurrency(days31)}`}
        />
      )}
      {p61 > 0 && (
        <div
          className={`${AGING_TONES.d61_90.dot} transition-all`}
          style={{ width: `${p61}%` }}
          title={`61-90 dagen: ${formatCurrency(days61)}`}
        />
      )}
      {p90 > 0 && (
        <div
          className={`${AGING_TONES.d90_plus.dot} transition-all`}
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
        <div className={`flex h-16 w-16 items-center justify-center rounded-2xl ${TONES.success.surface}`}>
          <Users className={`h-8 w-8 ${TONES.success.textFaint}`} />
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
          <p className={`text-xs font-medium ${AGING_TONES.d0_30.text} uppercase tracking-wider`}>
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
          <p className={`text-xs font-medium ${AGING_TONES.d31_60.text} uppercase tracking-wider`}>
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
          <p className={`text-xs font-medium ${AGING_TONES.d61_90.text} uppercase tracking-wider`}>
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
          <p className={`text-xs font-medium ${AGING_TONES.d90_plus.text} uppercase tracking-wider`}>
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
              <span className={`h-2.5 w-2.5 rounded-full ${AGING_TONES.d0_30.dot}`} /> 0-30d
            </span>
            <span className="flex items-center gap-1.5">
              <span className={`h-2.5 w-2.5 rounded-full ${AGING_TONES.d31_60.dot}`} /> 31-60d
            </span>
            <span className="flex items-center gap-1.5">
              <span className={`h-2.5 w-2.5 rounded-full ${AGING_TONES.d61_90.dot}`} /> 61-90d
            </span>
            <span className="flex items-center gap-1.5">
              <span className={`h-2.5 w-2.5 rounded-full ${AGING_TONES.d90_plus.dot}`} /> 90+d
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
              <th className={`px-4 py-3.5 text-right text-xs font-semibold uppercase tracking-wider ${AGING_TONES.d0_30.text}`}>
                0-30d
              </th>
              <th className={`px-4 py-3.5 text-right text-xs font-semibold uppercase tracking-wider ${AGING_TONES.d31_60.text}`}>
                31-60d
              </th>
              <th className={`px-4 py-3.5 text-right text-xs font-semibold uppercase tracking-wider ${AGING_TONES.d61_90.text}`}>
                61-90d
              </th>
              <th className={`px-4 py-3.5 text-right text-xs font-semibold uppercase tracking-wider ${AGING_TONES.d90_plus.text}`}>
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
                    <span className={AGING_TONES.d31_60.textStrong}>{formatCurrency(contact.days_31_60.total)}</span>
                  ) : (
                    <span className="text-muted-foreground/40">-</span>
                  )}
                </td>
                <td className="px-4 py-3.5 text-right text-sm tabular-nums">
                  {contact.days_61_90.total > 0 ? (
                    <span className={AGING_TONES.d61_90.textStrong}>{formatCurrency(contact.days_61_90.total)}</span>
                  ) : (
                    <span className="text-muted-foreground/40">-</span>
                  )}
                </td>
                <td className="px-4 py-3.5 text-right text-sm tabular-nums">
                  {contact.days_90_plus.total > 0 ? (
                    <span className={`font-medium ${AGING_TONES.d90_plus.textStrong}`}>{formatCurrency(contact.days_90_plus.total)}</span>
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
              <td className={`px-4 py-3.5 text-right text-sm font-semibold tabular-nums ${AGING_TONES.d31_60.textStrong}`}>
                {days_31_60.total > 0 ? formatCurrency(days_31_60.total) : "-"}
              </td>
              <td className={`px-4 py-3.5 text-right text-sm font-semibold tabular-nums ${AGING_TONES.d61_90.textStrong}`}>
                {days_61_90.total > 0 ? formatCurrency(days_61_90.total) : "-"}
              </td>
              <td className={`px-4 py-3.5 text-right text-sm font-semibold tabular-nums ${AGING_TONES.d90_plus.textStrong}`}>
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
        <div className={`flex items-start gap-3 rounded-xl border ${TONES.warning.border} ${TONES.warning.surface} p-4`}>
          <AlertTriangle className={`h-5 w-5 ${TONES.warning.text} mt-0.5 shrink-0`} />
          <div>
            <p className={`text-sm font-medium ${TONES.warning.heading}`}>
              {formatCurrency(total_overdue)} aan achterstallige facturen
            </p>
            <p className={`text-sm ${TONES.warning.textStrong} mt-0.5`}>
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
