"use client";

import { useState } from "react";
import Link from "next/link";
import { Plus, Search, Building2, User, Mail, Phone } from "lucide-react";
import { useRelations } from "@/hooks/use-relations";
import { formatDateShort } from "@/lib/utils";

export default function RelatiesPage() {
  const [search, setSearch] = useState("");
  const [contactType, setContactType] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useRelations({
    page,
    search: search || undefined,
    contact_type: contactType || undefined,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-navy-800">Relaties</h1>
          <p className="text-sm text-muted-foreground">
            Beheer je contacten en bedrijven
          </p>
        </div>
        <Link
          href="/relaties/nieuw"
          className="inline-flex items-center gap-2 rounded-md bg-navy-500 px-4 py-2 text-sm font-medium text-white hover:bg-navy-600 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Nieuwe relatie
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-3 sm:flex-row">
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
            className="w-full rounded-md border border-input bg-white pl-10 pr-4 py-2 text-sm focus:border-navy-500 focus:outline-none focus:ring-1 focus:ring-navy-500"
          />
        </div>
        <select
          value={contactType}
          onChange={(e) => {
            setContactType(e.target.value);
            setPage(1);
          }}
          className="rounded-md border border-input bg-white px-3 py-2 text-sm focus:border-navy-500 focus:outline-none focus:ring-1 focus:ring-navy-500"
        >
          <option value="">Alle types</option>
          <option value="company">Bedrijven</option>
          <option value="person">Personen</option>
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
                    Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                    Naam
                  </th>
                  <th className="hidden px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground md:table-cell">
                    E-mail
                  </th>
                  <th className="hidden px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground lg:table-cell">
                    Telefoon
                  </th>
                  <th className="hidden px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground lg:table-cell">
                    Plaats
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium uppercase text-muted-foreground">
                    Aangemaakt
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.items.map((contact) => (
                  <tr
                    key={contact.id}
                    className="hover:bg-muted/30 transition-colors"
                  >
                    <td className="px-4 py-3">
                      {contact.contact_type === "company" ? (
                        <Building2 className="h-4 w-4 text-navy-400" />
                      ) : (
                        <User className="h-4 w-4 text-navy-400" />
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/relaties/${contact.id}`}
                        className="font-medium text-navy-700 hover:text-navy-500 hover:underline"
                      >
                        {contact.name}
                      </Link>
                    </td>
                    <td className="hidden px-4 py-3 text-sm text-muted-foreground md:table-cell">
                      {contact.email && (
                        <span className="inline-flex items-center gap-1">
                          <Mail className="h-3 w-3" />
                          {contact.email}
                        </span>
                      )}
                    </td>
                    <td className="hidden px-4 py-3 text-sm text-muted-foreground lg:table-cell">
                      {contact.phone && (
                        <span className="inline-flex items-center gap-1">
                          <Phone className="h-3 w-3" />
                          {contact.phone}
                        </span>
                      )}
                    </td>
                    <td className="hidden px-4 py-3 text-sm text-muted-foreground lg:table-cell">
                      {contact.visit_city}
                    </td>
                    <td className="px-4 py-3 text-sm text-muted-foreground">
                      {formatDateShort(contact.created_at)}
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
                {data.total} resultaten
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
          <Users className="h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-sm text-muted-foreground">
            Geen relaties gevonden
          </p>
          <Link
            href="/relaties/nieuw"
            className="mt-2 text-sm font-medium text-navy-500 hover:underline"
          >
            Voeg je eerste relatie toe
          </Link>
        </div>
      )}
    </div>
  );
}

function Users(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  );
}
