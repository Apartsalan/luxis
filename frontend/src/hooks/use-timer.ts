"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useRef,
  useCallback,
} from "react";
import { useCreateTimeEntry } from "@/hooks/use-time-entries";
import { toast } from "sonner";

// ── Activity types ────────────────────────────────────────────────────────

export const ACTIVITY_TYPES = [
  { value: "correspondence", label: "Correspondentie" },
  { value: "meeting", label: "Bespreking" },
  { value: "phone", label: "Telefonisch" },
  { value: "research", label: "Onderzoek" },
  { value: "court", label: "Zitting" },
  { value: "travel", label: "Reistijd" },
  { value: "drafting", label: "Opstellen stukken" },
  { value: "other", label: "Overig" },
] as const;

export const ACTIVITY_TYPE_LABELS: Record<string, string> = Object.fromEntries(
  ACTIVITY_TYPES.map((t) => [t.value, t.label])
);

// ── Types ────────────────────────────────────────────────────────────────

export interface TimerState {
  running: boolean;
  seconds: number;
  caseId: string;
  caseName: string; // display label e.g. "2024-001 — Jansen B.V."
  description: string;
  activityType: string; // activity_type for time entry (default: "other")
  startedAt: number | null; // timestamp when started (for persistence)
}

interface TimerContextValue {
  timer: TimerState;
  startTimer: (caseId: string, caseName: string) => void;
  stopTimer: () => Promise<void>;
  discardTimer: () => void;
  setTimerCase: (caseId: string, caseName: string) => void;
  setTimerDescription: (desc: string) => void;
  setTimerActivityType: (type: string) => void;
  isExpanded: boolean;
  setIsExpanded: (v: boolean) => void;
}

const STORAGE_KEY = "luxis_timer";
const AUTO_TIMER_KEY = "luxis_auto_timer";
const FORGOTTEN_THRESHOLD = 2 * 60 * 60; // 2 hours in seconds
const AUTO_SAVE_MIN_SECONDS = 60; // minimum seconds to auto-save (1 min)

// ── Default ──────────────────────────────────────────────────────────────

const defaultTimer: TimerState = {
  running: false,
  seconds: 0,
  caseId: "",
  caseName: "",
  description: "",
  activityType: "other",
  startedAt: null,
};

// ── Context ──────────────────────────────────────────────────────────────

export const TimerContext = createContext<TimerContextValue>({
  timer: defaultTimer,
  startTimer: () => {},
  stopTimer: async () => {},
  discardTimer: () => {},
  setTimerCase: () => {},
  setTimerDescription: () => {},
  setTimerActivityType: () => {},
  isExpanded: false,
  setIsExpanded: () => {},
});

export function useTimer() {
  return useContext(TimerContext);
}

// ── Auto-timer preference hook ──────────────────────────────────────────

export function useAutoTimerPreference(): [boolean, (v: boolean) => void] {
  const [enabled, setEnabled] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem(AUTO_TIMER_KEY) === "true";
  });

  const toggle = useCallback((value: boolean) => {
    setEnabled(value);
    localStorage.setItem(AUTO_TIMER_KEY, String(value));
  }, []);

  return [enabled, toggle];
}

// ── Provider hook ────────────────────────────────────────────────────────

function loadFromStorage(): TimerState {
  if (typeof window === "undefined") return defaultTimer;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultTimer;
    const saved = JSON.parse(raw) as TimerState;

    // Ensure activityType exists (backwards compat)
    if (!saved.activityType) saved.activityType = "other";

    // If timer was running, recalculate elapsed seconds
    if (saved.running && saved.startedAt) {
      const elapsed = Math.floor((Date.now() - saved.startedAt) / 1000);
      return { ...saved, seconds: elapsed };
    }
    return saved;
  } catch {
    return defaultTimer;
  }
}

function saveToStorage(state: TimerState) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Storage full or unavailable — ignore
  }
}

function clearStorage() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
}

function toISO(d: Date): string {
  return d.toISOString().split("T")[0];
}

