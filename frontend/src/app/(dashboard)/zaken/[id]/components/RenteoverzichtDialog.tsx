"use client";

import { useState } from "react";
import { X, Euro, Calendar, TrendingUp } from "lucide-react";
import { useCaseInterest, useCaseBIK } from "@/hooks/use-collections";
import type { ClaimInterest, InterestPeriod } from "@/hooks/use-collections";

interface RenteoverzichtDialogProps {
  caseId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("nl-NL", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("nl-NL", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function formatPercentage(rate: number): string {
  return `${rate.toFixed(2)}%`;
}

function PeriodRow({ period }: { period: InterestPeriod }) {
  return (
    <tr className="border-b border-border/50 text-xs">
      <td className="py-1.5 pr-3 text-muted-foreground">
        {formatDate(period.start_date)} – {formatDate(period.end_date)}
      </td>
      <td className="py-1.5 pr-3 text-right">{period.days}d</td>
      <td className="py-1.5 pr-3 text-right">{formatPercentage(period.rate)}</td>
      <td className="py-1.5 pr-3 text-right">{formatCurrency(period.principal)}</td>
      <td className="py-1.5 text-right font-medium">{formatCurrency(period.interest)}</td>
    </tr>
  );
}

function ClaimSection({ claim }: { claim: ClaimInterest }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-border bg-card">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-muted/50 transition-colors"
      >
        <div>
          <p className="text-sm font-medium text-foreground">{claim.description}</p>
          <p className="text-xs text-muted-foreground">
            Hoofdsom: {formatCurrency(claim.principal_amount)} · Verzuimdatum: {formatDate(claim.default_date)}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm font-semibold text-orange-600">{formatCurrency(claim.total_interest)}</p>
          <p className="text-xs text-muted-foreground">{claim.periods.length} periodes</p>
        </div>
      </button>
      {expanded && claim.periods.length > 0 && (
        <div className="border-t border-border px-4 py-3">
          <table className="w-full">
            <thead>
              <tr className="text-[10px] uppercase text-muted-foreground">
                <th className="pb-1.5 text-left font-medium">Periode</th>
                <th className="pb-1.5 text-right font-medium">Dagen</th>
                <th className="pb-1.5 text-right font-medium">Tarief</th>
                <th className="pb-1.5 text-right font-medium">Hoofdsom</th>
                <th className="pb-1.5 text-right font-medium">Rente</th>
              </tr>
            </thead>
            <tbody>
              {claim.periods.map((period, i) => (
                <PeriodRow key={i} period={period} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export function RenteoverzichtDialog({ caseId, open, onOpenChange }: RenteoverzichtDialogProps) {
  const { data: interest, isLoading: interestLoading } = useCaseInterest(open ? caseId : undefined);
  const { data: bik, isLoading: bikLoading } = useCaseBIK(open ? caseId : undefined);

  if (!open) return null;

  const isLoading = interestLoading || bikLoading;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => onOpenChange(false)}
      />

      {/* Dialog */}
      <div className="relative z-10 w-full max-w-2xl max-h-[80vh] overflow-y-auto rounded-xl border border-border bg-background shadow-xl mx-4">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-background px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-orange-100 p-2">
              <TrendingUp className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">Renteoverzicht</h2>
              {interest && (
                <p className="text-xs text-muted-foreground">
                  Berekend per {formatDate(interest.calculation_date)} · {interest.interest_type === "statutory" ? "Wettelijke rente" : interest.interest_type === "commercial" ? "Handelsrente" : "Contractuele rente"}
                </p>
              )}
            </div>
          </div>
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="rounded-lg p-1.5 hover:bg-muted transition-colors"
          >
            <X className="h-5 w-5 text-muted-foreground" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <span className="ml-3 text-sm text-muted-foreground">Rente berekenen...</span>
            </div>
          ) : (
            <>
              {/* Summary cards */}
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-lg border border-border bg-card p-3">
                  <p className="text-xs text-muted-foreground">Totaal hoofdsom</p>
                  <p className="text-lg font-semibold text-foreground">
                    {formatCurrency(interest?.total_principal ?? 0)}
                  </p>
                </div>
                <div className="rounded-lg border border-orange-200 bg-orange-50 p-3 dark:border-orange-800 dark:bg-orange-950/30">
                  <p className="text-xs text-orange-600">Totaal rente</p>
                  <p className="text-lg font-semibold text-orange-700 dark:text-orange-400">
                    {formatCurrency(interest?.total_interest ?? 0)}
                  </p>
                </div>
                <div className="rounded-lg border border-border bg-card p-3">
                  <p className="text-xs text-muted-foreground">Totaal verschuldigd</p>
                  <p className="text-lg font-semibold text-foreground">
                    {formatCurrency(interest?.total_outstanding ?? 0)}
                  </p>
                </div>
              </div>

              {/* BIK card */}
              {bik && bik.bik_amount > 0 && (
                <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 dark:border-blue-800 dark:bg-blue-950/30">
                  <p className="text-xs text-blue-600 font-medium mb-1">Buitengerechtelijke incassokosten (BIK)</p>
                  <div className="flex items-center gap-4 text-sm">
                    <span>BIK: {formatCurrency(bik.bik_amount)}</span>
                    {bik.include_btw && <span>BTW: {formatCurrency(bik.bik_btw)}</span>}
                    <span className="font-semibold">Totaal: {formatCurrency(bik.total_bik)}</span>
                  </div>
                </div>
              )}

              {/* Per-claim breakdown */}
              {interest?.claims && interest.claims.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-foreground">Per vordering</h3>
                  {interest.claims.map((claim) => (
                    <ClaimSection key={claim.claim_id} claim={claim} />
                  ))}
                </div>
              )}

              {/* No claims */}
              {(!interest?.claims || interest.claims.length === 0) && !isLoading && (
                <div className="text-center py-8 text-sm text-muted-foreground">
                  Geen vorderingen gevonden voor dit dossier.
                  <br />
                  Voeg eerst vorderingen toe in de tab &ldquo;Vorderingen&rdquo;.
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
