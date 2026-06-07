"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import {
  Plus,
  Search,
  Building2,
  User,
  Mail,
  Phone,
  MapPin,
  Users,
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  ArrowUpDown,
  Briefcase,
  CheckSquare,
  Square,
  Trash2,
  X,
  Loader2,
} from "lucide-react";
import { useRelations, type RelationSortField, type SortDir } from "@/hooks/use-relations";
import { useDebounce } from "@/hooks/use-debounce";
import { formatDateShort } from "@/lib/utils";
import { QueryError } from "@/components/query-error";
import { useConfirm } from "@/components/confirm-dialog";
import { api } from "@/lib/api";
import { toast } from "sonner";

function SortHeader({
  label,
  field,
  activeField,
  direction,
  onToggle,
}: {
  label: string;
  field: RelationSortField;
  activeField: RelationSortField;
  direction: SortDir;
  onToggle: (field: RelationSortField) => void;
}) {
  const active = activeField === field;
  const Icon = active ? (direction === "asc" ? ChevronUp : ChevronDown) : ArrowUpDown;
  return (
    <button
      type="button"
      onClick={() => onToggle(field)}
      className={`inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider transition-colors ${
        active ? "text-foreground" : "text-muted-foreground hover:text-foreground"
      }`}
    >
      <span>{label}</span>
      <Icon className={`h-3.5 w-3.5 ${active ? "opacity-100" : "opacity-50"}`} />
    </button>
  );
}

const SORT_FIELDS: ReadonlySet<RelationSortField> = new Set([
  "name",
  "contact_type",
  "visit_city",
  "email",
  "created_at",
]);

