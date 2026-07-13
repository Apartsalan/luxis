// Shared status constants — single source of truth for case/task status labels and badge styles.
// Standard badge pattern: bg-[color]-50 text-[color]-700 ring-1 ring-inset ring-[color]-600/20
// Non-status semantic colours live in lib/tones.ts.

import { TONES } from "@/lib/tones";

// --- Case statuses (B3, S198: 4 vaste waarden; de incasso-pijplijn is de motor) ---
// De 4 kern-statussen staan bovenaan. De legacy-keys (14_dagenbrief/sommatie/…)
// blijven staan zodat historische statuswijzigingen in de tijdlijn nog een label
// + badge krijgen — ze worden NIET meer als keuze aangeboden.

// De 4 vaste statussen voor filter- en actie-dropdowns.
export const CASE_STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "nieuw", label: "Nieuw" },
  { value: "in_behandeling", label: "In behandeling" },
  { value: "betaald", label: "Betaald" },
  { value: "afgesloten", label: "Afgesloten" },
];

export const CASE_STATUS_LABELS: Record<string, string> = {
  nieuw: "Nieuw",
  in_behandeling: "In behandeling",
  betaald: "Betaald",
  afgesloten: "Afgesloten",
  // Legacy (vóór S198) — alleen historische weergave
  "14_dagenbrief": "14-dagenbrief",
  sommatie: "Sommatie",
  dagvaarding: "Dagvaarding",
  vonnis: "Vonnis",
  executie: "Executie",
};

export const CASE_STATUS_BADGE: Record<string, string> = {
  nieuw: "bg-blue-50 text-blue-700 ring-blue-600/20",
  in_behandeling: "bg-amber-50 text-amber-700 ring-amber-600/20",
  betaald: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  afgesloten: "bg-slate-50 text-slate-600 ring-slate-500/20",
  // Legacy
  "14_dagenbrief": "bg-sky-50 text-sky-700 ring-sky-600/20",
  sommatie: "bg-amber-50 text-amber-700 ring-amber-600/20",
  dagvaarding: "bg-red-50 text-red-700 ring-red-600/20",
  vonnis: "bg-purple-50 text-purple-700 ring-purple-600/20",
  executie: "bg-red-50 text-red-800 ring-red-700/20",
};

export const CASE_STATUS_BADGE_FALLBACK = "bg-slate-50 text-slate-600 ring-slate-500/20";

export const CASE_STATUS_COLOR_FALLBACK = "bg-slate-400";

// Solid colors for pipeline visualization (dashboard bar chart)
export const CASE_STATUS_COLORS: Record<string, string> = {
  nieuw: "bg-blue-500",
  in_behandeling: "bg-amber-500",
  betaald: "bg-emerald-500",
  afgesloten: "bg-slate-400",
  // Legacy
  "14_dagenbrief": "bg-blue-400",
  sommatie: "bg-amber-500",
  dagvaarding: "bg-purple-500",
  vonnis: "bg-purple-500",
  executie: "bg-purple-600",
};

// --- BaseNet-herkomst (S207c) ---
// Onderscheidt geïmporteerde dossiers die in BaseNet nog LIEPEN (worden in fases
// heropend) van dossiers die daar al AFGEHANDELD waren (blijven dicht). Vertaalt
// de ruwe BaseNet-status naar een leesbare herkomst-badge.

const BASENET_HEROPENEN = new Set(["Lopend", "Wacht"]);
const BASENET_AFGEHANDELD = new Set(["Gereed", "Geannuleerd", "Offerte"]);

export function basenetOrigin(
  status: string | null | undefined,
  phase?: string | null,
): { label: string; badge: string; title: string } | null {
  if (!status) return null;
  const fase = phase ? ` · fase: ${phase}` : "";
  if (BASENET_HEROPENEN.has(status)) {
    return {
      label: "Nog te openen",
      badge: "bg-amber-50 text-amber-700 ring-amber-600/20",
      title: `In BaseNet nog "${status.toLowerCase()}"${fase} — geparkeerd, wordt in fases heropend`,
    };
  }
  if (BASENET_AFGEHANDELD.has(status)) {
    return {
      label: "BaseNet-archief",
      badge: "bg-slate-50 text-slate-500 ring-slate-400/20",
      title: `In BaseNet al "${status.toLowerCase()}"${fase} — afgehandeld, blijft gesloten`,
    };
  }
  return null;
}

// --- Case type labels and badges ---

export const CASE_TYPE_LABELS: Record<string, string> = {
  incasso: "Incasso",
  dossier: "Dossier",
  advies: "Advies",
};

export const CASE_TYPE_BADGE: Record<string, string> = {
  incasso: "bg-blue-50 text-blue-600",
  dossier: "bg-slate-50 text-slate-600",
  advies: "bg-teal-50 text-teal-600",
};

// --- Incasso step categories (chip styling, shared by incasso page + staphistorie tab) ---

export const STEP_CATEGORY_STYLES: Record<string, string> = {
  minnelijk: TONES.info.chip,
  gerechtelijk: TONES.legal.chip,
  executie: TONES.danger.chip,
  regeling: TONES.agreement.chip,
  administratief: TONES.gray.chip,
  afsluiting: TONES.success.chip,
};

// --- Debtor type (B2B/B2C) badges ---

export const DEBTOR_TYPE_BADGE: Record<string, string> = {
  b2b: "bg-indigo-50 text-indigo-700 ring-indigo-600/20",
  b2c: "bg-pink-50 text-pink-700 ring-pink-600/20",
};

// --- Task statuses (workflow tasks) ---

export const TASK_STATUS_LABELS: Record<string, string> = {
  overdue: "Te laat",
  due: "Vandaag",
  pending: "Gepland",
  completed: "Afgerond",
  skipped: "Overgeslagen",
};

export const TASK_STATUS_BADGE: Record<string, string> = {
  overdue: "bg-red-50 text-red-700 ring-red-600/20",
  due: "bg-amber-50 text-amber-700 ring-amber-600/20",
  pending: "bg-slate-50 text-slate-600 ring-slate-500/20",
  completed: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  skipped: "bg-slate-50 text-slate-600 ring-slate-500/20",
};

export const TASK_STATUS_BADGE_FALLBACK = "bg-slate-50 text-slate-600 ring-slate-500/20";
