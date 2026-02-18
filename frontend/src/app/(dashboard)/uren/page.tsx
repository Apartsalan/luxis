"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import {
  Clock,
  Plus,
  Play,
  Square,
  Pencil,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Timer,
  Briefcase,
  X,
} from "lucide-react";
import {
  useTimeEntries,
  useCreateTimeEntry,
  useUpdateTimeEntry,
  useDeleteTimeEntry,
  useTimeEntrySummary,
  useMyTodayEntries,
  ACTIVITY_TYPE_LABELS,
  type TimeEntry,
} from "@/hooks/use-time-entries";
import { useCases, type CaseSummary } from "@/hooks/use-cases";
import { formatCurrency } from "@/lib/utils";
import { QueryError } from "@/components/query-error";
import { toast } from "sonner";

// ── Helpers ──────────────────────────────────────────────────────────────

function fmtMinutes(mins: number): string {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return `${h}:${String(m).padStart(2, "0")}`;
}

function getWeekDates(weekOffset: number): { start: string; end: string; days: Date[] } {
  const now = new Date();
  const day = now.getDay(); // 0=Sun
  const mondayOffset = day === 0 ? -6 : 1 - day;
  const monday = new Date(now);
  monday.setDate(now.getDate() + mondayOffset + weekOffset * 7);
  monday.setHours(0, 0, 0, 0);

  const days: Date[] = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    days.push(d);
  }
  const friday = days[4];
  return {
    start: toISO(monday),
    end: toISO(friday),
    days,
  };
}

function toISO(d: Date): string {
  return d.toISOString().split("T")[0];
}

const DAY_NAMES = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"];

// ── Page component ───────────────────────────────────────────────────────

