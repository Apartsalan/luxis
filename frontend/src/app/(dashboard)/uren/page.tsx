"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
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
  ChevronDown,
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
import { useTimer } from "@/hooks/use-timer";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api";
import { toast } from "sonner";

// ── Types ────────────────────────────────────────────────────────────────

type ViewMode = "week" | "month" | "day";

interface Contact {
  id: string;
  name: string;
  contact_type: string;
}

// ── Helpers ──────────────────────────────────────────────────────────────

function fmtMinutes(mins: number): string {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return `${h}:${String(m).padStart(2, "0")}`;
}

function toISO(d: Date): string {
  return d.toISOString().split("T")[0];
}

function getWeekDates(weekOffset: number): { start: string; end: string; days: Date[]; monday: Date; friday: Date } {
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
    monday,
    friday,
  };
}

function getMonthDates(monthOffset: number): { start: string; end: string; label: string; monthDate: Date } {
  const now = new Date();
  const d = new Date(now.getFullYear(), now.getMonth() + monthOffset, 1);
  const lastDay = new Date(d.getFullYear(), d.getMonth() + 1, 0);
  return {
    start: toISO(d),
    end: toISO(lastDay),
    label: d.toLocaleDateString("nl-NL", { month: "long", year: "numeric" }),
    monthDate: d,
  };
}

function getDayDate(dayOffset: number): { start: string; end: string; label: string; date: Date } {
  const now = new Date();
  const d = new Date(now);
  d.setDate(now.getDate() + dayOffset);
  d.setHours(0, 0, 0, 0);
  const iso = toISO(d);
  return {
    start: iso,
    end: iso,
    label: d.toLocaleDateString("nl-NL", { weekday: "long", day: "numeric", month: "long", year: "numeric" }),
    date: d,
  };
}

const DAY_NAMES = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"];

// ── Grouped Case Selector (Client → Cases) ─────────────────────────────

