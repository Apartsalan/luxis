"use client";

import { useState } from "react";
import Link from "next/link";
import { Plus, Search, Briefcase } from "lucide-react";
import { useCases } from "@/hooks/use-cases";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import { QueryError } from "@/components/query-error";

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

const STATUS_COLORS: Record<string, string> = {
  nieuw: "bg-blue-100 text-blue-700",
  "14_dagenbrief": "bg-yellow-100 text-yellow-700",
  sommatie: "bg-orange-100 text-orange-700",
  dagvaarding: "bg-red-100 text-red-700",
  vonnis: "bg-purple-100 text-purple-700",
  executie: "bg-red-200 text-red-800",
  betaald: "bg-emerald-100 text-emerald-700",
  afgesloten: "bg-gray-100 text-gray-600",
};

const TYPE_LABELS: Record<string, string> = {
  incasso: "Incasso",
  insolventie: "Insolventie",
  advies: "Advies",
  overig: "Overig",
};

export default function ZakenPage() {
  const [search, setSearch] = useState("");
  const [caseType, setCaseType] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, error, refetch } = useCases({
    page,
    case_type: caseType || undefined,
    status: status || undefined,
    search: search || undefined,
  });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Zaken</h1>
          <p className="text-sm text-muted-foreground">
            Beheer je zaken en dossiers
          </p>
        </div>
        <Link
          href="/zaken/nieuw"
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Nieuwe zaak
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Zoek op zaaknummer of beschrijving..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full rounded-lg border border-input bg-card pl-10 pr-4 py-2 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
          />
        </div>
        <select
          value={caseType}
          onChange={(e) => {
            setCaseType(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-input bg-card px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
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
          className="rounded-lg border border-input bg-card px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
        >
          <option value="">Alle statussen</option>
          {Object.entries(STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {/* Table */}
      {isError ? (
        <QueryError
          message={error?.message}
          onRetry={() => refetch()}
        />
      ) : isLoading ? (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-14 rounded-lg skeleton" />
          ))}
        </div>
      ) : data?.items && data.items.length > 0 ? (
        <>
          <div className="overflow-hidden rounded-xl border border-border bg-card">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/30">
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Zaaknummer
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Status
                  </th>
                  <th className="hidden px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground md:table-cell">
                    Client
                  </th>
                  <th className="hidden px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground lg:table-cell">
                    Wederpartij
                  </th>
                  <th className="hidden px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground md:table-cell">
                    Hoofdsom
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Geopend
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.items.map((zaak) => (
                  <tr
                    key={zaak.id}
                    className="hover:bg-muted/30 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <Link
                        href={`/zaken/${zaak.id}`}
                        className="font-mono text-sm font-medium text-foreground hover:text-primary hover:underline"
                      >
                        {zaak.case_number}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {TYPE_LABELS[zaak.case_type] ?? zaak.case_type}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          STATUS_COLORS[zaak.status] ??
                          "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {STATUS_LABELS[zaak.status] ?? zaak.status}
                      </span>
                    </td>
                    <td className="hidden px-4 py-3 text-sm text-muted-foreground md:table-cell">
                      {zaak.client?.name}
                    </td>
                    <td className="hidden px-4 py-3 text-sm text-muted-foreground lg:table-cell">
                      {zaak.opposing_party?.name ?? "-"}
                    </td>
                    <td className="hidden px-4 py-3 text-right text-sm font-medium text-foreground md:table-cell">
                      {formatCurrency(zaak.total_principal)}
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {formatDateShort(zaak.date_opened)}
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
                {data.total} zaken
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="rounded-lg border border-border px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:opacity-50 transition-colors"
                >
                  Vorige
                </button>
                <span className="flex items-center px-3 text-sm text-muted-foreground">
                  {page} / {data.pages}
                </span>
                <button
                  onClick={() =>
                    setPage((p) => Math.min(data.pages, p + 1))
                  }
                  disabled={page === data.pages}
                  className="rounded-lg border border-border px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:opacity-50 transition-colors"
                >
                  Volgende
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-16">
          <Briefcase className="h-12 w-12 text-muted-foreground/30" />
          <p className="mt-4 text-sm font-medium text-muted-foreground">
            Geen zaken gevonden
          </p>
          <Link
            href="/zaken/nieuw"
            className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
          >
            <Plus className="h-3.5 w-3.5" />
            Maak je eerste zaak aan
          </Link>
        </div>
      )}
    </div>
  );
}
