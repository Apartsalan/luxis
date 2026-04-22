"use client";

import { useState, useEffect } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Euro,
  Loader2,
  Pencil,
  Receipt,
  Save,
  Wallet,
} from "lucide-react";
import { toast } from "sonner";
import { useFinancialSummary } from "@/hooks/use-collections";
import { useCase, useUpdateCase } from "@/hooks/use-cases";
import { useRelation } from "@/hooks/use-relations";
import { formatCurrency, formatDate } from "@/lib/utils";
import { QueryError } from "@/components/query-error";

type BikMode = "wik" | "amount" | "percentage";

export function FinancieelTab({ caseId }: { caseId: string }) {
  const { data: summary, isLoading, isError, error, refetch } = useFinancialSummary(caseId);
  const { data: caseData } = useCase(caseId);
  const { data: clientContact } = useRelation(caseData?.client?.id);
  const updateCase = useUpdateCase();
  const [bikMode, setBikMode] = useState<BikMode>("wik");
  const [bikOverride, setBikOverride] = useState<string>("");
  const [bikPercentage, setBikPercentage] = useState<string>("");
  const [bikSaved, setBikSaved] = useState(false);

  // Initialize from persisted values: percentage takes precedence over fixed amount
  useEffect(() => {
    if (caseData?.bik_override_percentage != null) {
      setBikMode("percentage");
      setBikPercentage(String(caseData.bik_override_percentage));
      setBikSaved(true);
    } else if (caseData?.bik_override != null) {
      setBikMode("amount");
      setBikOverride(String(caseData.bik_override));
      setBikSaved(true);
    } else {
      setBikMode("wik");
      setBikSaved(true);
    }
  }, [caseData?.bik_override, caseData?.bik_override_percentage]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-28 rounded-xl skeleton" />
          ))}
        </div>
        <div className="h-6 rounded-lg skeleton" />
        <div className="h-48 rounded-xl skeleton" />
      </div>
    );
  }

  if (isError) return <QueryError message={error?.message} onRetry={refetch} />;

  if (!summary) return null;

  // Compute the effective BIK amount based on the selected mode
  let bikOverrideAmount: number | null = null;
  if (bikMode === "amount" && bikOverride !== "") {
    const v = parseFloat(bikOverride);
    bikOverrideAmount = isNaN(v) ? null : v;
  } else if (bikMode === "percentage" && bikPercentage !== "") {
    const pct = parseFloat(bikPercentage);
    if (!isNaN(pct) && summary.total_principal > 0) {
      bikOverrideAmount = Math.round(summary.total_principal * pct) / 100;
    }
  }
  const effectiveBik = bikOverrideAmount !== null && !isNaN(bikOverrideAmount) ? bikOverrideAmount : summary.total_bik;
  const bikDiff = effectiveBik - summary.total_bik;
  const bikManual = bikMode !== "wik";

  // DF117-22: detect when the current case BIK matches the client default
  // (i.e. it was inherited and not yet overridden on the case).
  const clientHasBikDefault =
    clientContact?.default_bik_override != null ||
    clientContact?.default_bik_override_percentage != null;
  const isInheritedFromClient =
    bikSaved &&
    clientHasBikDefault &&
    ((bikMode === "percentage" &&
      caseData?.bik_override_percentage != null &&
      Number(caseData.bik_override_percentage) ===
        Number(clientContact?.default_bik_override_percentage)) ||
      (bikMode === "amount" &&
        caseData?.bik_override != null &&
        Number(caseData.bik_override) ===
          Number(clientContact?.default_bik_override)));
  const effectiveGrandTotal = summary.grand_total + bikDiff;
  const effectiveOutstanding = summary.total_outstanding + bikDiff;
  const effectiveRemainingCosts = summary.remaining_costs + bikDiff;

  const paidPercent = effectiveGrandTotal > 0
    ? Math.min(100, Math.round((summary.total_paid / effectiveGrandTotal) * 100))
    : 0;

  const rows = [
    { label: "Hoofdsom", total: summary.total_principal, paid: summary.total_paid_principal, open: summary.remaining_principal },
    { label: "Rente", total: summary.total_interest, paid: summary.total_paid_interest, open: summary.remaining_interest },
    {
      label: summary.total_nakosten > 0
        ? (bikOverrideAmount !== null && !isNaN(bikOverrideAmount)
            ? "Kosten (handm. BIK + nakosten)"
            : summary.bik_btw > 0 ? "Kosten (BIK incl. BTW + nakosten)" : "Kosten (BIK + nakosten)")
        : (bikOverrideAmount !== null && !isNaN(bikOverrideAmount)
            ? "Incassokosten (handmatig)"
            : summary.bik_btw > 0 ? "BIK incl. BTW" : "BIK (art. 6:96 BW)"),
      total: effectiveBik + (summary.total_nakosten || 0),
      paid: summary.total_paid_costs,
      open: effectiveRemainingCosts,
    },
  ];

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-muted-foreground mb-1">
            <Receipt className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Totale vordering</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-foreground">
            {formatCurrency(effectiveGrandTotal)}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Hoofdsom + rente + kosten
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-emerald-600 mb-1">
            <CheckCircle2 className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Betaald</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-emerald-600">
            {formatCurrency(summary.total_paid)}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            {paidPercent}% van totaal
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center gap-2 text-amber-600 mb-1">
            <AlertTriangle className="h-4 w-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Openstaand</span>
          </div>
          <p className="text-2xl font-bold tabular-nums text-amber-600">
            {formatCurrency(effectiveOutstanding)}
          </p>
          {summary.derdengelden_balance > 0 && (
            <p className="text-xs text-muted-foreground mt-1">
              Derdengelden: {formatCurrency(summary.derdengelden_balance)}
            </p>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-muted-foreground">Betalingsvoortgang</span>
          <span className="text-xs font-semibold text-foreground tabular-nums">{paidPercent}%</span>
        </div>
        <div className="h-2.5 rounded-full bg-muted overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              paidPercent >= 100 ? "bg-emerald-500" : paidPercent >= 50 ? "bg-emerald-500" : "bg-amber-500"
            }`}
            style={{ width: `${paidPercent}%` }}
          />
        </div>
        <div className="flex justify-between mt-1.5">
          <span className="text-[10px] text-emerald-600 tabular-nums">{formatCurrency(summary.total_paid)} betaald</span>
          <span className="text-[10px] text-muted-foreground tabular-nums">{formatCurrency(effectiveGrandTotal)} totaal</span>
        </div>
      </div>

      {/* BIK override */}
      <div className="rounded-xl border border-border bg-card p-5 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Wallet className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Incassokosten</h3>
          </div>
          {bikManual && !bikSaved && (
            <button
              type="button"
              onClick={async () => {
                try {
                  if (bikMode === "amount") {
                    const val = Number(bikOverride);
                    if (isNaN(val) || val < 0) {
                      toast.error("Voer een geldig bedrag in");
                      return;
                    }
                    await updateCase.mutateAsync({
                      id: caseId,
                      data: { bik_override: bikOverride, bik_override_percentage: null },
                    });
                  } else if (bikMode === "percentage") {
                    const val = Number(bikPercentage);
                    if (isNaN(val) || val < 0 || val > 100) {
                      toast.error("Voer een percentage tussen 0 en 100 in");
                      return;
                    }
                    await updateCase.mutateAsync({
                      id: caseId,
                      data: { bik_override_percentage: bikPercentage, bik_override: null },
                    });
                  }
                  setBikSaved(true);
                  toast.success("Incassokosten opgeslagen");
                } catch {
                  toast.error("Opslaan mislukt");
                }
              }}
              disabled={updateCase.isPending}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
            >
              <Save className="h-3 w-3" />
              Opslaan
            </button>
          )}
        </div>

        {/* DF117-22: indicator that BIK is inherited from client default */}
        {isInheritedFromClient && (
          <div className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-800">
            <span className="font-medium">Overgenomen van klant-standaard.</span>{" "}
            Wijzig hieronder om voor dit dossier af te wijken.
          </div>
        )}

        {/* Mode selector */}
        <div className="grid grid-cols-3 gap-2">
          {(
            [
              { value: "wik" as const, label: "WIK-staffel", subtitle: "art. 6:96 BW" },
              { value: "amount" as const, label: "Vast bedrag", subtitle: "in euro's" },
              { value: "percentage" as const, label: "Percentage", subtitle: "van hoofdsom" },
            ]
          ).map((opt) => {
            const active = bikMode === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                onClick={async () => {
                  if (opt.value === bikMode) return;
                  setBikMode(opt.value);
                  setBikSaved(false);
                  if (opt.value === "wik") {
                    // Immediately persist WIK reset
                    try {
                      await updateCase.mutateAsync({
                        id: caseId,
                        data: { bik_override: null, bik_override_percentage: null },
                      });
                      setBikOverride("");
                      setBikPercentage("");
                      setBikSaved(true);
                      toast.success("Teruggezet naar WIK-staffel");
                    } catch {
                      toast.error("Opslaan mislukt");
                    }
                  } else if (opt.value === "amount" && !bikOverride) {
                    setBikOverride(summary.total_bik.toFixed(2));
                  }
                }}
                className={`rounded-lg border px-3 py-2.5 text-xs font-medium transition-colors text-left ${
                  active
                    ? "border-primary/30 bg-primary/5 text-primary"
                    : "border-border bg-card text-muted-foreground hover:border-primary/20 hover:text-foreground"
                }`}
              >
                <p className={active ? "font-semibold" : ""}>{opt.label}</p>
                <p className="text-[10px] text-muted-foreground mt-0.5">{opt.subtitle}</p>
              </button>
            );
          })}
        </div>

        <div className="flex items-end gap-4">
          <div className="flex-1">
            <p className="text-xs text-muted-foreground mb-1">
              {bikMode === "wik"
                ? "Berekend (WIK-staffel art. 6:96 BW)"
                : bikMode === "amount"
                  ? "WIK-staffel ter referentie"
                  : "WIK-staffel ter referentie"}
            </p>
            <p className="text-lg font-semibold tabular-nums text-foreground">
              {formatCurrency(summary.total_bik)}
            </p>
            {summary.bik_btw > 0 && (
              <p className="text-xs text-muted-foreground">
                incl. {formatCurrency(summary.bik_btw)} BTW
              </p>
            )}
          </div>

          {bikMode === "amount" && (
            <div className="flex-1">
              <label className="text-xs text-muted-foreground mb-1 block">
                Vast bedrag
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">€</span>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={bikOverride}
                  onChange={(e) => { setBikOverride(e.target.value); setBikSaved(false); }}
                  className="w-full rounded-lg border border-input bg-background pl-7 pr-3 py-2 text-sm font-medium tabular-nums focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                  placeholder={summary.total_bik.toFixed(2)}
                />
              </div>
              {bikOverrideAmount !== null && !isNaN(bikOverrideAmount) && bikDiff !== 0 && (
                <p className={`text-xs mt-1 ${bikDiff > 0 ? "text-amber-600" : "text-emerald-600"}`}>
                  {bikDiff > 0 ? "+" : ""}{formatCurrency(bikDiff)} t.o.v. WIK-berekening
                </p>
              )}
            </div>
          )}

          {bikMode === "percentage" && (
            <div className="flex-1">
              <label className="text-xs text-muted-foreground mb-1 block">
                Percentage van hoofdsom
              </label>
              <div className="relative">
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  value={bikPercentage}
                  onChange={(e) => { setBikPercentage(e.target.value); setBikSaved(false); }}
                  className="w-full rounded-lg border border-input bg-background pl-3 pr-8 py-2 text-sm font-medium tabular-nums focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                  placeholder="bijv. 10.00"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">%</span>
              </div>
              {bikOverrideAmount !== null && !isNaN(bikOverrideAmount) && (
                <p className="text-xs mt-1 text-muted-foreground">
                  = {formatCurrency(bikOverrideAmount)} ({bikPercentage}% van {formatCurrency(summary.total_principal)})
                </p>
              )}
            </div>
          )}
        </div>

        {bikManual && caseData?.interest_type !== "contractual" && (
          <p className="text-xs text-muted-foreground bg-amber-50 dark:bg-amber-950/20 rounded-lg px-3 py-2 border border-amber-200 dark:border-amber-800">
            Let op: bij een afwijkend bedrag is dit technisch geen WIK meer. Het berekende bedrag (WIK-staffel) blijft zichtbaar ter referentie.
          </p>
        )}
      </div>

      {/* Breakdown table */}
      <div className="rounded-xl border border-border bg-card overflow-x-auto">
        <div className="flex items-center gap-2 px-5 py-3.5 border-b border-border bg-muted/30">
          <Euro className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Specificatie</h3>
        </div>
        <table className="w-full min-w-[400px]">
          <thead>
            <tr className="border-b border-border">
              <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">Post</th>
              <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Totaal</th>
              <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Betaald</th>
              <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-muted-foreground">Openstaand</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((row) => {
              const rowPaid = row.total > 0 ? Math.round((row.paid / row.total) * 100) : 0;
              return (
                <tr key={row.label} className="hover:bg-muted/30 transition-colors">
                  <td className="px-5 py-3.5">
                    <p className="text-sm text-foreground">{row.label}</p>
                    <div className="mt-1 h-1 w-20 rounded-full bg-muted overflow-hidden">
                      <div className="h-full rounded-full bg-emerald-500" style={{ width: `${rowPaid}%` }} />
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-right text-sm font-medium tabular-nums">{formatCurrency(row.total)}</td>
                  <td className="px-5 py-3.5 text-right text-sm text-emerald-600 tabular-nums">{formatCurrency(row.paid)}</td>
                  <td className="px-5 py-3.5 text-right text-sm font-medium tabular-nums">
                    {row.open > 0 ? (
                      <span className="text-amber-600">{formatCurrency(row.open)}</span>
                    ) : (
                      <span className="text-emerald-600">{formatCurrency(0)}</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-border bg-muted/30">
              <td className="px-5 py-3.5 text-sm font-bold text-foreground">Totaal</td>
              <td className="px-5 py-3.5 text-right text-sm font-bold text-foreground tabular-nums">{formatCurrency(effectiveGrandTotal)}</td>
              <td className="px-5 py-3.5 text-right text-sm font-bold text-emerald-600 tabular-nums">{formatCurrency(summary.total_paid)}</td>
              <td className="px-5 py-3.5 text-right text-sm font-bold text-amber-600 tabular-nums">{formatCurrency(effectiveOutstanding)}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <p className="text-xs text-muted-foreground">
        Berekening op {formatDate(summary.calculation_date)}. Rente wordt dagelijks bijgewerkt.
      </p>
    </div>
  );
}
