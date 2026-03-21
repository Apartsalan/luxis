"use client";

import { useState, useEffect, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Play,
  Square,
  X,
  Clock,
  ChevronDown,
  ChevronUp,
  Briefcase,
  Trash2,
  Zap,
} from "lucide-react";
import {
  useTimer,
  useAutoTimerPreference,
  ACTIVITY_TYPES,
} from "@/hooks/use-timer";
import { useAuth } from "@/hooks/use-auth";
import { useCases, type CaseSummary } from "@/hooks/use-cases";

// ── Timer Display ────────────────────────────────────────────────────────

function formatTimer(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

// ── Compact Case Picker (for the floating timer) ─────────────────────────

function CompactCasePicker({
  cases,
  value,
  onChange,
  disabled,
}: {
  cases: CaseSummary[];
  value: string;
  onChange: (id: string, label: string) => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);

  const selected = cases.find((c) => c.id === value);

  const filtered = useMemo(() => {
    if (!search) return cases.slice(0, 20); // Show max 20
    const q = search.toLowerCase();
    return cases
      .filter(
        (c) =>
          c.case_number.toLowerCase().includes(q) ||
          c.client?.name?.toLowerCase().includes(q) ||
          c.description?.toLowerCase().includes(q)
      )
      .slice(0, 20);
  }, [cases, search]);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
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
        className="w-full rounded-md border border-input bg-background px-2.5 py-1.5 text-xs text-left flex items-center justify-between gap-1.5 hover:bg-muted/50 transition-colors disabled:opacity-50"
      >
        <span
          className={
            selected
              ? "text-foreground truncate"
              : "text-muted-foreground truncate"
          }
        >
          {selected
            ? `${selected.case_number}${selected.client?.name ? ` — ${selected.client.name}` : ""}`
            : "Selecteer dossier..."}
        </span>
        <ChevronDown className="h-3 w-3 text-muted-foreground shrink-0" />
      </button>

      {open && (
        <div className="absolute bottom-full mb-1 w-full min-w-[280px] rounded-md border border-border bg-card shadow-lg z-50">
          <div className="p-1.5 border-b border-border">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Zoek dossier..."
              className="w-full rounded border border-input bg-background px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-primary/30"
              autoFocus
            />
          </div>
          <div className="max-h-48 overflow-y-auto">
            {filtered.length === 0 ? (
              <p className="px-3 py-4 text-center text-xs text-muted-foreground">
                Geen dossiers gevonden
              </p>
            ) : (
              filtered.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => {
                    const label = `${c.case_number}${c.client?.name ? ` — ${c.client.name}` : ""}`;
                    onChange(c.id, label);
                    setOpen(false);
                    setSearch("");
                  }}
                  className={`w-full text-left px-2.5 py-1.5 text-xs hover:bg-muted/50 transition-colors flex items-center gap-2 ${
                    c.id === value
                      ? "bg-primary/5 text-primary"
                      : "text-foreground"
                  }`}
                >
                  <Briefcase className="h-3 w-3 text-muted-foreground shrink-0" />
                  <div className="min-w-0 truncate">
                    <span className="font-mono font-medium">
                      {c.case_number}
                    </span>
                    {c.client?.name && (
                      <span className="text-muted-foreground ml-1.5">
                        — {c.client.name}
                      </span>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Floating Timer Component ─────────────────────────────────────────────

export function FloatingTimer() {
  const { user } = useAuth();

  // Don't render (or run hooks like useCases) if not logged in
  if (!user) return null;

  return <FloatingTimerInner />;
}

function FloatingTimerInner() {
  const {
    timer,
    startTimer,
    resumeTimer,
    stopTimer,
    discardTimer,
    setTimerCase,
    setTimerDescription,
    setTimerActivityType,
    isExpanded,
    setIsExpanded,
  } = useTimer();
  const router = useRouter();
  const [autoTimer, setAutoTimer] = useAutoTimerPreference();

  const { data: casesData } = useCases({ per_page: 200 });
  const cases = casesData?.items ?? [];

  // Collapsed state: just a small pill when timer is running
  if (timer.running && !isExpanded) {
    return (
      <div className="fixed bottom-20 right-4 z-50 animate-in slide-in-from-bottom-2 duration-200">
        <button
          onClick={() => setIsExpanded(true)}
          className="flex items-center gap-2 rounded-full bg-emerald-600 px-4 py-2.5 text-white shadow-lg hover:bg-emerald-700 transition-all hover:shadow-xl"
        >
          <Clock className="h-4 w-4 animate-pulse" />
          <span className="font-mono text-sm font-bold tabular-nums">
            {formatTimer(timer.seconds)}
          </span>
          <ChevronUp className="h-3.5 w-3.5 opacity-70" />
        </button>
      </div>
    );
  }

  // Not running and not expanded: show start button
  if (!timer.running && !isExpanded) {
    return (
      <div className="fixed bottom-20 right-4 z-50">
        <button
          onClick={() => setIsExpanded(true)}
          className="flex items-center gap-2 rounded-full bg-card border border-border px-4 py-2.5 text-foreground shadow-lg hover:bg-muted/50 transition-all hover:shadow-xl"
          title="Timer starten (tijdschrijven)"
        >
          <Clock className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Timer</span>
        </button>
      </div>
    );
  }

  // Expanded state: full timer panel
  return (
    <div className="fixed bottom-20 right-4 z-50 w-72 animate-in slide-in-from-bottom-2 duration-200">
      <div className="rounded-xl border border-border bg-card shadow-xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-3 py-2 bg-muted/30 border-b border-border">
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-xs font-semibold text-foreground">
              Stopwatch
            </span>
          </div>
          <button
            onClick={() => setIsExpanded(false)}
            className="rounded p-0.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            title="Minimaliseren"
          >
            <ChevronDown className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Timer display */}
        <div className="px-3 pt-3 pb-2">
          <div
            className={`text-3xl font-mono font-bold tabular-nums text-center ${
              timer.running ? "text-emerald-600" : "text-foreground"
            }`}
          >
            {formatTimer(timer.seconds)}
          </div>
          {timer.caseName && (
            <p className="mt-1 text-[11px] text-muted-foreground text-center truncate">
              {timer.caseName}
            </p>
          )}
        </div>

        {/* Case selector (only when NOT running) */}
        {!timer.running && (
          <div className="px-3 pb-2">
            <CompactCasePicker
              cases={cases}
              value={timer.caseId}
              onChange={(id, label) => setTimerCase(id, label)}
              disabled={timer.running}
            />
          </div>
        )}

        {/* Activity type selector (when running) */}
        {timer.running && (
          <div className="px-3 pb-2">
            <select
              value={timer.activityType}
              onChange={(e) => setTimerActivityType(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary/30"
            >
              {ACTIVITY_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Description field */}
        {timer.running && (
          <div className="px-3 pb-2">
            <input
              type="text"
              value={timer.description}
              onChange={(e) => setTimerDescription(e.target.value)}
              placeholder="Omschrijving (optioneel)"
              className="w-full rounded-md border border-input bg-background px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary/30"
            />
          </div>
        )}

        {/* Action buttons */}
        <div className="px-3 pb-3 flex gap-2">
          {timer.running ? (
            <>
              <button
                onClick={stopTimer}
                className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-lg bg-destructive px-3 py-2 text-xs font-medium text-destructive-foreground hover:bg-destructive/90 transition-colors"
              >
                <Square className="h-3 w-3" />
                Stop & Opslaan
              </button>
              <button
                onClick={discardTimer}
                className="inline-flex items-center justify-center rounded-lg border border-border px-2.5 py-2 text-xs text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                title="Verwijderen"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </>
          ) : timer.seconds > 0 && timer.caseId ? (
            // Paused timer (e.g. restored after browser close) — show resume + discard
            <>
              <button
                onClick={resumeTimer}
                className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-medium text-white hover:bg-emerald-700 transition-colors"
              >
                <Play className="h-3 w-3" />
                Hervat
              </button>
              <button
                onClick={stopTimer}
                className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-border px-2.5 py-2 text-xs text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                title="Opslaan"
              >
                <Square className="h-3 w-3" />
              </button>
              <button
                onClick={discardTimer}
                className="inline-flex items-center justify-center rounded-lg border border-border px-2.5 py-2 text-xs text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                title="Verwijderen"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </>
          ) : (
            <button
              onClick={() => startTimer(timer.caseId, timer.caseName)}
              className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-medium text-white hover:bg-emerald-700 transition-colors"
            >
              <Play className="h-3 w-3" />
              Start
            </button>
          )}
        </div>

        {/* Auto-timer toggle */}
        <div className="px-3 pb-2 border-t border-border pt-2">
          <label className="flex items-center gap-2 cursor-pointer group">
            <button
              type="button"
              role="switch"
              aria-checked={autoTimer}
              onClick={() => setAutoTimer(!autoTimer)}
              className={`relative inline-flex h-4 w-7 shrink-0 items-center rounded-full transition-colors ${
                autoTimer ? "bg-emerald-600" : "bg-muted-foreground/30"
              }`}
            >
              <span
                className={`inline-block h-3 w-3 rounded-full bg-white shadow-sm transition-transform ${
                  autoTimer ? "translate-x-3.5" : "translate-x-0.5"
                }`}
              />
            </button>
            <span className="flex items-center gap-1 text-[11px] text-muted-foreground group-hover:text-foreground transition-colors">
              <Zap className="h-3 w-3" />
              Auto-start bij dossier
            </span>
          </label>
        </div>

        {/* Link to uren page */}
        <div className="px-3 pb-2 border-t border-border pt-2">
          <button
            onClick={() => {
              setIsExpanded(false);
              router.push("/uren");
            }}
            className="w-full text-center text-[11px] text-muted-foreground hover:text-primary transition-colors"
          >
            Naar urenregistratie →
          </button>
        </div>
      </div>
    </div>
  );
}