export function useTimerProvider() {
  const [timer, setTimer] = useState<TimerState>(defaultTimer);
  const [isExpanded, setIsExpanded] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const hasWarnedRef = useRef(false);
  const createMutation = useCreateTimeEntry();

  // Load persisted timer on mount
  useEffect(() => {
    const restored = loadFromStorage();
    setTimer(restored);
    // If timer was running, auto-expand to show it
    if (restored.running) {
      setIsExpanded(true);
    }
  }, []);

  // Multi-tab sync: listen for storage changes from other tabs
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY && e.newValue) {
        try {
          const updated = JSON.parse(e.newValue) as TimerState;
          if (!updated.activityType) updated.activityType = "other";
          // Recalculate seconds if running
          if (updated.running && updated.startedAt) {
            updated.seconds = Math.floor(
              (Date.now() - updated.startedAt) / 1000
            );
          }
          setTimer(updated);
        } catch {
          // ignore parse errors
        }
      } else if (e.key === STORAGE_KEY && !e.newValue) {
        // Timer was cleared in another tab
        setTimer(defaultTimer);
      }
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  // Tick interval + forgotten timer warning
  useEffect(() => {
    if (timer.running) {
      intervalRef.current = setInterval(() => {
        setTimer((prev) => {
          const next = { ...prev, seconds: prev.seconds + 1 };
          // Persist every 10 seconds to avoid excessive writes
          if (next.seconds % 10 === 0) {
            saveToStorage(next);
          }
          // Forgotten timer warning (after 2 hours)
          if (
            next.seconds >= FORGOTTEN_THRESHOLD &&
            !hasWarnedRef.current
          ) {
            hasWarnedRef.current = true;
            const h = Math.floor(next.seconds / 3600);
            toast.warning(
              `Timer loopt al ${h} uur voor ${next.caseName}`,
              { duration: 10000 }
            );
          }
          return next;
        });
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      hasWarnedRef.current = false;
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [timer.running]);

  const startTimer = useCallback((caseId: string, caseName: string) => {
    if (!caseId) {
      toast.error("Selecteer eerst een dossier");
      return;
    }
    const newState: TimerState = {
      running: true,
      seconds: 0,
      caseId,
      caseName,
      description: "",
      activityType: "other",
      startedAt: Date.now(),
    };
    setTimer(newState);
    saveToStorage(newState);
    setIsExpanded(true);
  }, []);

  const stopTimer = useCallback(async () => {
    const minutes = Math.max(1, Math.round(timer.seconds / 60));
    try {
      await createMutation.mutateAsync({
        case_id: timer.caseId,
        date: toISO(new Date()),
        duration_minutes: minutes,
        description: timer.description?.trim() || null,
        activity_type: timer.activityType || "other",
        billable: true,
      });
      const h = Math.floor(minutes / 60);
      const m = minutes % 60;
      toast.success(`${h}:${String(m).padStart(2, "0")} geregistreerd`);
      setTimer(defaultTimer);
      clearStorage();
    } catch (err: any) {
      toast.error(err.message || "Opslaan mislukt");
    }
  }, [timer.seconds, timer.caseId, timer.description, timer.activityType, createMutation]);

  const discardTimer = useCallback(() => {
    setTimer(defaultTimer);
    clearStorage();
  }, []);

  const setTimerCase = useCallback((caseId: string, caseName: string) => {
    setTimer((prev) => {
      const next = { ...prev, caseId, caseName };
      if (!prev.running) saveToStorage(next);
      return next;
    });
  }, []);

  const setTimerDescription = useCallback((description: string) => {
    setTimer((prev) => {
      const next = { ...prev, description };
      return next;
    });
  }, []);

  const setTimerActivityType = useCallback((activityType: string) => {
    setTimer((prev) => {
      const next = { ...prev, activityType };
      if (prev.running) saveToStorage(next);
      return next;
    });
  }, []);

  return {
    timer,
    startTimer,
    stopTimer,
    discardTimer,
    setTimerCase,
    setTimerDescription,
    setTimerActivityType,
    isExpanded,
    setIsExpanded,
  };
}

// ── Export constants for external use ────────────────────────────────────

export { AUTO_SAVE_MIN_SECONDS };
