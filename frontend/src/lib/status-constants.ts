// Shared status constants — single source of truth for case/task status labels and badge styles.
// Standard badge pattern: bg-[color]-50 text-[color]-700 ring-1 ring-inset ring-[color]-600/20

// --- Case statuses (incasso workflow + general) ---

export const CASE_STATUS_LABELS: Record<string, string> = {
  nieuw: "Nieuw",
  "14_dagenbrief": "14-dagenbrief",
  sommatie: "Sommatie",
  dagvaarding: "Dagvaarding",
  vonnis: "Vonnis",
  executie: "Executie",
  betaald: "Betaald",
  afgesloten: "Afgesloten",
};

export const CASE_STATUS_BADGE: Record<string, string> = {
  nieuw: "bg-blue-50 text-blue-700 ring-blue-600/20",
  "14_dagenbrief": "bg-sky-50 text-sky-700 ring-sky-600/20",
  sommatie: "bg-amber-50 text-amber-700 ring-amber-600/20",
  dagvaarding: "bg-red-50 text-red-700 ring-red-600/20",
  vonnis: "bg-purple-50 text-purple-700 ring-purple-600/20",
  executie: "bg-red-50 text-red-800 ring-red-700/20",
  betaald: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  afgesloten: "bg-slate-50 text-slate-600 ring-slate-500/20",
};

export const CASE_STATUS_BADGE_FALLBACK = "bg-slate-50 text-slate-600 ring-slate-500/20";

// Solid colors for pipeline visualization (dashboard bar chart)
export const CASE_STATUS_COLORS: Record<string, string> = {
  nieuw: "bg-blue-500",
  "14_dagenbrief": "bg-blue-400",
  sommatie: "bg-amber-500",
  dagvaarding: "bg-purple-500",
  vonnis: "bg-purple-500",
  executie: "bg-purple-600",
  betaald: "bg-emerald-500",
  afgesloten: "bg-slate-400",
};

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
