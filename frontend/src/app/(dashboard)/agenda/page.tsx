"use client";

import { useState, useMemo } from "react";
import { useUnsavedWarning } from "@/hooks/use-unsaved-warning";
import Link from "next/link";
import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  Briefcase,
  ShieldCheck,
  Plus,
  X,
  Clock,
  MapPin,
  Pencil,
  Trash2,
  Phone,
  Users,
  AlertTriangle,
  Bell,
  Gavel,
  MoreHorizontal,
  RefreshCw,
  Cloud,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCalendarEvents, type CalendarEvent } from "@/hooks/use-calendar";
import {
  useCreateCalendarEvent,
  useUpdateCalendarEvent,
  useDeleteCalendarEvent,
  EVENT_TYPES,
  EVENT_TYPE_LABELS,
  type CalendarEventCreateInput,
  type CalendarEventUpdateInput,
} from "@/hooks/use-calendar-events";
import { useSyncCalendar } from "@/hooks/use-sync-calendar";
import { TASK_TYPE_LABELS } from "@/hooks/use-workflow";
import { useCases } from "@/hooks/use-cases";
import type { CaseSummary } from "@/hooks/use-cases";
import { useRelations } from "@/hooks/use-relations";
import type { Contact } from "@/hooks/use-relations";
import { QueryError } from "@/components/query-error";

// ── Dutch day names (week starts Monday) ──────────────────────────────────────
const DAY_NAMES_SHORT = ["ma", "di", "wo", "do", "vr", "za", "zo"];
const DAY_NAMES_FULL = [
  "maandag",
  "dinsdag",
  "woensdag",
  "donderdag",
  "vrijdag",
  "zaterdag",
  "zondag",
];

// ── Date helpers ──────────────────────────────────────────────────────────────

