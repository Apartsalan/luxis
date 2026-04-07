"use client";

import { useState } from "react";
import { Clock, Euro, Filter, Plus, X } from "lucide-react";
import { toast } from "sonner";
import { EmptyState } from "@/components/empty-state";
import {
  useTimeEntries,
  useTimeEntrySummary,
  useCreateTimeEntry,
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
  const [billableFilter, setBillableFilter] = useState<"alle" | "declarabel" | "niet-declarabel">("alle");
  const [activityFilter, setActivityFilter] = useState<string>("alle");
  const [showAddDialog, setShowAddDialog] = useState(false);

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
      {/* Header with "Uren toevoegen" button */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">Tijdregistraties</h3>
        <button
          onClick={() => setShowAddDialog(true)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          Uren toevoegen
        </button>
      </div>

      {showAddDialog && (
        <AddTimeEntryDialog caseId={caseId} onClose={() => setShowAddDialog(false)} />
      )}

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
        <EmptyState
          icon={Clock}
          title="Geen uren geregistreerd"
          description="Start de timer of registreer handmatig via Tijdschrijven om uren bij te houden voor dit dossier."
        />
      ) : (() => {
        // Collect unique activity types for filter
        const activityTypes = [...new Set(entries.map((e: TimeEntry) => e.activity_type))];

        // Apply filters
        const filtered = entries.filter((entry: TimeEntry) => {
          if (billableFilter === "declarabel" && !entry.billable) return false;
          if (billableFilter === "niet-declarabel" && entry.billable) return false;
          if (activityFilter !== "alle" && entry.activity_type !== activityFilter) return false;
          return true;
        });

        return (
        <div className="space-y-3">
          {/* Filters */}
          {entries.length > 2 && (
            <div className="flex items-center gap-4 flex-wrap">
              <div className="flex items-center gap-2">
                <Filter className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                {(["alle", "declarabel", "niet-declarabel"] as const).map((opt) => {
                  const isActive = billableFilter === opt;
                  const label = opt === "alle" ? "Alle" : opt === "declarabel" ? "Declarabel" : "Niet declarabel";
                  return (
                    <button
                      key={opt}
                      onClick={() => setBillableFilter(opt)}
                      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                        isActive
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground"
                      }`}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>
              {activityTypes.length > 1 && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Activiteit:</span>
                  <select
                    value={activityFilter}
                    onChange={(e) => setActivityFilter(e.target.value)}
                    className="rounded-lg border border-border bg-card px-2.5 py-1 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                  >
                    <option value="alle">Alle</option>
                    {activityTypes.map((type) => (
                      <option key={type} value={type}>
                        {ACTIVITY_TYPE_LABELS[type] ?? type}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          )}

          <div className="rounded-xl border border-border overflow-x-auto">
          <table className="w-full min-w-[600px] text-sm">
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
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-sm text-muted-foreground">
                    Geen uren voor dit filter
                  </td>
                </tr>
              ) : filtered.map((entry: TimeEntry) => {
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
        </div>
        );
      })()}
    </div>
  );
}

function AddTimeEntryDialog({ caseId, onClose }: { caseId: string; onClose: () => void }) {
  const createEntry = useCreateTimeEntry();
  const [form, setForm] = useState({
    date: new Date().toISOString().slice(0, 10),
    hours: "",
    minutes: "",
    activity_type: "drafting",
    description: "",
    billable: true,
  });
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    const h = parseInt(form.hours || "0", 10);
    const m = parseInt(form.minutes || "0", 10);
    const totalMinutes = h * 60 + m;
    if (totalMinutes <= 0) {
      setError("Vul een duur in (uren of minuten)");
      return;
    }

    try {
      await createEntry.mutateAsync({
        case_id: caseId,
        date: form.date,
        duration_minutes: totalMinutes,
        activity_type: form.activity_type,
        description: form.description || null,
        billable: form.billable,
      });
      toast.success("Uren toegevoegd");
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Kon niet opslaan");
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-xl bg-card border border-border shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <h2 className="text-base font-semibold text-foreground">Uren toevoegen</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4 p-5">
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Datum</label>
            <input
              type="date"
              required
              value={form.date}
              onChange={(e) => setForm((p) => ({ ...p, date: e.target.value }))}
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Uren</label>
              <input
                type="number"
                min="0"
                max="24"
                placeholder="0"
                value={form.hours}
                onChange={(e) => setForm((p) => ({ ...p, hours: e.target.value }))}
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Minuten</label>
              <input
                type="number"
                min="0"
                max="59"
                step="6"
                placeholder="0"
                value={form.minutes}
                onChange={(e) => setForm((p) => ({ ...p, minutes: e.target.value }))}
                className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Activiteit</label>
            <select
              value={form.activity_type}
              onChange={(e) => setForm((p) => ({ ...p, activity_type: e.target.value }))}
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              {Object.entries(ACTIVITY_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1">Omschrijving</label>
            <textarea
              value={form.description}
              onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              rows={3}
              placeholder="Wat heb je gedaan?"
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none"
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.billable}
              onChange={(e) => setForm((p) => ({ ...p, billable: e.target.checked }))}
              className="rounded border-input"
            />
            <span className="text-foreground">Declarabel</span>
          </label>
          {error && (
            <div className="rounded-lg bg-destructive/10 px-3 py-2 text-xs text-destructive">{error}</div>
          )}
          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              disabled={createEntry.isPending}
              className="flex-1 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {createEntry.isPending ? "Opslaan..." : "Opslaan"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted transition-colors"
            >
              Annuleren
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
