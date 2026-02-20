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

// ── Types ────────────────────────────────────────────────────────────────

export interface TimerState {
  running: boolean;
  seconds: number;
  caseId: string;
  caseName: string; // display label e.g. "2024-001 — Jansen B.V."
  description: string;
  startedAt: number | null; // timestamp when started (for persistence)
}

interface TimerContextValue {
  timer: TimerState;
  startTimer: (caseId: string, caseName: string) => void;
  stopTimer: () => Promise<void>;
  discardTimer: () => void;
  setTimerCase: (caseId: string, caseName: string) => void;
  setTimerDescription: (desc: string) => void;
  isExpanded: boolean;
  setIsExpanded: (v: boolean) => void;
}

const STORAGE_KEY = "luxis_timer";

// ── Default ──────────────────────────────────────────────────────────────

const defaultTimer: TimerState = {
  running: false,
  seconds: 0,
  caseId: "",
  caseName: "",
  description: "",
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
  isExpanded: false,
  setIsExpanded: () => {},
});

export function useTimer() {
  return useContext(TimerContext);
}

// ── Provider hook ────────────────────────────────────────────────────────

function loadFromStorage(): TimerState {
  if (typeof window === "undefined") return defaultTimer;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultTimer;
    const saved = JSON.parse(raw) as TimerState;

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

  // Tick interval
  useEffect(() => {
    if (timer.running) {
      intervalRef.current = setInterval(() => {
        setTimer((prev) => {
          const next = { ...prev, seconds: prev.seconds + 1 };
          // Persist every 10 seconds to avoid excessive writes
          if (next.seconds % 10 === 0) {
            saveToStorage(next);
          }
          return next;
        });
      }, 1000);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
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
        description: timer.description || undefined,
        activity_type: "other",
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
  }, [timer.seconds, timer.caseId, timer.description, createMutation]);

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

  return {
    timer,
    startTimer,
    stopTimer,
    discardTimer,
    setTimerCase,
    setTimerDescription,
    isExpanded,
    setIsExpanded,
  };
}
