// Semantic colour tones — single source of truth for non-status palette classes.
//
// Why: the design audit (docs/qa/impeccable-audit-2026-06-07.md) found 718
// hard-coded Tailwind palette classes across 62 files. Rebranding meant editing
// every file. This module centralises them: consumers reference a semantic tone
// + slot, only this file holds raw palette classes.
//
// Rules:
// - Slots contain ONLY colour-bearing classes. Layout (px/py, ring-1, ring-inset,
//   ring-4, border, rounded) stays at the consumer.
// - Values intentionally mirror the pre-migration palette so the migration is
//   visually identical. Do not "improve" shades here without a design pass.
// - All strings are full literal Tailwind classes (JIT-safe). Never concatenate
//   class fragments at runtime.
// - Case/task STATUS colours live in lib/status-constants.ts, not here.
//
// Foreground ladder: textFaint(-400) textMuted(-500) text(-600) textStrong(-700)
//                    heading(-800) headingStrong(-900)
// Background ladder: surface(-50) surfaceSoft(-50/50) surfaceFaint(-50/30)
//                    iconBox(-100) solidSoft(-400) solid(-500)

export const TONES = {
  /** Blue — informational accents, document/invoice references. */
  info: {
    text: "text-blue-600",
    textStrong: "text-blue-700",
    textMuted: "text-blue-500",
    surface: "bg-blue-50",
    surfaceSoft: "bg-blue-50/50",
    chip: "bg-blue-100 text-blue-700",
    badge: "bg-blue-50 text-blue-700 ring-blue-600/20",
    button: "bg-blue-600 text-white hover:bg-blue-700",
    outlineButton:
      "border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 hover:border-blue-300",
    stepper: "bg-blue-500 text-white ring-blue-500/20",
  },

  /** Emerald — success, paid, completed, positive amounts. */
  success: {
    text: "text-emerald-600",
    textStrong: "text-emerald-700",
    textMuted: "text-emerald-500",
    textFaint: "text-emerald-400",
    surface: "bg-emerald-50",
    surfaceSoft: "bg-emerald-50/50",
    chip: "bg-emerald-100 text-emerald-700",
    solid: "bg-emerald-500",
    solidSoft: "bg-emerald-400",
    button: "bg-emerald-600 text-white hover:bg-emerald-700",
    hoverSurface: "hover:bg-emerald-50",
    hoverBorder: "hover:border-emerald-500",
    stepper: "bg-emerald-500 text-white ring-emerald-500/20",
  },

  /** Amber — warnings, pending action, overdue-but-recoverable. */
  warning: {
    text: "text-amber-600",
    textStrong: "text-amber-700",
    textMuted: "text-amber-500",
    heading: "text-amber-800",
    headingStrong: "text-amber-900",
    surface: "bg-amber-50",
    surfaceSoft: "bg-amber-50/50",
    surfaceFaint: "bg-amber-50/30",
    chip: "bg-amber-100 text-amber-700",
    badge: "bg-amber-50 text-amber-700 ring-amber-600/20",
    iconBox: "bg-amber-100",
    solid: "bg-amber-500",
    solidSoft: "bg-amber-400",
    button: "bg-amber-600 text-white hover:bg-amber-700",
    outlineButton:
      "border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100",
    hoverSurface: "hover:bg-amber-50",
    border: "border-amber-200",
    borderStrong: "border-amber-300",
    ring: "ring-amber-200",
    ringStrong: "ring-amber-300",
    stepper: "bg-amber-500 text-white ring-amber-500/20",
  },

  /** Red — errors, blocked, overdue, destructive actions. */
  danger: {
    text: "text-red-600",
    textStrong: "text-red-700",
    textMuted: "text-red-500",
    heading: "text-red-800",
    surface: "bg-red-50",
    surfaceSoft: "bg-red-50/50",
    chip: "bg-red-100 text-red-700",
    badge: "bg-red-50 text-red-700 ring-red-600/20",
    solid: "bg-red-500",
    border: "border-red-200",
    borderFaint: "border-red-100",
    divide: "divide-red-200",
    ring: "ring-red-200",
    hoverSurface: "hover:bg-red-50",
    hoverGhost: "hover:bg-red-50 hover:text-red-600",
    stepper: "bg-red-500 text-white ring-red-500/20",
  },

  /** Violet — AI features (suggestions, drafts, AI-linked mail). */
  ai: {
    text: "text-violet-600",
    textStrong: "text-violet-700",
    textMuted: "text-violet-500",
    surface: "bg-violet-50",
    chip: "bg-violet-100 text-violet-700",
    iconBox: "bg-violet-100",
  },

  /** Purple — judicial phase (gerechtelijk, vonnis). */
  legal: {
    textStrong: "text-purple-700",
    chip: "bg-purple-100 text-purple-700",
    stepper: "bg-purple-500 text-white ring-purple-500/20",
  },

  /** Teal — payment arrangement (regeling). */
  agreement: {
    textStrong: "text-teal-700",
    chip: "bg-teal-100 text-teal-700",
  },

  /** Slate — neutral fallback chips/dots (matches status-constants fallbacks). */
  neutral: {
    chip: "bg-slate-50 text-slate-600",
    badge: "bg-slate-50 text-slate-600 ring-slate-500/20",
    solid: "bg-slate-500",
    solidSoft: "bg-slate-400",
  },

  /** Gray — legacy neutral family (chips, wait-dots). Kept exact; do not mix
   *  with `neutral` (slate) silently — unification is a separate design pass. */
  gray: {
    text: "text-gray-700",
    chip: "bg-gray-100 text-gray-700",
    solidSoft: "bg-gray-400",
  },
} as const;

export type Tone = keyof typeof TONES;

/**
 * Credit nota — deliberate purple type-colour (audit: keep). Separate from
 * TONES.legal so invoicing can rebrand independently of the judicial phase.
 */
export const CREDIT_NOTE_TONE = {
  text: "text-purple-700",
  chip: "bg-purple-100 text-purple-600",
  chipStrong: "bg-purple-100 text-purple-700",
  outlineButton:
    "border-purple-200 bg-purple-50 text-purple-700 hover:bg-purple-100",
} as const;

/**
 * Debtor aging buckets (facturen) — sequential severity ramp for the
 * ouderdomsanalyse. Data-viz scale, not a state tone.
 */
export const AGING_TONES = {
  d0_30: {
    dot: TONES.success.solidSoft,
    text: TONES.success.text,
    textStrong: TONES.success.textStrong,
  },
  d31_60: {
    dot: TONES.warning.solidSoft,
    text: TONES.warning.text,
    textStrong: TONES.warning.textStrong,
  },
  d61_90: {
    dot: "bg-orange-400",
    text: "text-orange-600",
    textStrong: "text-orange-700",
  },
  d90_plus: {
    dot: TONES.danger.solid,
    text: TONES.danger.text,
    textStrong: TONES.danger.textStrong,
  },
} as const;

/**
 * Native checkbox colour classes (consumer adds sizing, e.g. "h-4 w-4").
 * border-gray-300 is deliberate: slightly darker than the `input` token so
 * small controls stay visible.
 */
export const CHECKBOX_COLOR = "rounded border-gray-300 text-primary focus:ring-primary";
