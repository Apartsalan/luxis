/**
 * Shared confidence label helpers for AI UX.
 *
 * Thresholds:
 *   >= 0.80  →  "Aanbevolen"  (blue)
 *   >= 0.60  →  "Mogelijk"    (orange)
 *   <  0.60  →  "Onzeker"     (grey)
 */

export type ConfidenceLevel = "high" | "medium" | "low";

export function confidenceLevel(c: number): ConfidenceLevel {
  if (c >= 0.8) return "high";
  if (c >= 0.6) return "medium";
  return "low";
}

export function confidenceLabelText(c: number): string {
  if (c >= 0.8) return "Aanbevolen";
  if (c >= 0.6) return "Mogelijk";
  return "Onzeker";
}

/** Tailwind bg color class */
export function confidenceBgColor(c: number): string {
  if (c >= 0.8) return "bg-blue-500";
  if (c >= 0.6) return "bg-amber-500";
  return "bg-slate-400";
}

/** Tailwind text color class */
export function confidenceTextColor(c: number): string {
  if (c >= 0.8) return "text-blue-700 dark:text-blue-400";
  if (c >= 0.6) return "text-amber-700 dark:text-amber-400";
  return "text-slate-500 dark:text-slate-400";
}

/** Badge classes (bg + text + ring) for inline badges */
export function confidenceBadgeClasses(c: number): string {
  if (c >= 0.8)
    return "bg-blue-50 text-blue-700 ring-blue-600/20 dark:bg-blue-900/30 dark:text-blue-400";
  if (c >= 0.6)
    return "bg-amber-50 text-amber-700 ring-amber-600/20 dark:bg-amber-900/30 dark:text-amber-400";
  return "bg-slate-50 text-slate-600 ring-slate-500/20 dark:bg-slate-800/30 dark:text-slate-400";
}