function CaseSelector({
  cases,
  value,
  onChange,
  disabled,
  placeholder = "Selecteer dossier...",
}: {
  cases: CaseSummary[];
  value: string;
  onChange: (id: string) => void;
  disabled?: boolean;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [expandedClients, setExpandedClients] = useState<Set<string>>(new Set());
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedCase = cases.find((c) => c.id === value);

  // Group cases by client
  const grouped = useMemo(() => {
    const map = new Map<string, { clientName: string; clientId: string; cases: CaseSummary[] }>();
    for (const c of cases) {
      const clientId = c.client?.id ?? "unknown";
      const clientName = c.client?.name ?? "Onbekende cliënt";
      if (!map.has(clientId)) {
        map.set(clientId, { clientName, clientId, cases: [] });
      }
      map.get(clientId)!.cases.push(c);
    }
    // Sort groups by client name
    return [...map.values()].sort((a, b) => a.clientName.localeCompare(b.clientName));
  }, [cases]);

  // Filter groups based on search
  const filteredGroups = useMemo(() => {
    if (!search) return grouped;
    const q = search.toLowerCase();
    return grouped
      .map((group) => ({
        ...group,
        cases: group.cases.filter(
          (c) =>
            c.case_number.toLowerCase().includes(q) ||
            c.client?.name?.toLowerCase().includes(q) ||
            c.opposing_party?.name?.toLowerCase().includes(q) ||
            c.description?.toLowerCase().includes(q)
        ),
      }))
      .filter((group) => group.cases.length > 0);
  }, [grouped, search]);

  // Auto-expand all groups when searching, or when there's only one group
  const effectiveExpanded = useMemo(() => {
    if (search || filteredGroups.length === 1) {
      return new Set(filteredGroups.map((g) => g.clientId));
    }
    return expandedClients;
  }, [search, filteredGroups, expandedClients]);

  const toggleClient = (clientId: string) => {
    setExpandedClients((prev) => {
      const next = new Set(prev);
      if (next.has(clientId)) {
        next.delete(clientId);
      } else {
        next.add(clientId);
      }
      return next;
    });
  };

  // Auto-expand the group of the selected case
  useEffect(() => {
    if (selectedCase?.client?.id) {
      setExpandedClients((prev) => {
        if (prev.has(selectedCase.client!.id)) return prev;
        const next = new Set(prev);
        next.add(selectedCase.client!.id);
        return next;
      });
    }
  }, [selectedCase]);

  // Close on click outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => !disabled && setOpen(!open)}
        disabled={disabled}
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-left flex items-center justify-between gap-2 hover:bg-muted/50 transition-colors disabled:opacity-50"
      >
        <span className={selectedCase ? "text-foreground truncate" : "text-muted-foreground"}>
          {selectedCase
            ? `${selectedCase.case_number}${selectedCase.client?.name ? ` — ${selectedCase.client.name}` : ""}`
            : placeholder}
        </span>
        <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
      </button>

      {open && (
        <div className="absolute z-50 mt-1 w-full min-w-[320px] rounded-md border border-border bg-card shadow-lg">
          <div className="p-2 border-b border-border">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Zoek op cliënt, dossiernummer..."
              className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
              autoFocus
            />
          </div>
          <div className="max-h-72 overflow-y-auto">
            {filteredGroups.length === 0 ? (
              <p className="px-3 py-6 text-center text-sm text-muted-foreground">
                Geen dossiers gevonden
              </p>
            ) : (
              filteredGroups.map((group) => {
                const isExpanded = effectiveExpanded.has(group.clientId);
                return (
                  <div key={group.clientId}>
                    {/* Client header */}
                    <button
                      type="button"
                      onClick={() => toggleClient(group.clientId)}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm font-medium text-foreground bg-muted/30 hover:bg-muted/60 transition-colors sticky top-0"
                    >
                      <ChevronDown
                        className={`h-3.5 w-3.5 text-muted-foreground shrink-0 transition-transform ${
                          isExpanded ? "" : "-rotate-90"
                        }`}
                      />
                      <Briefcase className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                      <span className="truncate">{group.clientName}</span>
                      <span className="ml-auto text-xs text-muted-foreground shrink-0">
                        {group.cases.length} {group.cases.length === 1 ? "dossier" : "dossiers"}
                      </span>
                    </button>
                    {/* Cases under this client */}
                    {isExpanded && (
                      <div>
                        {group.cases.map((c) => (
                          <button
                            key={c.id}
                            type="button"
                            onClick={() => {
                              onChange(c.id);
                              setOpen(false);
                              setSearch("");
                            }}
                            className={`w-full text-left pl-9 pr-3 py-2 text-sm hover:bg-muted/50 transition-colors flex items-center justify-between ${
                              c.id === value
                                ? "bg-primary/5 text-primary"
                                : "text-foreground"
                            }`}
                          >
                            <div className="min-w-0">
                              <span className="font-mono font-medium">{c.case_number}</span>
                              {c.description && (
                                <span className="text-muted-foreground ml-2 truncate">
                                  — {c.description}
                                </span>
                              )}
                            </div>
                            <span className="text-[10px] text-muted-foreground shrink-0 ml-2 uppercase">
                              {c.case_type}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Page component ───────────────────────────────────────────────────────

export default function UrenPage() {
  const { user } = useAuth();

  // ── View mode & navigation offsets ─────────────────────────────────────
  const [viewMode, setViewMode] = useState<ViewMode>("week");
  const [weekOffset, setWeekOffset] = useState(0);
  const [monthOffset, setMonthOffset] = useState(0);
  const [dayOffset, setDayOffset] = useState(0);

  // Compute date range based on view mode
  const dateRange = useMemo(() => {
    if (viewMode === "week") {
      const w = getWeekDates(weekOffset);
      return { start: w.start, end: w.end };
    } else if (viewMode === "month") {
      const m = getMonthDates(monthOffset);
      return { start: m.start, end: m.end };
    } else {
      const d = getDayDate(dayOffset);
      return { start: d.start, end: d.end };
    }
  }, [viewMode, weekOffset, monthOffset, dayOffset]);

  const week = getWeekDates(weekOffset);
  const month = getMonthDates(monthOffset);
  const dayInfo = getDayDate(dayOffset);
  const isCurrentPeriod =
    viewMode === "week" ? weekOffset === 0 :
    viewMode === "month" ? monthOffset === 0 :
    dayOffset === 0;

  // Filters
  const [filterCaseId, setFilterCaseId] = useState("");
  const [filterBillable, setFilterBillable] = useState<string>("");
  const [filterContactId, setFilterContactId] = useState("");

  // Contacts for filter
  const [contacts, setContacts] = useState<Contact[]>([]);
  useEffect(() => {
    api("/api/relations?contact_type=company&per_page=200")
      .then((res) => res.ok ? res.json() : null)
      .then((data) => {
        if (data?.items) setContacts(data.items);
      })
      .catch(() => {});
  }, []);

  // Query data
  const {
    data: entries,
    isLoading,
    isError,
    error,
    refetch,
  } = useTimeEntries({
    date_from: dateRange.start,
    date_to: dateRange.end,
    case_id: filterCaseId || undefined,
    billable: filterBillable === "" ? undefined : filterBillable === "true",
    contact_id: filterContactId || undefined,
  });

  const { data: summary } = useTimeEntrySummary({
    date_from: dateRange.start,
    date_to: dateRange.end,
  });

  const { data: todayEntries } = useMyTodayEntries();

  const { data: casesData } = useCases({ per_page: 200 });
  const cases = casesData?.items ?? [];

  // Mutations
  const createMutation = useCreateTimeEntry();
  const updateMutation = useUpdateTimeEntry();
  const deleteMutation = useDeleteTimeEntry();

  // ── Global Timer (from context — persists across pages) ─────────────
  const {
    timer,
    startTimer: globalStartTimer,
    stopTimer: globalStopTimer,
    setTimerCase: globalSetTimerCase,
    isExpanded: timerExpanded,
    setIsExpanded: setTimerExpanded,
  } = useTimer();

  // Aliases for backward compatibility with the timer card UI
  const timerRunning = timer.running;
  const timerSeconds = timer.seconds;
  const timerCaseId = timer.caseId;
  const setTimerCaseId = (id: string) => {
    const c = cases.find((cs) => cs.id === id);
    const label = c ? `${c.case_number}${c.client?.name ? ` — ${c.client.name}` : ""}` : "";
    globalSetTimerCase(id, label);
  };

  const startTimer = () => {
    const c = cases.find((cs) => cs.id === timerCaseId);
    const label = c ? `${c.case_number}${c.client?.name ? ` — ${c.client.name}` : ""}` : "";
    globalStartTimer(timerCaseId, label);
  };

  const stopTimer = globalStopTimer;

  // ── New entry form ───────────────────────────────────────────────────
  const [showForm, setShowForm] = useState(false);
  const [formCaseId, setFormCaseId] = useState("");
  const [formDate, setFormDate] = useState(toISO(new Date()));
  const [formHours, setFormHours] = useState("");
  const [formMinutes, setFormMinutes] = useState("");
  const [formActivity, setFormActivity] = useState("other");
  const [formDescription, setFormDescription] = useState("");
  const [formBillable, setFormBillable] = useState(true);
  const defaultRate = user?.default_hourly_rate != null ? String(user.default_hourly_rate) : "";
  const [formRate, setFormRate] = useState(defaultRate);
  const [formDiscount, setFormDiscount] = useState(false);
  const [formBillableMinutes, setFormBillableMinutes] = useState("");

  const resetForm = () => {
    setFormCaseId("");
    setFormDate(toISO(new Date()));
    setFormHours("");
    setFormMinutes("");
    setFormActivity("other");
    setFormDescription("");
    setFormBillable(true);
    setFormRate(defaultRate);
    setFormDiscount(false);
    setFormBillableMinutes("");
  };

  const submitEntry = async () => {
    const totalMinutes = (parseInt(formHours || "0") * 60) + parseInt(formMinutes || "0");
    if (!formCaseId || totalMinutes <= 0) {
      toast.error("Selecteer een dossier en voer een geldige duur in");
      return;
    }
    try {
      const payload: Record<string, unknown> = {
        case_id: formCaseId,
        date: formDate,
        duration_minutes: totalMinutes,
        activity_type: formActivity,
        description: formDescription?.trim() || null,
        billable: formBillable,
        hourly_rate: formRate ? parseFloat(formRate) : null,
      };
      if (formDiscount && formBillableMinutes !== "") {
        payload.billable_minutes = parseInt(formBillableMinutes) || 0;
      }
      await createMutation.mutateAsync(payload as any);
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
  const [editDate, setEditDate] = useState("");
  const [editBillableMinutes, setEditBillableMinutes] = useState("");

  const startEdit = (entry: TimeEntry) => {
    setEditId(entry.id);
    setEditMinutes(String(entry.duration_minutes));
    setEditDescription(entry.description || "");
    setEditDate(entry.date);
    setEditBillableMinutes(
      entry.billable_minutes != null && entry.billable_minutes !== entry.duration_minutes
        ? String(entry.billable_minutes)
        : ""
    );
  };

  const saveEdit = async () => {
    if (!editId) return;
    try {
      const data: Record<string, unknown> = {
        duration_minutes: parseInt(editMinutes) || 1,
        description: editDescription?.trim() || null,
        date: editDate,
      };
      if (editBillableMinutes !== "") {
        data.billable_minutes = parseInt(editBillableMinutes) || 0;
      } else {
        data.billable_minutes = null;
      }
      await updateMutation.mutateAsync({
        id: editId,
        data: data as any,
      });
      toast.success("Bijgewerkt");
      setEditId(null);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const deleteEntry = async (id: string) => {
    if (!confirm("Weet je zeker dat je deze registratie wilt verwijderen?")) return;
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

  // ── Navigation helpers ────────────────────────────────────────────────
  const navigateBack = () => {
    if (viewMode === "week") setWeekOffset((w) => w - 1);
    else if (viewMode === "month") setMonthOffset((m) => m - 1);
    else setDayOffset((d) => d - 1);
  };

  const navigateForward = () => {
    if (viewMode === "week") setWeekOffset((w) => w + 1);
    else if (viewMode === "month") setMonthOffset((m) => m + 1);
    else setDayOffset((d) => d + 1);
  };

  const navigateToday = () => {
    if (viewMode === "week") setWeekOffset(0);
    else if (viewMode === "month") setMonthOffset(0);
    else setDayOffset(0);
  };

  const periodLabel = useMemo(() => {
    if (viewMode === "week") {
      return `${week.monday.toLocaleDateString("nl-NL", { day: "numeric", month: "short" })} — ${week.friday.toLocaleDateString("nl-NL", { day: "numeric", month: "short", year: "numeric" })}`;
    } else if (viewMode === "month") {
      return month.label;
    } else {
      return dayInfo.label;
    }
  }, [viewMode, week, month, dayInfo]);

  const todayButtonLabel = viewMode === "week" ? "Deze week" : viewMode === "month" ? "Deze maand" : "Vandaag";

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
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Timer card */}
        <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground mb-3">
            <Timer className="h-4 w-4" />
            Stopwatch
          </div>
          <div className="text-2xl font-mono font-bold text-foreground mb-3 tabular-nums">
            {timerDisplay}
          </div>
          <div className="mb-2">
            <CaseSelector
              cases={cases}
              value={timerCaseId}
              onChange={setTimerCaseId}
              disabled={timerRunning}
              placeholder="Selecteer dossier..."
            />
          </div>
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
          <p className="text-sm font-medium text-muted-foreground">Totaal deze {viewMode === "week" ? "week" : viewMode === "month" ? "maand" : "dag"}</p>
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
          <p className="mt-0.5 text-xs text-muted-foreground">deze {viewMode === "week" ? "week" : viewMode === "month" ? "maand" : "dag"}</p>
        </div>
      </div>

      {/* View mode switcher + navigation + filters */}
      <div className="flex flex-col gap-3">
        {/* Row 1: View mode tabs + navigation */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            {/* View mode tabs */}
            <div className="flex items-center rounded-lg border border-border bg-muted/30 p-0.5">
              {(["dag", "week", "maand"] as const).map((label) => {
                const mode = label === "dag" ? "day" : label === "maand" ? "month" : "week";
                return (
                  <button
                    key={mode}
                    onClick={() => setViewMode(mode)}
                    className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                      viewMode === mode
                        ? "bg-background text-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {label.charAt(0).toUpperCase() + label.slice(1)}
                  </button>
                );
              })}
            </div>

            {/* Period navigation */}
            <div className="flex items-center gap-2">
              <button
                onClick={navigateBack}
                className="rounded-md border border-border p-1.5 hover:bg-muted transition-colors"
                aria-label="Vorige periode"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={navigateToday}
                className="rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors"
                disabled={isCurrentPeriod}
              >
                {todayButtonLabel}
              </button>
              <button
                onClick={navigateForward}
                className="rounded-md border border-border p-1.5 hover:bg-muted transition-colors"
                aria-label="Volgende periode"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
              <span className="ml-2 text-sm text-muted-foreground">
                {periodLabel}
              </span>
            </div>
          </div>

          {/* Filters */}
          <div className="flex items-center gap-2 flex-wrap">
            <div className="w-56">
              <CaseSelector
                cases={cases}
                value={filterCaseId}
                onChange={setFilterCaseId}
                placeholder="Alle dossiers"
              />
            </div>
            <select
              value={filterContactId}
              onChange={(e) => setFilterContactId(e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-1.5 text-sm"
            >
              <option value="">Alle relaties</option>
              {contacts.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
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
      </div>

      {/* Week day bar (only shown in week view) */}
      {viewMode === "week" && (
        <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
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
      )}

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
              <label className="block text-xs font-medium text-muted-foreground mb-1">Dossier *</label>
              <CaseSelector
                cases={cases}
                value={formCaseId}
                onChange={setFormCaseId}
                placeholder="Selecteer dossier..."
              />
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
            <div className="flex items-end gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formBillable}
                  onChange={(e) => setFormBillable(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-primary"
                />
                <span className="text-sm text-foreground">Declarabel</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formDiscount}
                  onChange={(e) => setFormDiscount(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-primary"
                />
                <span className="text-sm text-foreground">Korting geven</span>
              </label>
            </div>
          </div>
          {formDiscount && (
            <div className="mt-3 max-w-xs">
              <label className="block text-xs font-medium text-muted-foreground mb-1">Te factureren (minuten)</label>
              <input
                type="number"
                min="0"
                placeholder="bijv. 45"
                value={formBillableMinutes}
                onChange={(e) => setFormBillableMinutes(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Standaard: zelfde als duur. Vul hier een lager aantal in voor korting.
              </p>
            </div>
          )}
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
              <div className="h-4 w-20 rounded skeleton" />
              <div className="h-4 w-16 rounded skeleton" />
              <div className="h-4 w-32 rounded skeleton flex-1" />
              <div className="h-4 w-14 rounded skeleton" />
            </div>
          ))}
        </div>
      ) : !entries || entries.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/50 py-20">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
            <Clock className="h-8 w-8 text-muted-foreground/50" />
          </div>
          <p className="mt-5 text-base font-medium text-foreground">
            Geen registraties {viewMode === "week" ? "deze week" : viewMode === "month" ? "deze maand" : "vandaag"}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            Gebruik de stopwatch of klik op &quot;Nieuwe registratie&quot;
          </p>
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card shadow-sm overflow-x-auto">
          <div className="min-w-[700px]">
          {/* Table header */}
          <div className="grid grid-cols-[100px_80px_1fr_120px_80px_60px_80px_60px] gap-2 px-5 py-2.5 border-b border-border bg-muted/50 text-xs font-medium text-muted-foreground">
            <span>Datum</span>
            <span>Dossier</span>
            <span>Omschrijving</span>
            <span>Activiteit</span>
            <span className="text-right">Duur</span>
            <span className="text-center">Decl.</span>
            <span className="text-center">Factuur</span>
            <span></span>
          </div>

          {/* Table rows */}
          {entries.map((entry) => (
            <div
              key={entry.id}
              className="group grid grid-cols-[100px_80px_1fr_120px_80px_60px_80px_60px] gap-2 items-center px-5 py-3 border-b border-border last:border-0 hover:bg-muted/30 transition-colors"
            >
              {editId === entry.id ? (
                <input
                  type="date"
                  value={editDate}
                  onChange={(e) => setEditDate(e.target.value)}
                  className="rounded border border-input bg-background px-1.5 py-1 text-sm w-full"
                />
              ) : (
                <span className="text-sm text-foreground tabular-nums">
                  {new Date(entry.date + "T00:00:00").toLocaleDateString("nl-NL", { day: "numeric", month: "short" })}
                </span>
              )}
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
                <div className="space-y-1">
                  <input
                    type="number"
                    value={editMinutes}
                    onChange={(e) => setEditMinutes(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && saveEdit()}
                    className="rounded border border-input bg-background px-2 py-1 text-sm text-right w-full"
                    min="1"
                    title="Duur (minuten)"
                  />
                  <input
                    type="number"
                    value={editBillableMinutes}
                    onChange={(e) => setEditBillableMinutes(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && saveEdit()}
                    className="rounded border border-input bg-background px-2 py-1 text-xs text-right w-full"
                    min="0"
                    placeholder="factur."
                    title="Te factureren minuten (leeg = zelfde als duur)"
                  />
                </div>
              ) : (
                <div className="text-right">
                  <span className="text-sm font-medium text-foreground tabular-nums">
                    {fmtMinutes(entry.duration_minutes)}
                  </span>
                  {entry.billable_minutes != null && entry.billable_minutes !== entry.duration_minutes && (
                    <span className="block text-[10px] text-muted-foreground tabular-nums">
                      facturabel: {fmtMinutes(entry.billable_minutes)}
                    </span>
                  )}
                </div>
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
              <span className="text-center">
                {entry.invoiced && entry.invoice_number ? (
                  <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-medium text-blue-700">
                    {entry.invoice_number}
                  </span>
                ) : (
                  <span className="text-[10px] text-muted-foreground">—</span>
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
        </div>
      )}

      {/* Per-case breakdown */}
      {summary && summary.per_case.length > 0 && (
        <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-foreground mb-3">Overzicht per dossier</h3>
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
