"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Scale, Calendar, TrendingUp, Info } from "lucide-react";
import { api } from "@/lib/api";
import { formatDateShort } from "@/lib/utils";

interface InterestRate {
  id: string;
  interest_type: string;
  rate: number;
  effective_date: string;
  end_date: string | null;
  source: string | null;
}

const INTEREST_TYPE_LABELS: Record<string, string> = {
  statutory: "Wettelijke rente (art. 6:119 BW)",
  commercial: "Handelsrente (art. 6:119a BW)",
  government: "Overheidsrente (art. 6:119b BW)",
};

const INTEREST_TYPE_SHORT: Record<string, string> = {
  statutory: "Wettelijk",
  commercial: "Handels",
  government: "Overheid",
};

const INTEREST_TYPE_DESCRIPTIONS: Record<string, string> = {
  statutory:
    "De wettelijke rente voor niet-handelstransacties. Geldt bij verzuim in overeenkomsten met consumenten en niet-handelspartijen.",
  commercial:
    "De wettelijke handelsrente voor handelstransacties tussen bedrijven. Hoger dan de gewone wettelijke rente (art. 6:119a BW).",
  government:
    "De wettelijke rente voor transacties waarbij overheidsinstanties betrokken zijn (art. 6:119b BW).",
};

const INTEREST_TYPE_COLORS: Record<string, string> = {
  statutory: "bg-blue-100 text-blue-700",
  commercial: "bg-amber-100 text-amber-700",
  government: "bg-purple-100 text-purple-700",
};

export default function TarievenPage() {
  const [selectedType, setSelectedType] = useState<string>("statutory");

  const { data: rates, isLoading } = useQuery<InterestRate[]>({
    queryKey: ["interest-rates"],
    queryFn: async () => {
      const res = await api("/api/interest-rates");
      if (!res.ok) throw new Error("Failed to fetch interest rates");
      return res.json();
    },
  });

  // Group rates by type
  const ratesByType: Record<string, InterestRate[]> = {};
  if (rates) {
    for (const rate of rates) {
      if (!ratesByType[rate.interest_type]) {
        ratesByType[rate.interest_type] = [];
      }
      ratesByType[rate.interest_type].push(rate);
    }
    // Sort each group by effective_date descending (newest first)
    for (const type of Object.keys(ratesByType)) {
      ratesByType[type].sort(
        (a, b) =>
          new Date(b.effective_date).getTime() -
          new Date(a.effective_date).getTime()
      );
    }
  }

  const selectedRates = ratesByType[selectedType] ?? [];
  const currentRate = selectedRates[0]; // Most recent = currently active

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Rentetarieven</h1>
        <p className="text-sm text-muted-foreground">
          Wettelijke rentetarieven voor renteberekeningen
        </p>
      </div>

      {/* Current rates summary */}
      <div className="grid gap-4 md:grid-cols-3">
        {(["statutory", "commercial", "government"] as const).map((type) => {
          const typeRates = ratesByType[type] ?? [];
          const current = typeRates[0];
          const isSelected = selectedType === type;

          return (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              className={`rounded-xl border p-5 text-left transition-all ${
                isSelected
                  ? "border-primary bg-primary/5 ring-1 ring-primary/20"
                  : "border-border bg-card hover:border-primary/30"
              }`}
            >
              <div className="flex items-center gap-3 mb-3">
                <div
                  className={`flex h-9 w-9 items-center justify-center rounded-lg ${
                    INTEREST_TYPE_COLORS[type]
                  }`}
                >
                  <Scale className="h-4 w-4" />
                </div>
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {INTEREST_TYPE_SHORT[type]}
                </span>
              </div>
              {isLoading ? (
                <div className="h-8 w-20 rounded-md skeleton" />
              ) : current ? (
                <div>
                  <p className="text-2xl font-bold text-foreground">
                    {current.rate}%
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Sinds {formatDateShort(current.effective_date)}
                  </p>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  Geen data
                </p>
              )}
            </button>
          );
        })}
      </div>

      {/* Info card */}
      <div className="rounded-xl border border-border bg-card p-5">
        <div className="flex items-start gap-3">
          <Info className="h-5 w-5 text-primary mt-0.5 shrink-0" />
          <div>
            <h3 className="text-sm font-semibold text-foreground">
              {INTEREST_TYPE_LABELS[selectedType]}
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {INTEREST_TYPE_DESCRIPTIONS[selectedType]}
            </p>
          </div>
        </div>
      </div>

      {/* Rates history table */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-border bg-muted/30 px-5 py-3">
          <h2 className="text-sm font-semibold text-foreground">
            Historische tarieven &mdash;{" "}
            {INTEREST_TYPE_SHORT[selectedType]}
          </h2>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Calendar className="h-3.5 w-3.5" />
            {selectedRates.length} periodes
          </div>
        </div>

        {isLoading ? (
          <div className="p-5 space-y-2">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-10 rounded-md skeleton" />
            ))}
          </div>
        ) : selectedRates.length > 0 ? (
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Ingangsdatum
                </th>
                <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Einddatum
                </th>
                <th className="px-5 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Tarief
                </th>
                <th className="hidden sm:table-cell px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Bron
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {selectedRates.map((rate, idx) => (
                <tr
                  key={rate.id}
                  className={`hover:bg-muted/30 transition-colors ${
                    idx === 0 ? "bg-primary/5" : ""
                  }`}
                >
                  <td className="px-5 py-3 text-sm text-foreground">
                    {formatDateShort(rate.effective_date)}
                    {idx === 0 && (
                      <span className="ml-2 inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
                        <TrendingUp className="h-3 w-3" />
                        Huidig
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-sm text-muted-foreground">
                    {rate.end_date
                      ? formatDateShort(rate.end_date)
                      : "Heden"}
                  </td>
                  <td className="px-5 py-3 text-right text-sm font-semibold text-foreground">
                    {rate.rate}%
                  </td>
                  <td className="hidden sm:table-cell px-5 py-3 text-xs text-muted-foreground">
                    {rate.source || "DNB / Rijksoverheid"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="py-12 text-center">
            <Scale className="mx-auto h-10 w-10 text-muted-foreground/30" />
            <p className="mt-3 text-sm text-muted-foreground">
              Geen tarieven gevonden voor dit type
            </p>
          </div>
        )}
      </div>

      {/* WIK staffel info */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold text-foreground mb-4">
          BIK Staffel (art. 6:96 BW)
        </h2>
        <p className="text-sm text-muted-foreground mb-4">
          De buitengerechtelijke incassokosten worden berekend volgens
          onderstaande staffel. Minimum: &euro;40, Maximum: &euro;6.775.
        </p>
        <div className="rounded-lg border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="px-4 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Over het bedrag
                </th>
                <th className="px-4 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Percentage
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              <tr>
                <td className="px-4 py-2.5 text-foreground">
                  Eerste &euro;2.500
                </td>
                <td className="px-4 py-2.5 text-right font-medium">15%</td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 text-foreground">
                  &euro;2.500 &ndash; &euro;5.000
                </td>
                <td className="px-4 py-2.5 text-right font-medium">10%</td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 text-foreground">
                  &euro;5.000 &ndash; &euro;10.000
                </td>
                <td className="px-4 py-2.5 text-right font-medium">5%</td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 text-foreground">
                  &euro;10.000 &ndash; &euro;200.000
                </td>
                <td className="px-4 py-2.5 text-right font-medium">1%</td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 text-foreground">
                  Boven &euro;200.000
                </td>
                <td className="px-4 py-2.5 text-right font-medium">0,5%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
