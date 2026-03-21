import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind classes with proper precedence.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a number as Euro currency (Dutch locale).
 * Example: 1523.47 → "€ 1.523,47"
 */
export function formatCurrency(amount: number | string | null | undefined): string {
  if (amount == null) return "€ 0,00";
  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  if (isNaN(num)) return "€ 0,00";
  return new Intl.NumberFormat("nl-NL", {
    style: "currency",
    currency: "EUR",
  }).format(num);
}

/**
 * Format a date in Dutch locale.
 * Example: "2026-02-17" → "17 februari 2026"
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return new Intl.DateTimeFormat("nl-NL", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(d);
}

/**
 * Format a date as short Dutch format.
 * Example: "2026-02-17" → "17-02-2026"
 */
export function formatDateShort(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return new Intl.DateTimeFormat("nl-NL", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(d);
}

/**
 * Format a date as relative time in Dutch.
 * Examples: "Zojuist", "5 min geleden", "2 uur geleden", "Gisteren 14:30", "17 feb"
 */
export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === "string" ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);
  const diffDays = Math.floor(diffMs / 86_400_000);

  const time = new Intl.DateTimeFormat("nl-NL", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);

  if (diffMin < 1) return "Zojuist";
  if (diffMin < 60) return `${diffMin} min geleden`;
  if (diffHours < 24) return `${diffHours} uur geleden`;
  if (diffDays === 1) return `Gisteren ${time}`;
  if (diffDays < 7) {
    const dag = new Intl.DateTimeFormat("nl-NL", { weekday: "long" }).format(d);
    return `${dag.charAt(0).toUpperCase() + dag.slice(1)} ${time}`;
  }
  if (d.getFullYear() === now.getFullYear()) {
    return new Intl.DateTimeFormat("nl-NL", {
      day: "numeric",
      month: "short",
    }).format(d);
  }
  return formatDateShort(d);
}
