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
  resumeTimer: () => void;
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
  resumeTimer: () => {},
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

// Threshold to distinguish page refresh from browser close (5 seconds)
const BROWSER_CLOSE_THRESHOLD = 5000;

interface PersistedTimerState extends TimerState {
  lastSavedAt?: number; // timestamp of last save (for browser close detection)
}

function loadFromStorage(): { state: TimerState; wasRestoredFromClose: boolean } {
  if (typeof window === "undefined") return { state: defaultTimer, wasRestoredFromClose: false };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { state: defaultTimer, wasRestoredFromClose: false };
    const saved = JSON.parse(raw) as PersistedTimerState;

    // Ensure activityType exists (backwards compat)
    if (!saved.activityType) saved.activityType = "other";

    // If timer was running, check if this is a page refresh or browser reopen
    if (saved.running && saved.startedAt) {
      const timeSinceLastSave = saved.lastSavedAt
        ? Date.now() - saved.lastSavedAt
        : Infinity;

      if (timeSinceLastSave > BROWSER_CLOSE_THRESHOLD) {
        // Browser was closed — pause the timer at the last known seconds
        return {
          state: { ...saved, running: false },
          wasRestoredFromClose: true,
        };
      }

      // Page refresh — recalculate elapsed seconds and keep running
      const elapsed = Math.floor((Date.now() - saved.startedAt) / 1000);
      return { state: { ...saved, seconds: elapsed }, wasRestoredFromClose: false };
    }
    return { state: saved, wasRestoredFromClose: false };
  } catch {
    return { state: defaultTimer, wasRestoredFromClose: false };
  }
}

function saveToStorage(state: TimerState) {
  if (typeof window === "undefined") return;
  try {
    const persisted: PersistedTimerState = { ...state, lastSavedAt: Date.now() };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(persisted));
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
  const timerRef = useRef<TimerState>(defaultTimer);
  const createMutation = useCreateTimeEntry();

  // Load persisted timer on mount
  useEffect(() => {
    const { state: restored, wasRestoredFromClose } = loadFromStorage();
    setTimer(restored);
    // If timer was running or restored from close, auto-expand to show it
    if (restored.running || wasRestoredFromClose) {
      setIsExpanded(true);
    }
    // Notify user that timer was paused due to browser close
    if (wasRestoredFromClose && restored.seconds > 0) {
      const h = Math.floor(restored.seconds / 3600);
      const m = Math.floor((restored.seconds % 3600) / 60);
      const time = h > 0
        ? `${h}:${String(m).padStart(2, "0")} uur`
        : `${m} minuten`;
      toast.info(
        `Timer voor ${restored.caseName} gepauzeerd op ${time} (browser was gesloten)`,
        { duration: 8000 }
      );
    }
  }, []);

  // Keep ref in sync with state (for use in beforeunload)
  useEffect(() => {
    timerRef.current = timer;
  }, [timer]);

  // Save accurate state on browser close / tab close / navigation
  useEffect(() => {
    const handleBeforeUnload = () => {
      const current = timerRef.current;
      if (current.running) {
        saveToStorage(current);
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
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

  // Resume a paused timer (e.g. after browser close restore)
  const resumeTimer = useCallback(() => {
    setTimer((prev) => {
      if (prev.running || !prev.caseId) return prev;
      const resumed: TimerState = {
        ...prev,
        running: true,
        // Set startedAt so elapsed calculation works: now minus already-elapsed seconds
        startedAt: Date.now() - prev.seconds * 1000,
      };
      saveToStorage(resumed);
      return resumed;
    });
  }, []);

  const stopTimer = useCallback(async () => {
    // Round up to nearest 6 minutes (0.1 hour) — standard legal billing
    const minutes = Math.max(6, Math.ceil(timer.seconds / 360) * 6);
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
    resumeTimer,
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
