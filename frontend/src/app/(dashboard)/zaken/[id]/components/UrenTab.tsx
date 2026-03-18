"use client";

import { Clock, Euro } from "lucide-react";
import {
  useTimeEntries,
  useTimeEntrySummary,
  ACTIVITY_TYPE_LABELS,
  type TimeEntry,
} from "@/hooks/use-time-entries";
import { formatCurrency, formatDateShort } from "@/lib/utils";

function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}:${String(m).padStart(2, "0")}`;
}

export default function UrenTab({ caseId }: { caseId: string }) {
  const { data: entries, isLoading } = useTimeEntries({ case_id: caseId });
  const { data: summary } = useTimeEntrySummary({ case_id: caseId });

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-14 rounded-lg skeleton" />
        ))}
      </div>
    );
  }

  const totalMinutes = summary?.total_minutes ?? 0;
  const billableMinutes = summary?.billable_minutes ?? 0;
  const totalAmount = summary?.total_amount ?? 0;

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span className="text-xs font-medium">Totaal uren</span>
          </div>
          <p className="mt-1 text-2xl font-semibold text-foreground">
            {formatDuration(totalMinutes)}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span className="text-xs font-medium">Declarabel</span>
          </div>
          <p className="mt-1 text-2xl font-semibold text-foreground">
            {formatDuration(billableMinutes)}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Euro className="h-4 w-4" />
            <span className="text-xs font-medium">Totaal bedrag</span>
          </div>
          <p className="mt-1 text-2xl font-semibold text-foreground">
            {formatCurrency(totalAmount)}
          </p>
        </div>
      </div>

      {/* Time entries list */}
      {!entries || entries.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <Clock className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">
            Geen uren geregistreerd voor dit dossier
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Start de timer of registreer handmatig via Tijdschrijven
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                  Datum
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                  Medewerker
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                  Activiteit
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground">
                  Omschrijving
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground">
                  Duur
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-muted-foreground">
                  Bedrag
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {entries.map((entry: TimeEntry) => {
                const amount =
                  entry.billable && entry.hourly_rate
                    ? (entry.duration_minutes / 60) * entry.hourly_rate
                    : 0;
                return (
                  <tr
                    key={entry.id}
                    className="hover:bg-muted/30 transition-colors"
                  >
                    <td className="px-4 py-3 text-foreground whitespace-nowrap">
                      {formatDateShort(entry.date)}
                    </td>
                    <td className="px-4 py-3 text-foreground">
                      {entry.user?.full_name ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {ACTIVITY_TYPE_LABELS[entry.activity_type] ??
                        entry.activity_type}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground max-w-xs truncate">
                      {entry.description || "—"}
                    </td>
                    <td className="px-4 py-3 text-right text-foreground font-medium whitespace-nowrap">
                      {formatDuration(entry.duration_minutes)}
                    </td>
                    <td className="px-4 py-3 text-right text-foreground whitespace-nowrap">
                      {entry.billable ? (
                        formatCurrency(amount)
                      ) : (
                        <span className="text-muted-foreground text-xs">
                          Niet declarabel
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
