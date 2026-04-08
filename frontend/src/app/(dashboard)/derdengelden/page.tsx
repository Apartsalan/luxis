"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  PiggyBank,
  Users,
  Clock,
  Search,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  ArrowUpRight,
} from "lucide-react";
import {
  useTrustFundsOverview,
  type ClientTrustOverview,
} from "@/hooks/use-collections";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import { QueryError } from "@/components/query-error";

export default function DerdengeldenPage() {
  const [onlyNonzero, setOnlyNonzero] = useState(true);
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const { data, isLoading, isError, error, refetch } =
    useTrustFundsOverview(onlyNonzero);

  const filtered = useMemo<ClientTrustOverview[]>(() => {
    if (!data?.clients) return [];
    if (!search.trim()) return data.clients;
    const q = search.toLowerCase();
    return data.clients.filter((c) => c.contact_name.toLowerCase().includes(q));
  }, [data, search]);

  const toggleExpand = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  if (isError) {
    return (
      <QueryError
        message={error instanceof Error ? error.message : undefined}
        onRetry={refetch}
      />
    );
  }

  const totals = data?.totals;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <PiggyBank className="h-6 w-6 text-primary" />
            <h1 className="text-2xl font-bold text-foreground">Derdengelden</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Overzicht van saldi per cliënt op de Stichting Derdengelden rekening
          </p>
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard
          label="Totaal saldo"
          value={totals ? formatCurrency(totals.total_balance) : "—"}
          icon={<PiggyBank className="h-5 w-5" />}
          accent="primary"
          loading={isLoading}
        />
        <KpiCard
          label="Cliënten met saldo"
          value={totals ? String(totals.client_count) : "—"}
          icon={<Users className="h-5 w-5" />}
          loading={isLoading}
        />
        <KpiCard
          label="Dossiers"
          value={totals ? String(totals.case_count) : "—"}
          icon={<ArrowUpRight className="h-5 w-5" />}
          loading={isLoading}
        />
        <KpiCard
          label="Wachten op goedkeuring"
          value={totals ? String(totals.pending_approval_count) : "—"}
          icon={<AlertCircle className="h-5 w-5" />}
          accent={
            totals && totals.pending_approval_count > 0 ? "warning" : undefined
          }
          loading={isLoading}
        />
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Zoek cliënt..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer select-none">
          <input
            type="checkbox"
            checked={onlyNonzero}
            onChange={(e) => setOnlyNonzero(e.target.checked)}
            className="h-4 w-4 rounded border-border"
          />
          Alleen cliënten met saldo
        </label>
      </div>

      {/* Client list */}
      <div className="bg-card rounded-lg border border-border overflow-hidden">
        {isLoading ? (
          <div className="p-10 text-center text-muted-foreground text-sm">
            Laden...
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState onlyNonzero={onlyNonzero} />
        ) : (
          <div className="divide-y divide-border">
            {filtered.map((client) => (
              <ClientRow
                key={client.contact_id}
                client={client}
                expanded={expanded.has(client.contact_id)}
                onToggle={() => toggleExpand(client.contact_id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Sub-components ───────────────────────────────────────────────────────────

function KpiCard({
  label,
  value,
  icon,
  accent,
  loading,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  accent?: "primary" | "warning";
  loading?: boolean;
}) {
  const accentClass =
    accent === "primary"
      ? "text-primary"
      : accent === "warning"
      ? "text-amber-600"
      : "text-muted-foreground";
  return (
    <div className="bg-card rounded-lg border border-border p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {label}
        </span>
        <span className={accentClass}>{icon}</span>
      </div>
      <p
        className={`mt-2 text-2xl font-bold ${
          loading ? "text-muted-foreground/30" : "text-foreground"
        }`}
      >
        {loading ? "•••" : value}
      </p>
    </div>
  );
}

function ClientRow({
  client,
  expanded,
  onToggle,
}: {
  client: ClientTrustOverview;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div>
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-muted/30 transition-colors text-left"
      >
        <div className="flex items-center gap-3 min-w-0 flex-1">
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
          )}
          <div className="min-w-0">
            <div className="font-medium text-foreground truncate">
              {client.contact_name}
            </div>
            <div className="text-xs text-muted-foreground">
              {client.case_count}{" "}
              {client.case_count === 1 ? "dossier" : "dossiers"}
              {client.pending_disbursements > 0 && (
                <span className="ml-2 text-amber-600">
                  • {formatCurrency(client.pending_disbursements)} in afwachting
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="text-right shrink-0 ml-4">
          <div
            className={`font-semibold ${
              client.total_balance > 0
                ? "text-foreground"
                : "text-muted-foreground"
            }`}
          >
            {formatCurrency(client.total_balance)}
          </div>
        </div>
      </button>

      {expanded && (
        <div className="bg-muted/20 border-t border-border">
          <table className="w-full text-sm">
            <thead className="text-xs text-muted-foreground">
              <tr>
                <th className="text-left font-medium px-4 py-2">Dossier</th>
                <th className="text-left font-medium px-4 py-2">
                  Laatste mutatie
                </th>
                <th className="text-right font-medium px-4 py-2">
                  In afwachting
                </th>
                <th className="text-right font-medium px-4 py-2">Saldo</th>
                <th className="w-8"></th>
              </tr>
            </thead>
            <tbody>
              {client.cases.map((c) => (
                <tr
                  key={c.case_id}
                  className="border-t border-border hover:bg-background/60"
                >
                  <td className="px-4 py-2">
                    <div className="font-mono text-xs text-muted-foreground">
                      {c.case_number}
                    </div>
                    {c.case_description && (
                      <div className="text-xs text-muted-foreground/80 truncate max-w-xs">
                        {c.case_description}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">
                    {c.last_transaction_date
                      ? formatDateShort(c.last_transaction_date)
                      : "—"}
                  </td>
                  <td className="px-4 py-2 text-right">
                    {c.pending_disbursements > 0 ? (
                      <span className="text-amber-600">
                        {formatCurrency(c.pending_disbursements)}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-right font-medium">
                    {formatCurrency(c.total_balance)}
                  </td>
                  <td className="px-4 py-2">
                    <Link
                      href={`/zaken/${c.case_id}`}
                      className="text-primary hover:text-primary/80 inline-flex"
                      title="Open dossier"
                    >
                      <ArrowUpRight className="h-4 w-4" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function EmptyState({ onlyNonzero }: { onlyNonzero: boolean }) {
  return (
    <div className="p-10 text-center">
      <PiggyBank className="h-10 w-10 text-muted-foreground/40 mx-auto mb-3" />
      <p className="text-sm text-muted-foreground">
        {onlyNonzero
          ? "Geen cliënten met actief derdengeldensaldo."
          : "Geen derdengelden-transacties gevonden."}
      </p>
      <p className="text-xs text-muted-foreground/60 mt-2">
        Stortingen en uitbetalingen worden geregistreerd vanuit een dossier.
      </p>
    </div>
  );
}