export default function UrenPage() {
  // Week navigation
  const [weekOffset, setWeekOffset] = useState(0);
  const week = getWeekDates(weekOffset);
  const isCurrentWeek = weekOffset === 0;

  // Filters
  const [filterCaseId, setFilterCaseId] = useState("");
  const [filterBillable, setFilterBillable] = useState<string>("");

  // Query data
  const {
    data: entries,
    isLoading,
    isError,
    error,
    refetch,
  } = useTimeEntries({
    date_from: week.start,
    date_to: week.end,
    case_id: filterCaseId || undefined,
    billable: filterBillable === "" ? undefined : filterBillable === "true",
  });

  const { data: summary } = useTimeEntrySummary({
    date_from: week.start,
    date_to: week.end,
  });

  const { data: todayEntries } = useMyTodayEntries();

  const { data: casesData } = useCases({ per_page: 200 });
  const cases = casesData?.items ?? [];

  // Mutations
  const createMutation = useCreateTimeEntry();
  const updateMutation = useUpdateTimeEntry();
  const deleteMutation = useDeleteTimeEntry();

  // ── Timer state ──────────────────────────────────────────────────────
  const [timerRunning, setTimerRunning] = useState(false);
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [timerCaseId, setTimerCaseId] = useState("");
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (timerRunning) {
      timerRef.current = setInterval(() => setTimerSeconds((s) => s + 1), 1000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [timerRunning]);

  const startTimer = () => {
    if (!timerCaseId) {
      toast.error("Selecteer eerst een zaak");
      return;
    }
    setTimerSeconds(0);
    setTimerRunning(true);
  };

  const stopTimer = async () => {
    setTimerRunning(false);
    const minutes = Math.max(1, Math.round(timerSeconds / 60));
    try {
      await createMutation.mutateAsync({
        case_id: timerCaseId,
        date: toISO(new Date()),
        duration_minutes: minutes,
        activity_type: "other",
        billable: true,
      });
      toast.success(`${fmtMinutes(minutes)} geregistreerd`);
      setTimerSeconds(0);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  // ── New entry form ───────────────────────────────────────────────────
  const [showForm, setShowForm] = useState(false);
  const [formCaseId, setFormCaseId] = useState("");
  const [formDate, setFormDate] = useState(toISO(new Date()));
  const [formHours, setFormHours] = useState("");
  const [formMinutes, setFormMinutes] = useState("");
  const [formActivity, setFormActivity] = useState("other");
  const [formDescription, setFormDescription] = useState("");
  const [formBillable, setFormBillable] = useState(true);
  const [formRate, setFormRate] = useState("");

  const resetForm = () => {
    setFormCaseId("");
    setFormDate(toISO(new Date()));
    setFormHours("");
    setFormMinutes("");
    setFormActivity("other");
    setFormDescription("");
    setFormBillable(true);
    setFormRate("");
  };

  const submitEntry = async () => {
    const totalMinutes = (parseInt(formHours || "0") * 60) + parseInt(formMinutes || "0");
    if (!formCaseId || totalMinutes <= 0) {
      toast.error("Selecteer een zaak en voer een geldige duur in");
      return;
    }
    try {
      await createMutation.mutateAsync({
        case_id: formCaseId,
        date: formDate,
        duration_minutes: totalMinutes,
        activity_type: formActivity,
        description: formDescription || undefined,
        billable: formBillable,
        hourly_rate: formRate ? parseFloat(formRate) : undefined,
      });
      toast.success("Tijdregistratie opgeslagen");
      resetForm();
      setShowForm(false);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  // ── Inline edit ──────────────────────────────────────────────────────
  const [editId, setEditId] = useState<string | null>(null);
  const [editMinutes, setEditMinutes] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const startEdit = (entry: TimeEntry) => {
    setEditId(entry.id);
    setEditMinutes(String(entry.duration_minutes));
    setEditDescription(entry.description || "");
  };

  const saveEdit = async () => {
    if (!editId) return;
    try {
      await updateMutation.mutateAsync({
        id: editId,
        data: {
          duration_minutes: parseInt(editMinutes) || 1,
          description: editDescription || undefined,
        },
      });
      toast.success("Bijgewerkt");
      setEditId(null);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const deleteEntry = async (id: string) => {
    try {
      await deleteMutation.mutateAsync(id);
      toast.success("Verwijderd");
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  // ── Computed ─────────────────────────────────────────────────────────
  const dayTotals = new Map<string, number>();
  if (entries) {
    for (const e of entries) {
      dayTotals.set(e.date, (dayTotals.get(e.date) || 0) + e.duration_minutes);
    }
  }

  const todayTotal = todayEntries?.reduce((sum, e) => sum + e.duration_minutes, 0) ?? 0;
  const timerDisplay = `${Math.floor(timerSeconds / 3600)}:${String(Math.floor((timerSeconds % 3600) / 60)).padStart(2, "0")}:${String(timerSeconds % 60).padStart(2, "0")}`;

  // ── Render ───────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Urenregistratie</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Vandaag: {fmtMinutes(todayTotal)} geregistreerd
          </p>
        </div>
        <button
          onClick={() => { resetForm(); setShowForm(true); }}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Nieuwe registratie
        </button>
      </div>

      {/* Timer + Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Timer card */}
        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground mb-3">
            <Timer className="h-4 w-4" />
            Stopwatch
          </div>
          <div className="text-2xl font-mono font-bold text-foreground mb-3 tabular-nums">
            {timerDisplay}
          </div>
          <select
            value={timerCaseId}
            onChange={(e) => setTimerCaseId(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm mb-2"
            disabled={timerRunning}
          >
            <option value="">Selecteer zaak...</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.case_number}
              </option>
            ))}
          </select>
          {timerRunning ? (
            <button
              onClick={stopTimer}
              className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-destructive px-3 py-2 text-sm font-medium text-destructive-foreground hover:bg-destructive/90 transition-colors"
            >
              <Square className="h-3.5 w-3.5" />
              Stop
            </button>
          ) : (
            <button
              onClick={startTimer}
              className="w-full inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 transition-colors"
            >
              <Play className="h-3.5 w-3.5" />
              Start
            </button>
          )}
        </div>

        {/* Summary cards */}
        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Totaal deze week</p>
          <p className="mt-1 text-2xl font-bold text-foreground">
            {summary ? fmtMinutes(summary.total_minutes) : "—"}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">uur</p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Declarabel</p>
          <p className="mt-1 text-2xl font-bold text-emerald-600">
            {summary ? fmtMinutes(summary.billable_minutes) : "—"}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {summary ? `${summary.non_billable_minutes > 0 ? fmtMinutes(summary.non_billable_minutes) + " niet-declarabel" : "alles declarabel"}` : ""}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Totaal bedrag</p>
          <p className="mt-1 text-2xl font-bold text-foreground">
            {summary ? formatCurrency(summary.total_amount) : "—"}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">deze week</p>
        </div>
      </div>

      {/* Week navigation + filters */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setWeekOffset((w) => w - 1)}
            className="rounded-md border border-border p-1.5 hover:bg-muted transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            onClick={() => setWeekOffset(0)}
            className="rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors"
            disabled={isCurrentWeek}
          >
            Deze week
          </button>
          <button
            onClick={() => setWeekOffset((w) => w + 1)}
            className="rounded-md border border-border p-1.5 hover:bg-muted transition-colors"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
          <span className="ml-2 text-sm text-muted-foreground">
            {new Date(week.start).toLocaleDateString("nl-NL", { day: "numeric", month: "short" })}
            {" — "}
            {new Date(week.end).toLocaleDateString("nl-NL", { day: "numeric", month: "short", year: "numeric" })}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={filterCaseId}
            onChange={(e) => setFilterCaseId(e.target.value)}
            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm"
          >
            <option value="">Alle zaken</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>{c.case_number}</option>
            ))}
          </select>
          <select
            value={filterBillable}
            onChange={(e) => setFilterBillable(e.target.value)}
            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm"
          >
            <option value="">Alle typen</option>
            <option value="true">Declarabel</option>
            <option value="false">Niet-declarabel</option>
          </select>
        </div>
      </div>

      {/* Week day bar */}
      <div className="grid grid-cols-5 gap-2">
        {week.days.slice(0, 5).map((day, i) => {
          const iso = toISO(day);
          const total = dayTotals.get(iso) || 0;
          const isToday = iso === toISO(new Date());
          return (
            <div
              key={iso}
              className={`rounded-lg border p-3 text-center transition-colors ${
                isToday
                  ? "border-primary bg-primary/5"
                  : "border-border bg-card"
              }`}
            >
              <p className="text-xs font-medium text-muted-foreground">{DAY_NAMES[i]}</p>
              <p className="text-xs text-muted-foreground">
                {day.toLocaleDateString("nl-NL", { day: "numeric", month: "short" })}
              </p>
              <p className={`mt-1 text-lg font-bold tabular-nums ${total > 0 ? "text-foreground" : "text-muted-foreground/40"}`}>
                {fmtMinutes(total)}
              </p>
            </div>
          );
        })}
      </div>

      {/* New entry form (modal-like panel) */}
      {showForm && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground">Nieuwe registratie</h3>
            <button onClick={() => setShowForm(false)} className="text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Zaak *</label>
              <select
                value={formCaseId}
                onChange={(e) => setFormCaseId(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Selecteer zaak...</option>
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>{c.case_number}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Datum</label>
              <input
                type="date"
                value={formDate}
                onChange={(e) => setFormDate(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Duur *</label>
              <div className="flex gap-1.5">
                <input
                  type="number"
                  min="0"
                  placeholder="uur"
                  value={formHours}
                  onChange={(e) => setFormHours(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
                <input
                  type="number"
                  min="0"
                  max="59"
                  placeholder="min"
                  value={formMinutes}
                  onChange={(e) => setFormMinutes(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Activiteit</label>
              <select
                value={formActivity}
                onChange={(e) => setFormActivity(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {Object.entries(ACTIVITY_TYPE_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-muted-foreground mb-1">Omschrijving</label>
              <input
                type="text"
                placeholder="Wat heb je gedaan?"
                value={formDescription}
                onChange={(e) => setFormDescription(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted-foreground mb-1">Uurtarief</label>
              <input
                type="number"
                min="0"
                step="0.01"
                placeholder="optioneel"
                value={formRate}
                onChange={(e) => setFormRate(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formBillable}
                  onChange={(e) => setFormBillable(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-primary"
                />
                <span className="text-sm text-foreground">Declarabel</span>
              </label>
            </div>
          </div>
          <div className="flex justify-end mt-4">
            <button
              onClick={submitEntry}
              disabled={createMutation.isPending}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {createMutation.isPending ? "Opslaan..." : "Opslaan"}
            </button>
          </div>
        </div>
      )}

      {/* Entries table */}
      {isError ? (
        <QueryError message={error?.message} onRetry={refetch} />
      ) : isLoading ? (
        <div className="rounded-xl border border-border bg-card shadow-sm">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="flex items-center gap-4 px-5 py-3.5 border-b border-border last:border-0">
              <div className="h-4 w-20 rounded bg-muted animate-pulse" />
              <div className="h-4 w-16 rounded bg-muted animate-pulse" />
              <div className="h-4 w-32 rounded bg-muted animate-pulse flex-1" />
              <div className="h-4 w-14 rounded bg-muted animate-pulse" />
            </div>
          ))}
        </div>
      ) : !entries || entries.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-card py-16 text-center">
          <Clock className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm font-medium text-foreground">Geen registraties deze week</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Gebruik de stopwatch of klik op &quot;Nieuwe registratie&quot;
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card shadow-sm overflow-hidden">
          {/* Table header */}
          <div className="grid grid-cols-[100px_80px_1fr_120px_80px_60px_60px] gap-2 px-5 py-2.5 border-b border-border bg-muted/50 text-xs font-medium text-muted-foreground">
            <span>Datum</span>
            <span>Zaak</span>
            <span>Omschrijving</span>
            <span>Activiteit</span>
            <span className="text-right">Duur</span>
            <span className="text-center">Decl.</span>
            <span></span>
          </div>

          {/* Table rows */}
          {entries.map((entry) => (
            <div
              key={entry.id}
              className="group grid grid-cols-[100px_80px_1fr_120px_80px_60px_60px] gap-2 items-center px-5 py-3 border-b border-border last:border-0 hover:bg-muted/30 transition-colors"
            >
              <span className="text-sm text-foreground tabular-nums">
                {new Date(entry.date).toLocaleDateString("nl-NL", { day: "numeric", month: "short" })}
              </span>
              <Link
                href={`/zaken/${entry.case.id}`}
                className="text-sm font-medium text-foreground truncate hover:text-primary transition-colors"
                title={entry.case.case_number}
              >
                {entry.case.case_number}
              </Link>
              {editId === entry.id ? (
                <input
                  type="text"
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && saveEdit()}
                  className="rounded border border-input bg-background px-2 py-1 text-sm"
                  autoFocus
                />
              ) : (
                <span className="text-sm text-muted-foreground truncate">
                  {entry.description || "—"}
                </span>
              )}
              <span className="text-xs text-muted-foreground">
                {ACTIVITY_TYPE_LABELS[entry.activity_type] || entry.activity_type}
              </span>
              {editId === entry.id ? (
                <input
                  type="number"
                  value={editMinutes}
                  onChange={(e) => setEditMinutes(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && saveEdit()}
                  className="rounded border border-input bg-background px-2 py-1 text-sm text-right w-full"
                  min="1"
                />
              ) : (
                <span className="text-sm font-medium text-foreground text-right tabular-nums">
                  {fmtMinutes(entry.duration_minutes)}
                </span>
              )}
              <span className="text-center">
                {entry.billable ? (
                  <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
                    Ja
                  </span>
                ) : (
                  <span className="inline-flex items-center rounded-full bg-slate-50 px-2 py-0.5 text-[10px] font-medium text-slate-600 ring-1 ring-inset ring-slate-500/20">
                    Nee
                  </span>
                )}
              </span>
              <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                {editId === entry.id ? (
                  <>
                    <button
                      onClick={saveEdit}
                      className="rounded p-1 text-emerald-600 hover:bg-emerald-50 transition-colors"
                      title="Opslaan"
                    >
                      <Plus className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => setEditId(null)}
                      className="rounded p-1 text-muted-foreground hover:bg-muted transition-colors"
                      title="Annuleren"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => startEdit(entry)}
                      className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                      title="Bewerken"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => deleteEntry(entry.id)}
                      className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                      title="Verwijderen"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Per-case breakdown */}
      {summary && summary.per_case.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-foreground mb-3">Overzicht per zaak</h3>
          <div className="space-y-2">
            {summary.per_case.map((cs) => (
              <div key={cs.case_id} className="flex items-center justify-between py-1.5">
                <div className="flex items-center gap-2">
                  <Briefcase className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-sm font-medium text-foreground">{cs.case_number}</span>
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground tabular-nums">
                  <span>{fmtMinutes(cs.total_minutes)}</span>
                  <span className="text-emerald-600">{fmtMinutes(cs.billable_minutes)} decl.</span>
                  <span className="font-medium text-foreground w-24 text-right">
                    {formatCurrency(cs.total_amount)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