/** Format YYYY-MM-DD from a Date */
function toDateString(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/** Is the same calendar day? */
function isSameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

/** Get Monday of the week containing `date` */
function getMonday(date: Date): Date {
  const d = new Date(date);
  const day = d.getDay(); // 0=Sun, 1=Mon, ...
  const diff = day === 0 ? -6 : 1 - day;
  d.setDate(d.getDate() + diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

/** Get all 42 days (6 weeks) for the month grid starting on Monday */
function getMonthGridDates(year: number, month: number): Date[] {
  const firstOfMonth = new Date(year, month, 1);
  const startMonday = getMonday(firstOfMonth);
  const dates: Date[] = [];
  for (let i = 0; i < 42; i++) {
    const d = new Date(startMonday);
    d.setDate(startMonday.getDate() + i);
    dates.push(d);
  }
  return dates;
}

/** Get 7 days of the week containing `date`, starting Monday */
function getWeekDates(date: Date): Date[] {
  const monday = getMonday(date);
  const dates: Date[] = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    dates.push(d);
  }
  return dates;
}

/** Group events by date string key */
function groupEventsByDate(
  events: CalendarEvent[]
): Record<string, CalendarEvent[]> {
  const grouped: Record<string, CalendarEvent[]> = {};
  for (const event of events) {
    const key = event.date.slice(0, 10); // YYYY-MM-DD
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(event);
  }
  return grouped;
}

/** Format month + year in Dutch */
function formatMonthYear(date: Date): string {
  return date.toLocaleDateString("nl-NL", { month: "long", year: "numeric" });
}

/** Format a full Dutch date for the detail header */
function formatFullDate(date: Date): string {
  return date.toLocaleDateString("nl-NL", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

/** Format time string HH:MM from ISO datetime */
function formatTime(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleTimeString("nl-NL", { hour: "2-digit", minute: "2-digit" });
}

// ── Event type icon mapping ──────────────────────────────────────────────────

const EVENT_TYPE_ICONS: Record<string, typeof Briefcase> = {
  task: Briefcase,
  kyc_review: ShieldCheck,
  appointment: Calendar,
  hearing: Gavel,
  deadline: AlertTriangle,
  reminder: Bell,
  meeting: Users,
  call: Phone,
  other: MoreHorizontal,
};

function getEventIcon(eventType: string) {
  return EVENT_TYPE_ICONS[eventType] ?? Calendar;
}

function getEventLabel(eventType: string) {
  return EVENT_TYPE_LABELS[eventType] ?? eventType;
}

// ── Main Page Component ───────────────────────────────────────────────────────

type ViewMode = "month" | "week";

export default function AgendaPage() {
  const today = useMemo(() => new Date(), []);
  const [currentDate, setCurrentDate] = useState<Date>(today);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("month");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null);
  const [prefillDate, setPrefillDate] = useState<string | null>(null);

  // Compute date range for API call
  const { dateFrom, dateTo, gridDates } = useMemo(() => {
    if (viewMode === "month") {
      const dates = getMonthGridDates(
        currentDate.getFullYear(),
        currentDate.getMonth()
      );
      return {
        dateFrom: toDateString(dates[0]),
        dateTo: toDateString(dates[dates.length - 1]),
        gridDates: dates,
      };
    } else {
      const dates = getWeekDates(currentDate);
      return {
        dateFrom: toDateString(dates[0]),
        dateTo: toDateString(dates[dates.length - 1]),
        gridDates: dates,
      };
    }
  }, [currentDate, viewMode]);

  const {
    data: events,
    isLoading,
    isError,
    error,
    refetch,
  } = useCalendarEvents(dateFrom, dateTo);

  const syncMutation = useSyncCalendar();
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  function handleSync() {
    setSyncMessage(null);
    syncMutation.mutate(undefined, {
      onSuccess: (stats) => {
        setSyncMessage(
          `Gesynchroniseerd: ${stats.created} nieuw, ${stats.updated} bijgewerkt, ${stats.deleted} verwijderd`
        );
        setTimeout(() => setSyncMessage(null), 5000);
      },
      onError: (err) => {
        setSyncMessage(err instanceof Error ? err.message : "Synchronisatie mislukt");
        setTimeout(() => setSyncMessage(null), 5000);
      },
    });
  }

  const eventsByDate = useMemo(
    () => groupEventsByDate(events ?? []),
    [events]
  );

  // Navigation handlers
  function navigatePrev() {
    setSelectedDate(null);
    if (viewMode === "month") {
      setCurrentDate(
        (prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1)
      );
    } else {
      setCurrentDate((prev) => {
        const d = new Date(prev);
        d.setDate(d.getDate() - 7);
        return d;
      });
    }
  }

  function navigateNext() {
    setSelectedDate(null);
    if (viewMode === "month") {
      setCurrentDate(
        (prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1)
      );
    } else {
      setCurrentDate((prev) => {
        const d = new Date(prev);
        d.setDate(d.getDate() + 7);
        return d;
      });
    }
  }

  function goToToday() {
    setSelectedDate(null);
    setCurrentDate(new Date());
  }

  function handleDayClick(date: Date) {
    setSelectedDate((prev) =>
      prev && isSameDay(prev, date) ? null : date
    );
  }

  function handleAddEvent(date?: Date) {
    setEditingEvent(null);
    setPrefillDate(date ? toDateString(date) : null);
    setDialogOpen(true);
  }

  function handleEditEvent(event: CalendarEvent) {
    setEditingEvent(event);
    setPrefillDate(null);
    setDialogOpen(true);
  }

  function handleDialogClose() {
    setDialogOpen(false);
    setEditingEvent(null);
    setPrefillDate(null);
  }

  // Events for selected day
  const selectedDayEvents = selectedDate
    ? eventsByDate[toDateString(selectedDate)] ?? []
    : [];

  // Error state
  if (isError) {
    return (
      <QueryError message={error?.message} onRetry={() => refetch()} />
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Agenda</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Overzicht van taken en afspraken
          </p>
        </div>
        <button
          onClick={() => handleAddEvent()}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Nieuw event
        </button>
      </div>

      {/* Calendar card */}
      <div className="rounded-xl border border-border bg-card">
        {/* Toolbar */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between px-5 py-4 border-b border-border">
          {/* Left: navigation */}
          <div className="flex items-center gap-2">
            <button
              onClick={navigatePrev}
              className="flex h-8 w-8 items-center justify-center rounded-md border border-border hover:bg-muted/50 transition-colors"
              title={viewMode === "month" ? "Vorige maand" : "Vorige week"}
            >
              <ChevronLeft className="h-4 w-4 text-foreground" />
            </button>
            <button
              onClick={navigateNext}
              className="flex h-8 w-8 items-center justify-center rounded-md border border-border hover:bg-muted/50 transition-colors"
              title={viewMode === "month" ? "Volgende maand" : "Volgende week"}
            >
              <ChevronRight className="h-4 w-4 text-foreground" />
            </button>
            <h2 className="text-sm font-semibold text-card-foreground capitalize ml-2">
              {viewMode === "month"
                ? formatMonthYear(currentDate)
                : `Week van ${gridDates[0].toLocaleDateString("nl-NL", { day: "numeric", month: "long" })} - ${gridDates[6].toLocaleDateString("nl-NL", { day: "numeric", month: "long", year: "numeric" })}`}
            </h2>
          </div>

          {/* Right: sync + view toggle + today button */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleSync}
              disabled={syncMutation.isPending}
              className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted/50 transition-colors disabled:opacity-50"
              title="Outlook agenda synchroniseren"
            >
              <RefreshCw className={cn("h-3.5 w-3.5", syncMutation.isPending && "animate-spin")} />
              Sync
            </button>
            <button
              onClick={goToToday}
              className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted/50 transition-colors"
            >
              Vandaag
            </button>
            <div className="flex rounded-md border border-border overflow-hidden">
              <button
                onClick={() => setViewMode("month")}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium transition-colors",
                  viewMode === "month"
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground hover:bg-muted/50"
                )}
              >
                Maand
              </button>
              <button
                onClick={() => setViewMode("week")}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium transition-colors border-l border-border",
                  viewMode === "week"
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground hover:bg-muted/50"
                )}
              >
                Week
              </button>
            </div>
          </div>
        </div>

        {/* Sync feedback */}
        {syncMessage && (
          <div className={cn(
            "mx-5 mt-3 px-3 py-2 rounded-lg text-xs font-medium",
            syncMutation.isError
              ? "bg-destructive/10 text-destructive"
              : "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400"
          )}>
            <Cloud className="h-3.5 w-3.5 inline mr-1.5" />
            {syncMessage}
          </div>
        )}

        {/* Loading state */}
        {isLoading ? (
          <div className="p-5">
            <div className="grid grid-cols-7 gap-1">
              {[...Array(7)].map((_, i) => (
                <div key={i} className="h-6 rounded skeleton" />
              ))}
              {[...Array(35)].map((_, i) => (
                <div key={i} className="h-20 rounded skeleton" />
              ))}
            </div>
          </div>
        ) : viewMode === "month" ? (
          <MonthView
            gridDates={gridDates}
            currentDate={currentDate}
            today={today}
            selectedDate={selectedDate}
            eventsByDate={eventsByDate}
            onDayClick={handleDayClick}
          />
        ) : (
          <WeekView
            gridDates={gridDates}
            today={today}
            selectedDate={selectedDate}
            eventsByDate={eventsByDate}
            onDayClick={handleDayClick}
          />
        )}
      </div>

      {/* Selected day detail panel */}
      {selectedDate && (
        <DayDetailPanel
          date={selectedDate}
          events={selectedDayEvents}
          onClose={() => setSelectedDate(null)}
          onAddEvent={() => handleAddEvent(selectedDate)}
          onEditEvent={handleEditEvent}
        />
      )}

      {/* Mobile compact list (visible on small screens when no day selected) */}
      {!selectedDate && !isLoading && (
        <div className="sm:hidden space-y-3">
          <MobileEventList
            gridDates={gridDates}
            eventsByDate={eventsByDate}
            today={today}
            onDayClick={handleDayClick}
          />
        </div>
      )}

      {/* Event dialog */}
      {dialogOpen && (
        <EventDialog
          event={editingEvent}
          prefillDate={prefillDate}
          onClose={handleDialogClose}
          onSaved={() => {
            handleDialogClose();
            refetch();
          }}
        />
      )}
    </div>
  );
}

// ── Event Dialog (Create / Edit) ─────────────────────────────────────────────

function EventDialog({
  event,
  prefillDate,
  onClose,
  onSaved,
}: {
  event: CalendarEvent | null;
  prefillDate: string | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const isEdit = !!event;
  const createMutation = useCreateCalendarEvent();
  const updateMutation = useUpdateCalendarEvent();
  const deleteMutation = useDeleteCalendarEvent();

  const { data: cases } = useCases({ per_page: 200 });
  const { data: relations } = useRelations({ per_page: 200 });

  // Default times
  const defaultDate = prefillDate || toDateString(new Date());
  const defaultStart = event?.start_time
    ? event.start_time.slice(0, 16)
    : `${defaultDate}T09:00`;
  const defaultEnd = event?.end_time
    ? event.end_time.slice(0, 16)
    : `${defaultDate}T10:00`;

  const [title, setTitle] = useState(event?.title ?? "");
  const [eventType, setEventType] = useState(
    event?.event_type ?? "appointment"
  );
  const [startTime, setStartTime] = useState(defaultStart);
  const [endTime, setEndTime] = useState(defaultEnd);
  const [allDay, setAllDay] = useState(event?.all_day ?? false);
  const [location, setLocation] = useState(event?.location ?? "");
  const [description, setDescription] = useState(event?.description ?? "");
  const [caseId, setCaseId] = useState(event?.case_id ?? "");
  const [contactId, setContactId] = useState(event?.contact_id ?? "");
  const [reminderMinutes, setReminderMinutes] = useState<number | null>(30);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useUnsavedWarning(!!title || !!description || !!location);

  const isSaving =
    createMutation.isPending || updateMutation.isPending;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;

    const start = allDay ? `${startTime.slice(0, 10)}T00:00:00` : `${startTime}:00`;
    const end = allDay ? `${endTime.slice(0, 10)}T23:59:59` : `${endTime}:00`;

    if (isEdit && event?.user_event_id) {
      const data: CalendarEventUpdateInput = {
        title: title.trim(),
        event_type: eventType,
        start_time: start,
        end_time: end,
        all_day: allDay,
        location: location.trim() || null,
        description: description.trim() || null,
        case_id: caseId || null,
        contact_id: contactId || null,
        reminder_minutes: reminderMinutes,
      };
      await updateMutation.mutateAsync({
        id: event.user_event_id,
        data,
      });
    } else {
      const data: CalendarEventCreateInput = {
        title: title.trim(),
        event_type: eventType,
        start_time: start,
        end_time: end,
        all_day: allDay,
        location: location.trim() || null,
        description: description.trim() || null,
        case_id: caseId || null,
        contact_id: contactId || null,
        reminder_minutes: reminderMinutes,
      };
      await createMutation.mutateAsync(data);
    }
    onSaved();
  }

  async function handleDelete() {
    if (!event?.user_event_id) return;
    await deleteMutation.mutateAsync(event.user_event_id);
    onSaved();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 animate-fade-in">
      <div
        className="w-full max-w-lg rounded-xl border border-border bg-card shadow-xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h2 className="text-base font-semibold text-card-foreground">
            {isEdit ? "Event bewerken" : "Nieuw event"}
          </h2>
          <button
            onClick={onClose}
            className="flex h-7 w-7 items-center justify-center rounded-md hover:bg-muted/50 transition-colors"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* Title */}
          <div>
            <label htmlFor="agenda-title" className="block text-xs font-medium text-muted-foreground mb-1.5">
              Titel *
            </label>
            <input
              id="agenda-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Bijv. Overleg met cliënt"
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30"
              required
              autoFocus
            />
          </div>

          {/* Event type grid */}
          <div>
            <label className="block text-xs font-medium text-muted-foreground mb-1.5">
              Type
            </label>
            <div className="grid grid-cols-4 gap-1.5">
              {EVENT_TYPES.map((t) => {
                const Icon = getEventIcon(t.value);
                const isActive = eventType === t.value;
                return (
                  <button
                    key={t.value}
                    type="button"
                    onClick={() => setEventType(t.value)}
                    className={cn(
                      "flex flex-col items-center gap-1 rounded-lg px-2 py-2 text-[10px] font-medium transition-colors border",
                      isActive
                        ? "border-primary bg-primary/5 text-primary"
                        : "border-transparent bg-muted/30 text-muted-foreground hover:bg-muted/50"
                    )}
                  >
                    <Icon
                      className="h-3.5 w-3.5"
                      style={{ color: isActive ? t.color : undefined }}
                    />
                    {t.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* All day toggle */}
          <label htmlFor="agenda-all-day" className="flex items-center gap-2 cursor-pointer">
            <input
              id="agenda-all-day"
              type="checkbox"
              checked={allDay}
              onChange={(e) => setAllDay(e.target.checked)}
              className="h-4 w-4 rounded border-border text-primary focus:ring-primary/30"
            />
            <span className="text-sm text-foreground">Hele dag</span>
          </label>

          {/* Date / Time */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="agenda-start" className="block text-xs font-medium text-muted-foreground mb-1.5">
                {allDay ? "Startdatum" : "Start"}
              </label>
              <input
                id="agenda-start"
                type={allDay ? "date" : "datetime-local"}
                value={allDay ? startTime.slice(0, 10) : startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
                required
              />
            </div>
            <div>
              <label htmlFor="agenda-end" className="block text-xs font-medium text-muted-foreground mb-1.5">
                {allDay ? "Einddatum" : "Einde"}
              </label>
              <input
                id="agenda-end"
                type={allDay ? "date" : "datetime-local"}
                value={allDay ? endTime.slice(0, 10) : endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
                required
              />
            </div>
          </div>

          {/* Location */}
          <div>
            <label htmlFor="agenda-location" className="block text-xs font-medium text-muted-foreground mb-1.5">
              Locatie
            </label>
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <input
                id="agenda-location"
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Bijv. Kantoor, Rechtbank Amsterdam"
                className="w-full rounded-lg border border-border bg-background pl-9 pr-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
          </div>

          {/* Case & Contact pickers */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="agenda-case" className="block text-xs font-medium text-muted-foreground mb-1.5">
                Zaak
              </label>
              <select
                id="agenda-case"
                value={caseId}
                onChange={(e) => setCaseId(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
              >
                <option value="">Geen zaak</option>
                {(cases?.items ?? []).map((c: CaseSummary) => (
                  <option key={c.id} value={c.id}>
                    {c.case_number} — {c.description}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="agenda-contact" className="block text-xs font-medium text-muted-foreground mb-1.5">
                Relatie
              </label>
              <select
                id="agenda-contact"
                value={contactId}
                onChange={(e) => setContactId(e.target.value)}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
              >
                <option value="">Geen relatie</option>
                {(relations?.items ?? []).map((r: Contact) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Reminder */}
          <div>
            <label htmlFor="agenda-reminder" className="block text-xs font-medium text-muted-foreground mb-1.5">
              Herinnering
            </label>
            <select
              id="agenda-reminder"
              value={reminderMinutes ?? ""}
              onChange={(e) =>
                setReminderMinutes(
                  e.target.value === "" ? null : Number(e.target.value)
                )
              }
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              <option value="">Geen herinnering</option>
              <option value="5">5 minuten van tevoren</option>
              <option value="15">15 minuten van tevoren</option>
              <option value="30">30 minuten van tevoren</option>
              <option value="60">1 uur van tevoren</option>
              <option value="1440">1 dag van tevoren</option>
            </select>
          </div>

          {/* Description */}
          <div>
            <label htmlFor="agenda-description" className="block text-xs font-medium text-muted-foreground mb-1.5">
              Omschrijving
            </label>
            <textarea
              id="agenda-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Eventuele notities..."
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-2 border-t border-border">
            {isEdit && event?.user_event_id ? (
              <div>
                {showDeleteConfirm ? (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-destructive">Weet je het zeker?</span>
                    <button
                      type="button"
                      onClick={handleDelete}
                      disabled={deleteMutation.isPending}
                      className="inline-flex items-center gap-1 rounded-md bg-destructive px-2.5 py-1.5 text-xs font-medium text-destructive-foreground hover:bg-destructive/90 transition-colors disabled:opacity-50"
                    >
                      <Trash2 className="h-3 w-3" />
                      Verwijderen
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowDeleteConfirm(false)}
                      className="text-xs text-muted-foreground hover:text-foreground"
                    >
                      Annuleren
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => setShowDeleteConfirm(true)}
                    className="inline-flex items-center gap-1 rounded-md border border-destructive/30 px-2.5 py-1.5 text-xs font-medium text-destructive hover:bg-destructive/5 transition-colors"
                  >
                    <Trash2 className="h-3 w-3" />
                    Verwijderen
                  </button>
                )}
              </div>
            ) : (
              <div />
            )}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-md border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-muted/50 transition-colors"
              >
                Annuleren
              </button>
              <button
                type="submit"
                disabled={isSaving || !title.trim()}
                className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {isSaving
                  ? "Opslaan..."
                  : isEdit
                    ? "Bijwerken"
                    : "Aanmaken"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Month View Grid ───────────────────────────────────────────────────────────

function MonthView({
  gridDates,
  currentDate,
  today,
  selectedDate,
  eventsByDate,
  onDayClick,
}: {
  gridDates: Date[];
  currentDate: Date;
  today: Date;
  selectedDate: Date | null;
  eventsByDate: Record<string, CalendarEvent[]>;
  onDayClick: (date: Date) => void;
}) {
  const currentMonth = currentDate.getMonth();

  return (
    <div className="p-3 sm:p-5">
      {/* Day name headers */}
      <div className="hidden sm:grid grid-cols-7 gap-1 mb-1">
        {DAY_NAMES_SHORT.map((name) => (
          <div
            key={name}
            className="text-center text-xs font-medium text-muted-foreground py-2 uppercase tracking-wider"
          >
            {name}
          </div>
        ))}
      </div>

      {/* Day cells */}
      <div className="hidden sm:grid grid-cols-7 gap-1">
        {gridDates.map((date) => {
          const dateKey = toDateString(date);
          const dayEvents = eventsByDate[dateKey] ?? [];
          const isCurrentMonth = date.getMonth() === currentMonth;
          const isToday = isSameDay(date, today);
          const isSelected = selectedDate ? isSameDay(date, selectedDate) : false;

          return (
            <button
              key={dateKey}
              onClick={() => onDayClick(date)}
              className={cn(
                "relative flex flex-col items-start rounded-lg p-2 min-h-[5rem] text-left transition-colors",
                isCurrentMonth
                  ? "hover:bg-muted/50"
                  : "opacity-40 hover:opacity-60",
                isSelected && "ring-2 ring-primary bg-primary/5",
                isToday && !isSelected && "bg-primary/5"
              )}
            >
              {/* Date number */}
              <span
                className={cn(
                  "inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium",
                  isToday
                    ? "bg-primary text-primary-foreground"
                    : isCurrentMonth
                      ? "text-foreground"
                      : "text-muted-foreground"
                )}
              >
                {date.getDate()}
              </span>

              {/* Event dots / chips */}
              <div className="mt-1 w-full space-y-0.5">
                {dayEvents.slice(0, 3).map((event) => (
                  <div
                    key={event.id}
                    className="flex items-center gap-1 truncate"
                    title={event.title}
                  >
                    <div
                      className="h-1.5 w-1.5 shrink-0 rounded-full"
                      style={{ backgroundColor: event.color || "#6b7280" }}
                    />
                    <span className="text-[10px] leading-tight text-foreground truncate">
                      {event.source === "user" && event.start_time && !event.all_day
                        ? `${formatTime(event.start_time)} ${event.title}`
                        : event.title}
                    </span>
                  </div>
                ))}
                {dayEvents.length > 3 && (
                  <span className="text-[10px] text-muted-foreground">
                    +{dayEvents.length - 3} meer
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ── Week View ─────────────────────────────────────────────────────────────────

function WeekView({
  gridDates,
  today,
  selectedDate,
  eventsByDate,
  onDayClick,
}: {
  gridDates: Date[];
  today: Date;
  selectedDate: Date | null;
  eventsByDate: Record<string, CalendarEvent[]>;
  onDayClick: (date: Date) => void;
}) {
  return (
    <div className="p-3 sm:p-5">
      {/* Day headers */}
      <div className="hidden sm:grid grid-cols-7 gap-2 mb-2">
        {gridDates.map((date, i) => {
          const isToday = isSameDay(date, today);
          return (
            <div key={i} className="text-center">
              <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                {DAY_NAMES_SHORT[i]}
              </div>
              <div
                className={cn(
                  "mt-1 inline-flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold",
                  isToday
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground"
                )}
              >
                {date.getDate()}
              </div>
            </div>
          );
        })}
      </div>

      {/* Day columns with full event cards */}
      <div className="hidden sm:grid grid-cols-7 gap-2">
        {gridDates.map((date, i) => {
          const dateKey = toDateString(date);
          const dayEvents = eventsByDate[dateKey] ?? [];
          const isSelected = selectedDate
            ? isSameDay(date, selectedDate)
            : false;

          return (
            <button
              key={i}
              onClick={() => onDayClick(date)}
              className={cn(
                "flex flex-col rounded-lg p-2 min-h-[10rem] text-left transition-colors hover:bg-muted/50",
                isSelected && "ring-2 ring-primary bg-primary/5"
              )}
            >
              {dayEvents.length > 0 ? (
                <div className="space-y-1.5 w-full">
                  {dayEvents.map((event) => (
                    <EventChip key={event.id} event={event} />
                  ))}
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <span className="text-[10px] text-muted-foreground/50">
                    Geen items
                  </span>
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Mobile: list view for the week */}
      <div className="sm:hidden space-y-3">
        {gridDates.map((date, i) => {
          const dateKey = toDateString(date);
          const dayEvents = eventsByDate[dateKey] ?? [];
          const isToday = isSameDay(date, today);

          return (
            <div key={i}>
              <div className="flex items-center gap-2 mb-1.5">
                <span
                  className={cn(
                    "inline-flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold",
                    isToday
                      ? "bg-primary text-primary-foreground"
                      : "text-foreground"
                  )}
                >
                  {date.getDate()}
                </span>
                <span className="text-xs text-muted-foreground capitalize">
                  {DAY_NAMES_FULL[i]}
                </span>
              </div>
              {dayEvents.length > 0 ? (
                <div className="ml-9 space-y-1.5">
                  {dayEvents.map((event) => (
                    <MobileEventCard
                      key={event.id}
                      event={event}
                    />
                  ))}
                </div>
              ) : (
                <div className="ml-9">
                  <span className="text-xs text-muted-foreground/50">
                    Geen items
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Event Chip (compact, for week view grid cells) ────────────────────────────

function EventChip({ event }: { event: CalendarEvent }) {
  const timeStr =
    (event.source === "user" || event.source === "outlook") && event.start_time && !event.all_day
      ? formatTime(event.start_time)
      : null;

  return (
    <div
      className="rounded-md px-2 py-1 text-[10px] leading-tight truncate w-full"
      style={{
        backgroundColor: event.color ? `${event.color}18` : "#6b728018",
        borderLeft: `3px solid ${event.color || "#6b7280"}`,
      }}
      title={event.title}
    >
      <span className="font-medium text-foreground truncate block">
        {event.source === "outlook" && <Cloud className="h-3 w-3 inline mr-1 text-blue-500" />}
        {timeStr ? `${timeStr} ${event.title}` : event.title}
      </span>
      {event.case_number && (
        <span className="text-muted-foreground">{event.case_number}</span>
      )}
    </div>
  );
}

// ── Mobile Event Card ─────────────────────────────────────────────────────────

function MobileEventCard({ event }: { event: CalendarEvent }) {
  const Icon = getEventIcon(event.event_type);
  const href =
    event.event_type === "kyc_review" && event.contact_id
      ? `/relaties/${event.contact_id}`
      : event.case_id
        ? `/zaken/${event.case_id}`
        : null;

  const timeStr =
    event.source === "user" && event.start_time && !event.all_day
      ? `${formatTime(event.start_time)} - ${formatTime(event.end_time)}`
      : null;

  const content = (
    <div
      className="flex items-start gap-2.5 rounded-lg border border-border bg-card p-3 hover:bg-muted/50 transition-colors"
      style={{ borderLeftColor: event.color || "#6b7280", borderLeftWidth: "3px" }}
    >
      <div
        className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md"
        style={{ backgroundColor: event.color ? `${event.color}18` : "#6b728018" }}
      >
        <Icon
          className="h-3 w-3"
          style={{ color: event.color || "#6b7280" }}
        />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-foreground truncate">
          {event.title}
        </p>
        <div className="flex items-center gap-1.5 mt-0.5">
          {timeStr && (
            <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
              <Clock className="h-2.5 w-2.5" />
              {timeStr}
            </span>
          )}
          {event.case_number && (
            <span className="text-[10px] text-primary font-medium">
              {event.case_number}
            </span>
          )}
          {event.contact_name && (
            <span className="text-[10px] text-muted-foreground">
              {event.contact_name}
            </span>
          )}
        </div>
      </div>
    </div>
  );

  if (href) {
    return <Link href={href}>{content}</Link>;
  }
  return content;
}

// ── Mobile Event List (for month view on small screens) ───────────────────────

function MobileEventList({
  gridDates,
  eventsByDate,
  today,
  onDayClick,
}: {
  gridDates: Date[];
  eventsByDate: Record<string, CalendarEvent[]>;
  today: Date;
  onDayClick: (date: Date) => void;
}) {
  // Show only days that have events, sorted by date
  const daysWithEvents = gridDates
    .filter((date) => {
      const key = toDateString(date);
      return eventsByDate[key] && eventsByDate[key].length > 0;
    })
    .slice(0, 20); // cap to keep it manageable

  if (daysWithEvents.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card px-5 py-8 text-center">
        <Calendar className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
        <p className="text-sm text-muted-foreground">
          Geen items deze periode
        </p>
      </div>
    );
  }

  return (
    <>
      {daysWithEvents.map((date) => {
        const dateKey = toDateString(date);
        const dayEvents = eventsByDate[dateKey] ?? [];
        const isToday = isSameDay(date, today);

        return (
          <div key={dateKey} className="rounded-xl border border-border bg-card overflow-hidden">
            <button
              onClick={() => onDayClick(date)}
              className={cn(
                "flex items-center gap-2 w-full px-4 py-2.5 border-b border-border text-left",
                isToday && "bg-primary/5"
              )}
            >
              <span
                className={cn(
                  "inline-flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold",
                  isToday
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground"
                )}
              >
                {date.getDate()}
              </span>
              <span className="text-xs text-muted-foreground capitalize">
                {date.toLocaleDateString("nl-NL", {
                  weekday: "long",
                  day: "numeric",
                  month: "long",
                })}
              </span>
              <span className="ml-auto inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                {dayEvents.length}
              </span>
            </button>
            <div className="divide-y divide-border">
              {dayEvents.map((event) => {
                const Icon = getEventIcon(event.event_type);
                const href =
                  event.event_type === "kyc_review" && event.contact_id
                    ? `/relaties/${event.contact_id}`
                    : event.case_id
                      ? `/zaken/${event.case_id}`
                      : null;

                const row = (
                  <div className="flex items-center gap-3 px-4 py-2.5 hover:bg-muted/50 transition-colors">
                    <div
                      className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md"
                      style={{
                        backgroundColor: event.color
                          ? `${event.color}18`
                          : "#6b728018",
                      }}
                    >
                      <Icon
                        className="h-3 w-3"
                        style={{ color: event.color || "#6b7280" }}
                      />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-medium text-foreground truncate">
                        {event.title}
                      </p>
                      {(event.case_number || event.contact_name) && (
                        <p className="text-[10px] text-muted-foreground mt-0.5 truncate">
                          {[event.case_number, event.contact_name]
                            .filter(Boolean)
                            .join(" \u00B7 ")}
                        </p>
                      )}
                    </div>
                    <StatusBadge status={event.status} color={event.color} />
                  </div>
                );

                return href ? (
                  <Link key={event.id} href={href}>
                    {row}
                  </Link>
                ) : (
                  <div key={event.id}>{row}</div>
                );
              })}
            </div>
          </div>
        );
      })}
    </>
  );
}

// ── Day Detail Panel ──────────────────────────────────────────────────────────

function DayDetailPanel({
  date,
  events,
  onClose,
  onAddEvent,
  onEditEvent,
}: {
  date: Date;
  events: CalendarEvent[];
  onClose: () => void;
  onAddEvent: () => void;
  onEditEvent: (event: CalendarEvent) => void;
}) {
  return (
    <div className="rounded-xl border border-border bg-card animate-fade-in">
      <div className="flex items-center justify-between px-5 py-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold text-card-foreground capitalize">
            {formatFullDate(date)}
          </h2>
          {events.length > 0 && (
            <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
              {events.length}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onAddEvent}
            className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-3 w-3" />
            Event
          </button>
          <button
            onClick={onClose}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            Sluiten
          </button>
        </div>
      </div>

      {events.length > 0 ? (
        <div className="divide-y divide-border">
          {events.map((event) => (
            <DayDetailEvent
              key={event.id}
              event={event}
              onEdit={() => onEditEvent(event)}
            />
          ))}
        </div>
      ) : (
        <div className="px-5 py-8 text-center">
          <Calendar className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">
            Geen items op deze dag
          </p>
        </div>
      )}
    </div>
  );
}

function DayDetailEvent({
  event,
  onEdit,
}: {
  event: CalendarEvent;
  onEdit: () => void;
}) {
  const Icon = getEventIcon(event.event_type);

  const taskTypeLabel = event.task_type
    ? TASK_TYPE_LABELS[event.task_type] ?? event.task_type
    : null;

  const href =
    event.event_type === "kyc_review" && event.contact_id
      ? `/relaties/${event.contact_id}`
      : event.case_id
        ? `/zaken/${event.case_id}`
        : null;

  const timeStr =
    (event.source === "user" || event.source === "outlook") && event.start_time && !event.all_day
      ? `${formatTime(event.start_time)} - ${formatTime(event.end_time)}`
      : null;

  return (
    <div
      className="flex items-start gap-3 px-5 py-3.5"
      style={{ borderLeftColor: event.color || "#6b7280", borderLeftWidth: "3px" }}
    >
      {/* Icon */}
      <div
        className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
        style={{
          backgroundColor: event.color ? `${event.color}18` : "#6b728018",
        }}
      >
        <Icon
          className="h-4 w-4"
          style={{ color: event.color || "#6b7280" }}
        />
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="text-sm font-medium text-card-foreground">
            {event.title}
          </p>
          <StatusBadge status={event.status} color={event.color} />
          {event.source === "outlook" && (
            <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-medium text-blue-600 ring-1 ring-inset ring-blue-500/20 dark:bg-blue-950/30 dark:text-blue-400 dark:ring-blue-400/30">
              <Cloud className="h-2.5 w-2.5" />
              Outlook
            </span>
          )}
          {taskTypeLabel && (
            <span className="inline-flex items-center rounded-full bg-slate-50 px-2 py-0.5 text-[10px] font-medium text-slate-600 ring-1 ring-inset ring-slate-500/20">
              {taskTypeLabel}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3 mt-1.5 flex-wrap">
          {/* Time display */}
          {timeStr && (
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              {timeStr}
            </span>
          )}

          {/* Location */}
          {event.location && (
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <MapPin className="h-3 w-3" />
              {event.location}
            </span>
          )}

          {/* Case link */}
          {event.case_number && event.case_id && (
            <Link
              href={`/zaken/${event.case_id}`}
              className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
            >
              <Briefcase className="h-3 w-3" />
              {event.case_number}
            </Link>
          )}

          {/* Contact link */}
          {event.contact_name && event.contact_id && (
            <Link
              href={`/relaties/${event.contact_id}`}
              className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
            >
              <Users className="h-3 w-3" />
              {event.contact_name}
            </Link>
          )}

          {/* Assigned to */}
          {event.assigned_to_name && (
            <span className="text-xs text-muted-foreground">
              Toegewezen aan {event.assigned_to_name}
            </span>
          )}

          {/* Event type label */}
          <span className="text-xs text-muted-foreground">
            {getEventLabel(event.event_type)}
          </span>
        </div>

        {/* Description */}
        {event.description && (
          <p className="text-xs text-muted-foreground mt-1.5 line-clamp-2">
            {event.description}
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1.5 shrink-0">
        {event.source === "user" && (
          <button
            onClick={onEdit}
            className="flex h-7 w-7 items-center justify-center rounded-md border border-border hover:bg-muted/50 transition-colors"
            title="Bewerken"
          >
            <Pencil className="h-3 w-3 text-muted-foreground" />
          </button>
        )}
        {href && (
          <Link
            href={href}
            className="shrink-0 inline-flex items-center rounded-md border border-border px-2.5 py-1.5 text-xs font-medium text-foreground hover:bg-muted/50 transition-colors"
          >
            Openen
          </Link>
        )}
      </div>
    </div>
  );
}

// ── Status Badge ──────────────────────────────────────────────────────────────

function StatusBadge({
  status,
  color,
}: {
  status: string;
  color: string;
}) {
  const STATUS_LABELS: Record<string, string> = {
    pending: "Gepland",
    due: "Openstaand",
    completed: "Afgerond",
    skipped: "Overgeslagen",
    overdue: "Te laat",
    active: "Actief",
    scheduled: "Ingepland",
  };

  return (
    <span
      className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium"
      style={{
        backgroundColor: color ? `${color}12` : "#6b728012",
        color: color || "#6b7280",
        boxShadow: `inset 0 0 0 1px ${color ? `${color}30` : "#6b728030"}`,
      }}
    >
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}
