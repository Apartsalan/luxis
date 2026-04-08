"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  PiggyBank,
  Users,
  Search,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  ArrowUpRight,
  Download,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";
import {
  useTrustFundsOverview,
  useSepaPending,
  type ClientTrustOverview,
  type SepaPendingTransaction,
} from "@/hooks/use-collections";
import { toast } from "sonner";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import { QueryError } from "@/components/query-error";

export default function DerdengeldenPage() {
  const [activeTab, setActiveTab] = useState<"overview" | "sepa">("overview");
  const [onlyNonzero, setOnlyNonzero] = useState(true);
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [reportDialog, setReportDialog] = useState<
    null | "mutaties" | "saldolijst"
  >(null);

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
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2">
            <PiggyBank className="h-6 w-6 text-primary" />
            <h1 className="text-2xl font-bold text-foreground">Derdengelden</h1>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Overzicht van saldi per cliënt op de Stichting Derdengelden rekening
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setReportDialog("mutaties")}
            className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-muted transition-colors"
          >
            <Download className="h-4 w-4" />
            Mutatieoverzicht
          </button>
          <button
            onClick={() => setReportDialog("saldolijst")}
            className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-muted transition-colors"
          >
            <Download className="h-4 w-4" />
            Saldolijst
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border">
        <div className="flex gap-6">
          <TabButton
            active={activeTab === "overview"}
            onClick={() => setActiveTab("overview")}
            label="Cliëntoverzicht"
          />
          <TabButton
            active={activeTab === "sepa"}
            onClick={() => setActiveTab("sepa")}
            label="SEPA-uitbetalingen"
          />
        </div>
      </div>

      {/* Report dialog */}
      {reportDialog && (
        <ReportDialog
          kind={reportDialog}
          onClose={() => setReportDialog(null)}
        />
      )}

      {activeTab === "sepa" ? (
        <SepaTab />
      ) : (
        <>
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
        </>
      )}
    </div>
  );
}

// ── Sub-components ───────────────────────────────────────────────────────────

function TabButton({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`pb-3 -mb-px text-sm font-medium border-b-2 transition-colors ${
        active
          ? "border-primary text-foreground"
          : "border-transparent text-muted-foreground hover:text-foreground"
      }`}
    >
      {label}
    </button>
  );
}

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

