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
  caseStatus?: string | null,
): { label: string; badge: string; title: string } | null {
  if (!status) return null;
  const fase = phase ? ` · fase: ${phase}` : "";
  if (BASENET_HEROPENEN.has(status)) {
    // S231 (demo-vondst Arsalan): een dossier dat inmiddels heropend ÍS, droeg
    // nog steeds "Nog te openen" — de badge keek alleen naar de herkomst, niet
    // naar de huidige status. Heropend → toon dat het uit de fase-heropening
    // komt, niet dat het nog moet.
    if (caseStatus && caseStatus !== "afgesloten") {
      return {
        label: "Heropend",
        badge: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
        title: `In BaseNet nog "${status.toLowerCase()}"${fase} — inmiddels heropend en in behandeling in Luxis`,
      };
    }
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
  onbekend: "bg-muted text-muted-foreground ring-border",
};

// --- S255: één etiket dat zegt wát de wederpartij is, in gewone taal ---
//
// Vervangt "B2B"/"B2C" in de dossierkop. B2B/B2C zegt niets over waar het écht
// om draait: is iemand privé aansprakelijk (dan gaat het renteoverzicht mee als
// bijlage) of niet. Sinds S255 staat van 437 wederpartijen de echte rechtsvorm
// uit het Handelsregister in Luxis, dus dat kan nu getoond worden.
//
// De KLEUR komt NIET uit een lijst hier: de backend rekent
// `beperkt_aansprakelijk` uit met dezelfde constante als de bijlage-beslissing
// (EXCLUDED_LEGAL_FORM_KEYWORDS in collections/compliance.py). Een tweede
// keywordlijst in TypeScript zou stil uit de pas kunnen lopen met de regel die
// bepaalt of er een bijlage meegaat.

// Alleen verkorting voor de leesbaarheid — geen juridische betekenis. Wat er
// niet in staat, wordt voluit getoond.
const RECHTSVORM_KORT: Record<string, string> = {
  "besloten vennootschap": "BV",
  "naamloze vennootschap": "NV",
  "vennootschap onder firma": "VOF",
  "commanditaire vennootschap": "CV",
  "vereniging van eigenaars": "VvE",
};

export type PartijEtiket = { label: string; badge: string; title: string };

export function partijEtiket(
  debtorType: string | null | undefined,
  legalForm: string | null | undefined,
  beperktAansprakelijk: boolean | null | undefined,
): PartijEtiket | null {
  if (!debtorType) return null;

  // Een consument heeft geen rechtsvorm en is altijd privé aansprakelijk.
  // Dit gaat vóór de rechtsvorm: staat er tóch een rechtsvorm op een
  // b2c-dossier, dan is het etiket fout — daar slaat de nachtelijke controle
  // op aan (find_debtor_type_mismatch), niet dit label.
  if (debtorType === "b2c") {
    return {
      label: "Consument",
      badge: DEBTOR_TYPE_BADGE.b2c,
      title: "Consument — wettelijke kostenstaffel geldt, renteoverzicht gaat mee",
    };
  }

  if (!legalForm) {
    return {
      label: "Zakelijk",
      badge: DEBTOR_TYPE_BADGE.onbekend,
      title:
        "Zakelijk, rechtsvorm nog onbekend — het renteoverzicht gaat voor de zekerheid wél mee",
    };
  }

  const kort = RECHTSVORM_KORT[legalForm.toLowerCase()] ?? legalForm;
  return beperktAansprakelijk
    ? {
        label: kort,
        badge: DEBTOR_TYPE_BADGE.b2b,
        title: `${legalForm} — beperkt aansprakelijk, renteoverzicht gaat niet mee`,
      }
    : {
        label: kort,
        badge: DEBTOR_TYPE_BADGE.b2c,
        title: `${legalForm} — privé aansprakelijk, renteoverzicht gaat mee`,
      };
}

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
