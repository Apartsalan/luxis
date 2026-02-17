"use client";

import { useState } from "react";
import Link from "next/link";
import { Plus, Search, Briefcase } from "lucide-react";
import { useCases } from "@/hooks/use-cases";
import { formatCurrency, formatDateShort } from "@/lib/utils";

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
  betaald: "bg-green-100 text-green-700",
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

  const { data, isLoading } = useCases({
    page,
    case_type: caseType || undefined,
    status: status || undefined,
    search: search || undefined,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-navy-800">Zaken</h1>
          <p className="text-sm text-muted-foreground">
            Beheer je zaken en dossiers
          </p>
        </div>
        <Link
          href="/zaken/nieuw"
          className="inline-flex items-center gap-2 rounded-md bg-navy-500 px-4 py-2 text-sm font-medium text-white hover:bg-navy-600 transition-colors"
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
            className="w-full rounded-md border border-input bg-white pl-10 pr-4 py-2 text-sm focus:border-navy-500 focus:outline-none focus:ring-1 focus:ring-navy-500"
          />
        </div>
        <select
          value={caseType}
          onChange={(e) => {
            setCaseType(e.target.value);
            setPage(1);
          }}
          className="rounded-md border border-input bg-white px-3 py-2 text-sm"
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
          className="rounded-md border border-input bg-white px-3 py-2 text-sm"
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
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-navy-200 border-t-navy-500" />
        </div>
      ) : data?.items && data.items.length > 0 ? (
        <>
          <div className="overflow-hidden rounded-lg border border-border bg-white">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                    Zaaknummer
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                    Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                    Status
                  </th>
                  <th className="hidden px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground md:table-cell">
                    Client
                  </th>
                  <th className="hidden px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground lg:table-cell">
                    Wederpartij
                  </th>
                  <th className="hidden px-4 py-3 text-right text-xs font-medium uppercase text-muted-foreground md:table-cell">
                    Hoofdsom
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
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
                        className="font-mono font-medium text-navy-700 hover:text-navy-500 hover:underline"
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
                          STATUS_COLORS[zaak.status] ?? "bg-gray-100 text-gray-600"
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
                    <td className="hidden px-4 py-3 text-right text-sm font-medium text-navy-700 md:table-cell">
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
                  className="rounded-md border border-border px-3 py-1 text-sm disabled:opacity-50"
                >
                  Vorige
                </button>
                <span className="flex items-center px-3 text-sm text-muted-foreground">
                  {page} / {data.pages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                  disabled={page === data.pages}
                  className="rounded-md border border-border px-3 py-1 text-sm disabled:opacity-50"
                >
                  Volgende
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-12">
          <Briefcase className="h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-sm text-muted-foreground">
            Geen zaken gevonden
          </p>
          <Link
            href="/zaken/nieuw"
            className="mt-2 text-sm font-medium text-navy-500 hover:underline"
          >
            Maak je eerste zaak aan
          </Link>
        </div>
      )}
    </div>
  );
}