function SepaTab() {
  const qc = useQueryClient();
  const [includeExported, setIncludeExported] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [executionDate, setExecutionDate] = useState(
    new Date().toISOString().slice(0, 10)
  );
  const [downloading, setDownloading] = useState(false);
  const { data, isLoading, isError, refetch } = useSepaPending(includeExported);

  const transactions = data || [];
  const exportable = transactions.filter((t) => !t.sepa_exported_at);

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === exportable.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(exportable.map((t) => t.id)));
    }
  };

  const selectedTotal = transactions
    .filter((t) => selected.has(t.id))
    .reduce((sum, t) => sum + Number(t.amount), 0);

  const handleExport = async () => {
    if (selected.size === 0) {
      toast.error("Selecteer minstens één uitbetaling");
      return;
    }
    setDownloading(true);
    try {
      const res = await api("/api/trust-funds/sepa/export", {
        method: "POST",
        body: JSON.stringify({
          transaction_ids: Array.from(selected),
          execution_date: executionDate,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `SEPA-export mislukt (${res.status})`);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `sepa-derdengelden-${executionDate}.xml`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success(`${selected.size} uitbetalingen geëxporteerd`);
      setSelected(new Set());
      qc.invalidateQueries({ queryKey: ["trust-funds", "sepa"] });
      qc.invalidateQueries({ queryKey: ["trust-funds", "overview"] });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Onbekende fout");
    } finally {
      setDownloading(false);
    }
  };

  if (isError) {
    return (
      <QueryError
        message="Kan SEPA-uitbetalingen niet laden"
        onRetry={refetch}
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Action bar */}
      <div className="bg-card rounded-lg border border-border p-4 flex flex-col lg:flex-row gap-4 lg:items-end lg:justify-between">
        <div>
          <h2 className="text-sm font-semibold text-foreground">
            SEPA-batch genereren
          </h2>
          <p className="text-xs text-muted-foreground mt-1">
            Selecteer goedgekeurde uitbetalingen, kies de uitvoerdatum en
            download het XML-bestand voor upload in de Rabobank-portal.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-end">
          <div>
            <label className="text-xs font-medium text-muted-foreground block">
              Uitvoerdatum
            </label>
            <input
              type="date"
              value={executionDate}
              onChange={(e) => setExecutionDate(e.target.value)}
              className="mt-1 rounded-md border border-border px-3 py-2 text-sm bg-background"
            />
          </div>
          <button
            onClick={handleExport}
            disabled={downloading || selected.size === 0}
            className="rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
          >
            {downloading
              ? "Bezig..."
              : `Download SEPA (${selected.size} geselecteerd${
                  selected.size > 0 ? ` — ${formatCurrency(selectedTotal)}` : ""
                })`}
          </button>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer select-none">
          <input
            type="checkbox"
            checked={includeExported}
            onChange={(e) => setIncludeExported(e.target.checked)}
            className="h-4 w-4 rounded border-border"
          />
          Toon ook reeds geëxporteerde batches
        </label>
        {exportable.length > 0 && (
          <button
            onClick={toggleAll}
            className="text-xs text-primary hover:underline"
          >
            {selected.size === exportable.length
              ? "Niets selecteren"
              : "Alles selecteren"}
          </button>
        )}
      </div>

      <div className="bg-card rounded-lg border border-border overflow-hidden">
        {isLoading ? (
          <div className="p-10 text-center text-muted-foreground text-sm">
            Laden...
          </div>
        ) : transactions.length === 0 ? (
          <div className="p-10 text-center">
            <PiggyBank className="h-10 w-10 text-muted-foreground/40 mx-auto mb-3" />
            <p className="text-sm text-muted-foreground">
              Geen uitbetalingen klaar voor SEPA-export.
            </p>
            <p className="text-xs text-muted-foreground/60 mt-2">
              Goedgekeurde uitbetalingen verschijnen hier automatisch.
            </p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-muted/30 text-xs text-muted-foreground">
              <tr>
                <th className="w-10 px-3 py-2"></th>
                <th className="text-left font-medium px-3 py-2">Datum</th>
                <th className="text-left font-medium px-3 py-2">Cliënt</th>
                <th className="text-left font-medium px-3 py-2">Begunstigde</th>
                <th className="text-left font-medium px-3 py-2">IBAN</th>
                <th className="text-right font-medium px-3 py-2">Bedrag</th>
                <th className="text-left font-medium px-3 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => (
                <SepaRow
                  key={tx.id}
                  tx={tx}
                  selected={selected.has(tx.id)}
                  onToggle={() => toggleSelect(tx.id)}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function SepaRow({
  tx,
  selected,
  onToggle,
}: {
  tx: SepaPendingTransaction;
  selected: boolean;
  onToggle: () => void;
}) {
  const exported = tx.sepa_exported_at !== null;
  return (
    <tr
      className={`border-t border-border ${
        exported ? "bg-muted/20 text-muted-foreground" : "hover:bg-muted/20"
      }`}
    >
      <td className="px-3 py-2">
        <input
          type="checkbox"
          checked={selected}
          disabled={exported}
          onChange={onToggle}
          className="h-4 w-4 rounded border-border"
        />
      </td>
      <td className="px-3 py-2 whitespace-nowrap">
        {formatDateShort(tx.transaction_date)}
      </td>
      <td className="px-3 py-2">{tx.contact_name}</td>
      <td className="px-3 py-2">{tx.beneficiary_name || "—"}</td>
      <td className="px-3 py-2 font-mono text-xs">
        {tx.beneficiary_iban || "—"}
      </td>
      <td className="px-3 py-2 text-right font-medium">
        {formatCurrency(tx.amount)}
      </td>
      <td className="px-3 py-2">
        {exported ? (
          <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs">
            Geëxporteerd
          </span>
        ) : (
          <span className="inline-flex items-center rounded-full bg-emerald-500/10 text-emerald-600 px-2 py-0.5 text-xs">
            Klaar
          </span>
        )}
      </td>
    </tr>
  );
}

function ReportDialog({
  kind,
  onClose,
}: {
  kind: "mutaties" | "saldolijst";
  onClose: () => void;
}) {
  const today = new Date().toISOString().slice(0, 10);
  const yearStart = today.slice(0, 4) + "-01-01";
  const [from, setFrom] = useState(yearStart);
  const [to, setTo] = useState(today);
  const [peildatum, setPeildatum] = useState(today);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async () => {
    setDownloading(true);
    setError(null);
    try {
      const url =
        kind === "mutaties"
          ? `/api/trust-funds/reports/mutaties.csv?from=${from}&to=${to}`
          : `/api/trust-funds/reports/saldolijst.csv?date=${peildatum}`;
      const res = await api(url);
      if (!res.ok) {
        throw new Error(`Download mislukt (${res.status})`);
      }
      const blob = await res.blob();
      const filename =
        kind === "mutaties"
          ? `derdengelden-mutaties_${from}_${to}.csv`
          : `derdengelden-saldolijst_${peildatum}.csv`;
      const downloadUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(downloadUrl);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Onbekende fout");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="bg-card rounded-lg border border-border shadow-xl w-full max-w-md p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-foreground">
              {kind === "mutaties"
                ? "Mutatieoverzicht downloaden"
                : "Saldolijst downloaden"}
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              {kind === "mutaties"
                ? "Alle derdengeldenmutaties in de geselecteerde periode (CSV)"
                : "Saldo per cliënt op de geselecteerde peildatum (CSV)"}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
            aria-label="Sluiten"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-3">
          {kind === "mutaties" ? (
            <>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Van
                </label>
                <input
                  type="date"
                  value={from}
                  onChange={(e) => setFrom(e.target.value)}
                  className="mt-1 w-full rounded-md border border-border px-3 py-2 text-sm bg-background"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Tot en met
                </label>
                <input
                  type="date"
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                  className="mt-1 w-full rounded-md border border-border px-3 py-2 text-sm bg-background"
                />
              </div>
            </>
          ) : (
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Peildatum
              </label>
              <input
                type="date"
                value={peildatum}
                onChange={(e) => setPeildatum(e.target.value)}
                className="mt-1 w-full rounded-md border border-border px-3 py-2 text-sm bg-background"
              />
            </div>
          )}
        </div>

        {error && (
          <p className="mt-3 text-xs text-destructive">{error}</p>
        )}

        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-md border border-border px-4 py-2 text-sm hover:bg-muted"
          >
            Annuleren
          </button>
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="rounded-md bg-primary text-primary-foreground px-4 py-2 text-sm font-medium hover:bg-primary/90 disabled:opacity-60"
          >
            {downloading ? "Bezig..." : "Download CSV"}
          </button>
        </div>
      </div>
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
