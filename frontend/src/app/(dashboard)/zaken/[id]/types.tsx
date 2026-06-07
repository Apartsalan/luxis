import {
  ArrowUpDown,
  Bot,
  MessageSquare,
  Phone,
  Mail,
  FileText,
  CreditCard,
  Briefcase,
  Zap,
} from "lucide-react";
import { sanitizeHtml } from "@/lib/sanitize";

// ── Status & Pipeline constants ─────────────────────────────────────────────
// Status/type labels en badges komen uit lib/status-constants.ts (single source
// of truth) en worden hier her-geëxporteerd onder de lokale namen.

export {
  CASE_STATUS_LABELS as STATUS_LABELS,
  CASE_STATUS_BADGE as STATUS_BADGE,
  CASE_TYPE_LABELS as TYPE_LABELS,
  TASK_STATUS_BADGE,
} from "@/lib/status-constants";

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
  ai_action: Bot,
  automation: Zap,
};

export const ACTIVITY_COLORS: Record<string, string> = {
  status_change: "bg-blue-50 text-blue-600",
  note: "bg-amber-50 text-amber-600",
  phone_call: "bg-emerald-50 text-emerald-600",
  email: "bg-violet-50 text-violet-600",
  document: "bg-slate-100 text-slate-600",
  payment: "bg-emerald-50 text-emerald-600",
  ai_action: "bg-violet-100 text-violet-700",
  automation: "bg-amber-100 text-amber-700",
};

export const ACTIVITY_TYPE_LABELS: Record<string, string> = {
  status_change: "Statuswijziging",
  note: "Notitie",
  phone_call: "Telefoongesprek",
  email: "E-mail",
  document: "Document",
  payment: "Betaling",
  ai_action: "AI",
  automation: "Automatisering",
};

// ── Helpers ─────────────────────────────────────────────────────────────────

/**
 * Render note content with backward compatibility.
 * HTML notes (from Tiptap) → prose rendering.
 * Plain text notes (legacy) → simple markdown rendering.
 */
export function renderNoteContent(text: string | null | undefined) {
  if (!text) return null;
  const isHtml = /<[a-z][\s\S]*>/i.test(text);
  if (isHtml) {
    return (
      <div
        className="prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0"
        dangerouslySetInnerHTML={{ __html: sanitizeHtml(text) }}
      />
    );
  }
  return renderSimpleMarkdown(text);
}

/** Strip HTML tags from a string (for truncated previews) */
export function stripHtml(text: string | null | undefined): string {
  if (!text) return "";
  return text.replace(/<[^>]*>/g, "").trim();
}

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
