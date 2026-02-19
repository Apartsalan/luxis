"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  Briefcase,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCalendarEvents, type CalendarEvent } from "@/hooks/use-calendar";
import { TASK_TYPE_LABELS } from "@/hooks/use-workflow";
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

// ── Event type config ─────────────────────────────────────────────────────────

const EVENT_TYPE_CONFIG: Record<
  string,
  { label: string; icon: typeof Briefcase }
> = {
  task: { label: "Taak", icon: Briefcase },
  kyc_review: { label: "KYC Review", icon: ShieldCheck },
};

// ── Main Page Component ───────────────────────────────────────────────────────

type ViewMode = "month" | "week";

export default function AgendaPage() {
  const today = useMemo(() => new Date(), []);
  const [currentDate, setCurrentDate] = useState<Date>(today);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("month");

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
      <div>
        <h1 className="text-2xl font-bold text-foreground">Agenda</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Overzicht van taken en afspraken
        </p>
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

          {/* Right: view toggle + today button */}
          <div className="flex items-center gap-2">
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
                      {event.title}
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
        {event.title}
      </span>
      {event.case_number && (
        <span className="text-muted-foreground">{event.case_number}</span>
      )}
    </div>
  );
}

// ── Mobile Event Card ─────────────────────────────────────────────────────────

function MobileEventCard({ event }: { event: CalendarEvent }) {
  const config = EVENT_TYPE_CONFIG[event.event_type] ?? EVENT_TYPE_CONFIG.task;
  const Icon = config.icon;
  const href =
    event.event_type === "kyc_review" && event.contact_id
      ? `/relaties/${event.contact_id}`
      : event.case_id
        ? `/zaken/${event.case_id}`
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
                const config =
                  EVENT_TYPE_CONFIG[event.event_type] ?? EVENT_TYPE_CONFIG.task;
                const Icon = config.icon;
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
}: {
  date: Date;
  events: CalendarEvent[];
  onClose: () => void;
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
        <button
          onClick={onClose}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          Sluiten
        </button>
      </div>

      {events.length > 0 ? (
        <div className="divide-y divide-border">
          {events.map((event) => (
            <DayDetailEvent key={event.id} event={event} />
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

function DayDetailEvent({ event }: { event: CalendarEvent }) {
  const config = EVENT_TYPE_CONFIG[event.event_type] ?? EVENT_TYPE_CONFIG.task;
  const Icon = config.icon;

  const taskTypeLabel = event.task_type
    ? TASK_TYPE_LABELS[event.task_type] ?? event.task_type
    : null;

  const href =
    event.event_type === "kyc_review" && event.contact_id
      ? `/relaties/${event.contact_id}`
      : event.case_id
        ? `/zaken/${event.case_id}`
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
          {taskTypeLabel && (
            <span className="inline-flex items-center rounded-full bg-slate-50 px-2 py-0.5 text-[10px] font-medium text-slate-600 ring-1 ring-inset ring-slate-500/20">
              {taskTypeLabel}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3 mt-1.5 flex-wrap">
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
              <ShieldCheck className="h-3 w-3" />
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
            {config.label}
          </span>
        </div>
      </div>

      {/* Action link */}
      {href && (
        <Link
          href={href}
          className="shrink-0 inline-flex items-center rounded-md border border-border px-2.5 py-1.5 text-xs font-medium text-foreground hover:bg-muted/50 transition-colors"
        >
          Openen
        </Link>
      )}
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
