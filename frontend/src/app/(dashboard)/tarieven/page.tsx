"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Scale, ChevronDown, ChevronUp } from "lucide-react";
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

const TYPE_LABELS: Record<string, string> = {
  statutory: "Wettelijke rente",
  commercial: "Handelsrente",
  government: "Overheidsrente",
};

const TYPE_COLORS: Record<string, string> = {
  statutory: "bg-blue-50 text-blue-700",
  commercial: "bg-amber-50 text-amber-700",
  government: "bg-purple-50 text-purple-700",
};

export default function TarievenPage() {
  const [expandedType, setExpandedType] = useState<string | null>(null);

  const { data: rates, isLoading } = useQuery<InterestRate[]>({
    queryKey: ["interest-rates"],
    queryFn: async () => {
      const res = await api("/api/interest-rates");
      if (!res.ok) throw new Error("Failed to fetch interest rates");
      return res.json();
    },
  });

  // Group and sort by type
  const ratesByType: Record<string, InterestRate[]> = {};
  if (rates) {
    for (const rate of rates) {
      if (!ratesByType[rate.interest_type]) {
        ratesByType[rate.interest_type] = [];
      }
      ratesByType[rate.interest_type].push(rate);
    }
    for (const type of Object.keys(ratesByType)) {
      ratesByType[type].sort(
        (a, b) =>
          new Date(b.effective_date).getTime() -
          new Date(a.effective_date).getTime()
      );
    }
  }

  const types = ["statutory", "commercial", "government"] as const;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Rentetarieven</h1>
        <p className="text-sm text-muted-foreground">
          Huidige rentetarieven voor berekeningen bij vorderingen
        </p>
      </div>

      {/* Compact rate overview */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        {isLoading ? (
          <div className="p-5 space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-12 rounded-md skeleton" />
            ))}
          </div>
        ) : (
          <div className="divide-y divide-border">
            {types.map((type) => {
              const typeRates = ratesByType[type] ?? [];
              const current = typeRates[0];
              const isExpanded = expandedType === type;

              return (
                <div key={type}>
                  {/* Rate row — compact, clickable */}
                  <button
                    onClick={() =>
                      setExpandedType(isExpanded ? null : type)
                    }
                    className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-muted/30 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className={`inline-flex items-center justify-center h-7 w-7 rounded-md text-xs ${TYPE_COLORS[type]}`}
                      >
                        <Scale className="h-3.5 w-3.5" />
                      </span>
                      <div className="text-left">
                        <span className="text-sm font-medium text-foreground">
                          {TYPE_LABELS[type]}
                        </span>
                        {current && (
                          <span className="ml-2 text-xs text-muted-foreground">
                            sinds {formatDateShort(current.effective_date)}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-semibold text-foreground tabular-nums">
                        {current ? `${current.rate}%` : "—"}
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>
                  </button>

                  {/* Expandable history */}
                  {isExpanded && typeRates.length > 0 && (
                    <div className="border-t border-border bg-muted/10 px-5 py-3">
                      <p className="text-xs font-medium text-muted-foreground mb-2">
                        Historische tarieven ({typeRates.length} periodes)
                      </p>
                      <div className="max-h-64 overflow-y-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-xs text-muted-foreground">
                              <th className="text-left py-1 font-medium">
                                Vanaf
                              </th>
                              <th className="text-left py-1 font-medium">
                                Tot
                              </th>
                              <th className="text-right py-1 font-medium">
                                Tarief
                              </th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border/50">
                            {typeRates.map((rate, idx) => (
                              <tr
                                key={rate.id}
                                className={
                                  idx === 0
                                    ? "text-foreground font-medium"
                                    : "text-muted-foreground"
                                }
                              >
                                <td className="py-1.5">
                                  {formatDateShort(rate.effective_date)}
                                  {idx === 0 && (
                                    <span className="ml-1.5 text-[10px] font-medium text-primary">
                                      huidig
                                    </span>
                                  )}
                                </td>
                                <td className="py-1.5">
                                  {rate.end_date
                                    ? formatDateShort(rate.end_date)
                                    : "heden"}
                                </td>
                                <td className="py-1.5 text-right tabular-nums">
                                  {rate.rate}%
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
