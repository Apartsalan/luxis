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
import { formatCurrency, formatDate } from "@/lib/utils";

export function FinancieelTab({ caseId }: { caseId: string }) {
  const { data: summary, isLoading } = useFinancialSummary(caseId);
  const { data: caseData } = useCase(caseId);
  const updateCase = useUpdateCase();
  const [bikOverride, setBikOverride] = useState<string>("");
  const [bikManual, setBikManual] = useState(false);
  const [bikSaved, setBikSaved] = useState(false);

  // Initialize from persisted bik_override
  useEffect(() => {
    if (caseData?.bik_override != null) {
      setBikManual(true);
      setBikOverride(String(caseData.bik_override));
      setBikSaved(true);
    }
  }, [caseData?.bik_override]);

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

  if (!summary) return null;

  const bikOverrideAmount = bikManual && bikOverride !== "" ? parseFloat(bikOverride) : null;
  const effectiveBik = bikOverrideAmount !== null && !isNaN(bikOverrideAmount) ? bikOverrideAmount : summary.total_bik;
  const bikDiff = effectiveBik - summary.total_bik;
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
      label: bikOverrideAmount !== null && !isNaN(bikOverrideAmount)
        ? "Incassokosten (handmatig)"
        : summary.bik_btw > 0 ? "BIK incl. BTW" : "BIK (art. 6:96 BW)",
      total: effectiveBik,
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
          <div className="flex items-center gap-2">
            {bikManual && !bikSaved && (
              <button
                type="button"
                onClick={async () => {
                  const val = Number(bikOverride);
                  if (isNaN(val) || val < 0) {
                    toast.error("Voer een geldig bedrag in");
                    return;
                  }
                  try {
                    await updateCase.mutateAsync({ id: caseId, data: { bik_override: bikOverride } });
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
            <button
              type="button"
              onClick={async () => {
                if (bikManual) {
                  // Turning off manual mode → clear override on backend
                  try {
                    await updateCase.mutateAsync({ id: caseId, data: { bik_override: null } });
                    setBikManual(false);
                    setBikOverride("");
                    setBikSaved(false);
                    toast.success("Incassokosten teruggezet naar WIK-berekening");
                  } catch {
                    toast.error("Opslaan mislukt");
                  }
                } else {
                  // Turning on manual mode
                  setBikManual(true);
                  setBikOverride(summary.total_bik.toFixed(2));
                  setBikSaved(false);
                }
              }}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                bikManual
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              <Pencil className="h-3 w-3" />
              {bikManual ? "Resetten" : "Aanpassen"}
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex-1">
            <p className="text-xs text-muted-foreground mb-1">
              Berekend (WIK-staffel art. 6:96 BW)
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

          {bikManual && (
            <div className="flex-1">
              <label className="text-xs text-muted-foreground mb-1 block">
                Handmatig bedrag
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
        </div>

        {bikManual && (
          <p className="text-xs text-muted-foreground bg-amber-50 dark:bg-amber-950/20 rounded-lg px-3 py-2 border border-amber-200 dark:border-amber-800">
            Let op: bij een handmatig bedrag is dit technisch geen WIK meer. Het berekende bedrag (WIK-staffel) blijft zichtbaar ter referentie.
          </p>
        )}
      </div>

      {/* Breakdown table */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="flex items-center gap-2 px-5 py-3.5 border-b border-border bg-muted/30">
          <Euro className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Specificatie</h3>
        </div>
        <table className="w-full">
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