export default function RelatiesPage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // DF138-sort-persist: sortBy/sortDir uit URL lezen zodat browser-back en
  // directe links de sortering bewaren. Standaard 'name asc' als geen URL.
  const sortByRaw = searchParams.get("sort_by") as RelationSortField | null;
  const sortDirRaw = searchParams.get("sort_dir") as SortDir | null;
  const sortBy: RelationSortField = sortByRaw && SORT_FIELDS.has(sortByRaw) ? sortByRaw : "name";
  const sortDir: SortDir = sortDirRaw === "desc" ? "desc" : "asc";

  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const [contactType, setContactType] = useState("");
  const [page, setPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [bulkLoading, setBulkLoading] = useState(false);
  const { confirm, ConfirmDialog: ConfirmDialogEl } = useConfirm();

  const toggleSort = (field: RelationSortField) => {
    let newDir: SortDir;
    if (sortBy === field) {
      newDir = sortDir === "asc" ? "desc" : "asc";
    } else {
      // Datumkolommen openen logischer op nieuwste eerst.
      newDir = field === "created_at" ? "desc" : "asc";
    }
    const params = new URLSearchParams(searchParams.toString());
    params.set("sort_by", field);
    params.set("sort_dir", newDir);
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    setPage(1);
  };

  const { data, isLoading, isError, error, refetch } = useRelations({
    page,
    search: debouncedSearch || undefined,
    contact_type: contactType || undefined,
    sort_by: sortBy,
    sort_dir: sortDir,
  });

  const allIds = data?.items?.map((c) => c.id) ?? [];
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
    if (allSelected) setSelectedIds(new Set());
    else setSelectedIds(new Set(allIds));
  };

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return;
    const ok = await confirm({
      title: `${selectedIds.size} ${selectedIds.size === 1 ? "relatie" : "relaties"} verwijderen?`,
      description:
        "Relaties die aan een actief dossier gekoppeld zijn worden overgeslagen. Deze actie kan niet ongedaan worden gemaakt.",
      confirmText: "Verwijderen",
      cancelText: "Annuleren",
      variant: "destructive",
    });
    if (!ok) return;
    setBulkLoading(true);
    const ids = Array.from(selectedIds);
    let success = 0;
    let failed = 0;
    let firstError = "";
    for (const id of ids) {
      try {
        const res = await api(`/api/relations/${id}`, { method: "DELETE" });
        if (res.ok) {
          success++;
        } else {
          failed++;
          if (!firstError) {
            try {
              const body = await res.json();
              if (typeof body?.detail === "string") firstError = body.detail;
            } catch {
              // body niet JSON — laat generieke melding staan
            }
          }
        }
      } catch {
        failed++;
      }
    }
    if (failed === 0) {
      toast.success(`${success} ${success === 1 ? "relatie" : "relaties"} verwijderd`);
    } else if (success === 0) {
      toast.error(firstError || `Verwijderen mislukt voor alle ${failed} relaties`);
    } else {
      toast.warning(`${success} verwijderd, ${failed} mislukt${firstError ? ` — ${firstError}` : ""}`);
    }
    setSelectedIds(new Set());
    setBulkLoading(false);
    refetch();
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {ConfirmDialogEl}
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Relaties</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {data?.total
              ? `${data.total} ${data.total === 1 ? "relatie" : "relaties"}`
              : "Beheer je contacten en bedrijven"}
          </p>
        </div>
        <Link
          href="/relaties/nieuw"
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span className="hidden sm:inline">Nieuwe relatie</span>
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Zoek op naam, e-mail of KvK-nummer..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full rounded-lg border border-input bg-card pl-10 pr-4 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => {
              setContactType("");
              setPage(1);
            }}
            className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary/20 ${
              contactType === ""
                ? "bg-primary text-primary-foreground"
                : "border border-input bg-card text-muted-foreground hover:bg-muted"
            }`}
          >
            Alle
          </button>
          <button
            onClick={() => {
              setContactType("company");
              setPage(1);
            }}
            className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary/20 ${
              contactType === "company"
                ? "bg-primary text-primary-foreground"
                : "border border-input bg-card text-muted-foreground hover:bg-muted"
            }`}
          >
            <Building2 className="h-3.5 w-3.5" />
            Bedrijven
          </button>
          <button
            onClick={() => {
              setContactType("person");
              setPage(1);
            }}
            className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-primary/20 ${
              contactType === "person"
                ? "bg-primary text-primary-foreground"
                : "border border-input bg-card text-muted-foreground hover:bg-muted"
            }`}
          >
            <User className="h-3.5 w-3.5" />
            Personen
          </button>
        </div>
      </div>

      {/* Bulk action toolbar */}
      {someSelected && (
        <div className="flex items-center gap-3 rounded-lg border border-primary/20 bg-primary/5 px-4 py-3">
          <span className="text-sm font-medium text-primary">
            {selectedIds.size} {selectedIds.size === 1 ? "relatie" : "relaties"} geselecteerd
          </span>
          <div className="h-4 w-px bg-primary/20" />
          <button
            onClick={handleBulkDelete}
            disabled={bulkLoading}
            className="inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium text-destructive hover:bg-destructive/10 transition-colors"
          >
            {bulkLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
            Verwijderen
          </button>
          <button
            onClick={() => setSelectedIds(new Set())}
            className="ml-auto rounded-md p-1 text-primary/60 hover:text-primary transition-colors"
            aria-label="Selectie wissen"
          >
            <X className="h-4 w-4" />
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
                <div className="h-9 w-9 rounded-full skeleton" />
                <div className="h-4 w-32 rounded skeleton" />
                <div className="hidden md:block h-4 w-40 rounded skeleton" />
                <div className="hidden lg:block h-4 w-24 rounded skeleton" />
                <div className="hidden lg:block h-4 w-20 rounded skeleton" />
                <div className="h-4 w-16 rounded skeleton ml-auto" />
              </div>
            ))}
          </div>
        </div>
      ) : data?.items && data.items.length > 0 ? (
        <>
          {/* Mobile card view */}
          <div className="block sm:hidden space-y-3">
            {data.items.map((contact) => (
              <Link
                key={contact.id}
                href={`/relaties/${contact.id}`}
                className="block rounded-xl border border-border bg-card p-4 hover:border-primary/30 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
                      contact.contact_type === "company"
                        ? "bg-blue-50 text-blue-600"
                        : "bg-violet-50 text-violet-600"
                    }`}
                  >
                    {contact.contact_type === "company" ? (
                      <Building2 className="h-4 w-4" />
                    ) : (
                      <User className="h-4 w-4" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-foreground truncate">
                      {contact.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {contact.contact_type === "company" ? "Bedrijf" : "Persoon"}
                      {contact.kvk_number && ` · KvK ${contact.kvk_number}`}
                    </p>
                  </div>
                </div>
                <div className="mt-2.5 space-y-1 text-xs text-muted-foreground">
                  {contact.email && (
                    <div className="flex items-center gap-1.5">
                      <Mail className="h-3 w-3 shrink-0" />
                      <span className="truncate">{contact.email}</span>
                    </div>
                  )}
                  {contact.phone && (
                    <div className="flex items-center gap-1.5">
                      <Phone className="h-3 w-3 shrink-0" />
                      {contact.phone}
                    </div>
                  )}
                  {contact.visit_city && (
                    <div className="flex items-center gap-1.5">
                      <MapPin className="h-3 w-3 shrink-0" />
                      {contact.visit_city}
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>

          {/* Desktop table view */}
          <div className="hidden sm:block overflow-x-auto rounded-xl border border-border bg-card">
            <table className="w-full min-w-[700px]">
              <thead>
                <tr className="border-b border-border">
                  <th className="w-10 px-4 py-3.5">
                    <button
                      onClick={toggleSelectAll}
                      className="text-muted-foreground hover:text-foreground transition-colors"
                      aria-label="Selecteer alle relaties"
                    >
                      {allSelected ? (
                        <CheckSquare className="h-4 w-4 text-primary" />
                      ) : (
                        <Square className="h-4 w-4" />
                      )}
                    </button>
                  </th>
                  <th className="px-4 py-3.5 text-left">
                    <SortHeader
                      label="Relatie"
                      field="name"
                      activeField={sortBy}
                      direction={sortDir}
                      onToggle={toggleSort}
                    />
                  </th>
                  <th className="px-4 py-3.5 text-left">
                    <SortHeader
                      label="Contact"
                      field="email"
                      activeField={sortBy}
                      direction={sortDir}
                      onToggle={toggleSort}
                    />
                  </th>
                  <th className="hidden lg:table-cell px-4 py-3.5 text-left">
                    <SortHeader
                      label="Plaats"
                      field="visit_city"
                      activeField={sortBy}
                      direction={sortDir}
                      onToggle={toggleSort}
                    />
                  </th>
                  <th className="hidden md:table-cell px-4 py-3.5 text-left">
                    <SortHeader
                      label="Aangemaakt"
                      field="created_at"
                      activeField={sortBy}
                      direction={sortDir}
                      onToggle={toggleSort}
                    />
                  </th>
                  <th className="px-4 py-3.5 w-10" />
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.items.map((contact) => (
                  <tr
                    key={contact.id}
                    className="group hover:bg-muted/40 transition-colors"
                  >
                    <td className="w-10 px-4 py-3.5">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleSelect(contact.id);
                        }}
                        className="text-muted-foreground hover:text-foreground transition-colors"
                        aria-label={`Selecteer relatie ${contact.name}`}
                      >
                        {selectedIds.has(contact.id) ? (
                          <CheckSquare className="h-4 w-4 text-primary" />
                        ) : (
                          <Square className="h-4 w-4" />
                        )}
                      </button>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex items-center gap-3">
                        <div
                          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
                            contact.contact_type === "company"
                              ? "bg-blue-50 text-blue-600"
                              : "bg-violet-50 text-violet-600"
                          }`}
                        >
                          {contact.contact_type === "company" ? (
                            <Building2 className="h-4 w-4" />
                          ) : (
                            <User className="h-4 w-4" />
                          )}
                        </div>
                        <div className="min-w-0">
                          <Link
                            href={`/relaties/${contact.id}`}
                            className="text-sm font-semibold text-foreground hover:text-primary transition-colors"
                          >
                            {contact.name}
                          </Link>
                          <p className="text-xs text-muted-foreground">
                            {contact.contact_type === "company"
                              ? "Bedrijf"
                              : "Persoon"}
                            {contact.kvk_number &&
                              ` · KvK ${contact.kvk_number}`}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="space-y-1">
                        {contact.email && (
                          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                            <Mail className="h-3 w-3 shrink-0" />
                            <span className="truncate max-w-[200px]">
                              {contact.email}
                            </span>
                          </div>
                        )}
                        {contact.phone && (
                          <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                            <Phone className="h-3 w-3 shrink-0" />
                            {contact.phone}
                          </div>
                        )}
                        {!contact.email && !contact.phone && (
                          <span className="text-sm text-muted-foreground/50">
                            -
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="hidden lg:table-cell px-4 py-3.5">
                      {contact.visit_city ? (
                        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                          <MapPin className="h-3 w-3 shrink-0" />
                          {contact.visit_city}
                        </div>
                      ) : (
                        <span className="text-sm text-muted-foreground/50">
                          -
                        </span>
                      )}
                    </td>
                    <td className="hidden md:table-cell px-4 py-3.5 text-sm text-muted-foreground">
                      {formatDateShort(contact.created_at)}
                    </td>
                    <td className="px-4 py-3.5">
                      <Link
                        href={`/relaties/${contact.id}`}
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
                Pagina {page} van {data.pages} &middot; {data.total} relaties
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
            <Users className="h-8 w-8 text-muted-foreground/50" />
          </div>
          <p className="mt-5 text-base font-medium text-foreground">
            Geen relaties gevonden
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            {search || contactType
              ? "Probeer andere zoektermen of filters"
              : "Begin met het toevoegen van je eerste relatie"}
          </p>
          <Link
            href="/relaties/nieuw"
            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Nieuwe relatie toevoegen
          </Link>
        </div>
      )}
    </div>
  );
}
