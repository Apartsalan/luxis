import {
  ArrowUpDown,
  MessageSquare,
  Phone,
  Mail,
  FileText,
  CreditCard,
  Briefcase,
} from "lucide-react";

// ── Status & Pipeline constants ─────────────────────────────────────────────

export const STATUS_LABELS: Record<string, string> = {
  nieuw: "Nieuw",
  "14_dagenbrief": "14-dagenbrief",
  sommatie: "Sommatie",
  dagvaarding: "Dagvaarding",
  vonnis: "Vonnis",
  executie: "Executie",
  betaald: "Betaald",
  afgesloten: "Afgesloten",
};

export const STATUS_BADGE: Record<string, string> = {
  nieuw: "bg-blue-50 text-blue-700 ring-blue-600/20",
  "14_dagenbrief": "bg-sky-50 text-sky-700 ring-sky-600/20",
  sommatie: "bg-amber-50 text-amber-700 ring-amber-600/20",
  dagvaarding: "bg-red-50 text-red-700 ring-red-600/20",
  vonnis: "bg-purple-50 text-purple-700 ring-purple-600/20",
  executie: "bg-red-50 text-red-800 ring-red-700/20",
  betaald: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  afgesloten: "bg-slate-50 text-slate-600 ring-slate-500/20",
};

export const PIPELINE_STEPS = [
  "nieuw",
  "14_dagenbrief",
  "sommatie",
  "dagvaarding",
  "vonnis",
  "executie",
  "betaald",
];

export const NEXT_STATUSES: Record<string, string[]> = {
  nieuw: ["14_dagenbrief", "afgesloten"],
  "14_dagenbrief": ["sommatie", "betaald", "afgesloten"],
  sommatie: ["dagvaarding", "betaald", "afgesloten"],
  dagvaarding: ["vonnis", "betaald", "afgesloten"],
  vonnis: ["executie", "betaald", "afgesloten"],
  executie: ["betaald", "afgesloten"],
  betaald: [],
  afgesloten: [],
};

export const TYPE_LABELS: Record<string, string> = {
  incasso: "Incasso",
  insolventie: "Insolventie",
  advies: "Advies",
  overig: "Overig",
};

export const INTEREST_LABELS: Record<string, string> = {
  statutory: "Wettelijke rente (art. 6:119 BW)",
  commercial: "Handelsrente (art. 6:119a BW)",
  government: "Overheidsrente (art. 6:119b BW)",
  contractual: "Contractuele rente",
};

// ── Activity constants ──────────────────────────────────────────────────────

export const ACTIVITY_ICONS: Record<string, typeof Briefcase> = {
  status_change: ArrowUpDown,
  note: MessageSquare,
  phone_call: Phone,
  email: Mail,
  document: FileText,
  payment: CreditCard,
};

export const ACTIVITY_COLORS: Record<string, string> = {
  status_change: "bg-blue-50 text-blue-600",
  note: "bg-amber-50 text-amber-600",
  phone_call: "bg-emerald-50 text-emerald-600",
  email: "bg-violet-50 text-violet-600",
  document: "bg-slate-100 text-slate-600",
  payment: "bg-green-50 text-green-600",
};

export const ACTIVITY_TYPE_LABELS: Record<string, string> = {
  status_change: "Statuswijziging",
  note: "Notitie",
  phone_call: "Telefoongesprek",
  email: "E-mail",
  document: "Document",
  payment: "Betaling",
};

// ── Task constants ──────────────────────────────────────────────────────────

export const TASK_STATUS_BADGE: Record<string, string> = {
  pending: "bg-slate-50 text-slate-600 ring-slate-500/20",
  due: "bg-blue-50 text-blue-700 ring-blue-600/20",
  completed: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  skipped: "bg-slate-50 text-slate-500 ring-slate-400/20",
  overdue: "bg-red-50 text-red-700 ring-red-600/20",
};

// ── Helpers ─────────────────────────────────────────────────────────────────

export function renderSimpleMarkdown(text: string) {
  const lines = text.split("\n");
  return lines.map((line, i) => {
    const isBullet = /^[-*]\s+/.test(line);
    const content = isBullet ? line.replace(/^[-*]\s+/, "") : line;

    const parts = content.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
    const formatted = parts.map((part, j) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={j}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith("*") && part.endsWith("*")) {
        return <em key={j}>{part.slice(1, -1)}</em>;
      }
      return part;
    });

    if (isBullet) {
      return (
        <div key={i} className="flex items-start gap-1.5">
          <span className="mt-1.5 h-1 w-1 rounded-full bg-current shrink-0" />
          <span>{formatted}</span>
        </div>
      );
    }
    return <div key={i}>{formatted.length > 0 ? formatted : "\u00A0"}</div>;
  });
}
