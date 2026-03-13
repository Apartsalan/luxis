"use client";

import { useState } from "react";
import Link from "next/link";
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
  Briefcase,
} from "lucide-react";
import { useRelations } from "@/hooks/use-relations";
import { formatDateShort } from "@/lib/utils";
import { QueryError } from "@/components/query-error";

export default function RelatiesPage() {
  const [search, setSearch] = useState("");
  const [contactType, setContactType] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, error, refetch } = useRelations({
    page,
    search: search || undefined,
    contact_type: contactType || undefined,
  });

  return (
    <div className="space-y-6 animate-fade-in">
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
          <div className="overflow-x-auto rounded-xl border border-border bg-card">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Relatie
                  </th>
                  <th className="hidden md:table-cell px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Contact
                  </th>
                  <th className="hidden lg:table-cell px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Plaats
                  </th>
                  <th className="hidden sm:table-cell px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Aangemaakt
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
                    <td className="hidden md:table-cell px-4 py-3.5">
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
                    <td className="hidden sm:table-cell px-4 py-3.5 text-sm text-muted-foreground">
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
