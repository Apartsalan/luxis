"use client";

import { useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Clock,
  CreditCard,
  FileText,
  Loader2,
  Mail,
  Paperclip,
  Plus,
  Send,
  Timer,
  Upload,
} from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { toast } from "sonner";
import {
  useCaseTimeline,
  useAddCaseActivity,
  type TimelineItem,
} from "@/hooks/use-cases";
import { formatRelativeTime } from "@/lib/utils";
import { renderNoteContent } from "../types";
import { RichNoteEditor, isNoteEmpty } from "@/components/rich-note-editor";

import type { CaseDetail } from "@/hooks/use-cases";

// ── Timeline type config ────────────────────────────────────────────────────

const TIMELINE_ICONS: Record<string, typeof Clock> = {
  activity: FileText,
  email: Mail,
  payment: CreditCard,
  document: FileText,
  time_entry: Timer,
  file: Upload,
};

const TIMELINE_COLORS: Record<string, string> = {
  activity: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400",
  email: "bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400",
  payment: "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/40 dark:text-emerald-400",
  document: "bg-purple-100 text-purple-600 dark:bg-purple-900/40 dark:text-purple-400",
  time_entry: "bg-amber-100 text-amber-600 dark:bg-amber-900/40 dark:text-amber-400",
  file: "bg-cyan-100 text-cyan-600 dark:bg-cyan-900/40 dark:text-cyan-400",
};

const TIMELINE_TYPE_LABELS: Record<string, string> = {
  activity: "Activiteit",
  email: "E-mail",
  payment: "Betaling",
  document: "Document",
  time_entry: "Uren",
  file: "Bestand",
};

const FILTER_TABS = [
  { key: undefined as string | undefined, label: "Alles" },
  { key: "activity", label: "Notities" },
  { key: "email", label: "E-mails" },
  { key: "document", label: "Documenten" },
  { key: "payment", label: "Betalingen" },
  { key: "time_entry", label: "Uren" },
  { key: "file", label: "Bestanden" },
];

// ── Component ───────────────────────────────────────────────────────────────

export default function ActiviteitenTab({ zaak }: { zaak: CaseDetail }) {
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState<string | undefined>(undefined);
  const [noteText, setNoteText] = useState("");
  const [isAddingNote, setIsAddingNote] = useState(false);
  const { data, isLoading } = useCaseTimeline(zaak.id, page, filter);
  const addActivity = useAddCaseActivity();

  const handleAddNote = async () => {
    if (isNoteEmpty(noteText)) return;

    try {
      await addActivity.mutateAsync({
        caseId: zaak.id,
        data: {
          activity_type: "note",
          title: "Notitie toegevoegd",
          description: noteText,
        },
      });
      setNoteText("");
      setIsAddingNote(false);
      setPage(1);
      toast.success("Notitie toegevoegd");
    } catch {
      toast.error("Kon notitie niet toevoegen");
    }
  };

  const items = data?.items ?? [];
  const totalPages = data?.pages ?? 0;

  return (
    <div className="space-y-4">
      {/* Inline note input */}
      <div className="rounded-xl border border-border bg-card">
        {isAddingNote ? (
          <div className="p-4 space-y-3">
            <RichNoteEditor
              content={noteText}
              onChange={setNoteText}
              placeholder="Schrijf een notitie..."
              autoFocus
            />
            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setIsAddingNote(false);
                  setNoteText("");
                }}
                className="rounded-lg border border-border px-3 py-1.5 text-xs hover:bg-muted transition-colors"
              >
                Annuleren
              </button>
              <button
                type="button"
                onClick={handleAddNote}
                disabled={isNoteEmpty(noteText) || addActivity.isPending}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {addActivity.isPending ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Send className="h-3 w-3" />
                )}
                Opslaan
              </button>
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setIsAddingNote(true)}
            className="flex w-full items-center gap-3 px-5 py-3.5 text-left hover:bg-muted/50 transition-colors rounded-xl"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              <Plus className="h-4 w-4 text-primary" />
            </div>
            <span className="text-sm text-muted-foreground">
              Notitie toevoegen...
            </span>
          </button>
        )}
      </div>

      {/* Timeline */}
      <div className="rounded-xl border border-border bg-card">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-card-foreground">
              Tijdlijn
            </h2>
            {data && (
              <span className="text-xs text-muted-foreground">
                ({data.total})
              </span>
            )}
          </div>
        </div>

        {/* Filter tabs */}
        <div className="flex items-center gap-1 px-5 py-2 border-b border-border overflow-x-auto">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab.key ?? "all"}
              type="button"
              onClick={() => { setFilter(tab.key); setPage(1); }}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors shrink-0 ${
                filter === tab.key
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {isLoading ? (
          <div className="divide-y divide-border">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-start gap-3 px-5 py-4 animate-pulse">
                <div className="h-8 w-8 rounded-full bg-muted shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-2/3 rounded bg-muted" />
                  <div className="h-3 w-1/2 rounded bg-muted" />
                </div>
              </div>
            ))}
          </div>
        ) : items.length > 0 ? (
          <div className="relative">
            <div className="absolute left-[2.375rem] top-0 bottom-0 w-px bg-border" />

            {items.map((item: TimelineItem) => {
              const Icon = TIMELINE_ICONS[item.type] ?? FileText;
              const colorClass = TIMELINE_COLORS[item.type] ?? "bg-muted text-muted-foreground";
              const typeLabel = TIMELINE_TYPE_LABELS[item.type] ?? item.type;

              return (
                <div
                  key={`${item.type}-${item.id}`}
                  className="relative flex items-start gap-3 px-5 py-4 hover:bg-muted/30 transition-colors"
                >
                  <div
                    className={`relative z-10 mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${colorClass}`}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-foreground">
                          {item.title}
                        </p>
                        {item.description && (
                          <div className="text-sm text-muted-foreground mt-0.5">
                            {item.type === "activity" && item.subtype === "note"
                              ? renderNoteContent(item.description)
                              : <p className="whitespace-pre-wrap line-clamp-2">{item.description}</p>
                            }
                          </div>
                        )}
                      </div>
                      <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground uppercase tracking-wide shrink-0">
                        {typeLabel}
                      </span>
                    </div>
                    <div className="mt-1.5 flex items-center gap-2 text-xs text-muted-foreground/70">
                      <span>{formatRelativeTime(item.date)}</span>
                      {"user" in item.metadata && item.metadata.user ? (
                        <>
                          <span>·</span>
                          <span>{String(item.metadata.user)}</span>
                        </>
                      ) : null}
                      {"from" in item.metadata && item.metadata.from ? (
                        <>
                          <span>·</span>
                          <span>{String(item.metadata.from)}</span>
                        </>
                      ) : null}
                      {"has_attachments" in item.metadata && item.metadata.has_attachments ? (
                        <Paperclip className="h-3 w-3" />
                      ) : null}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <EmptyState
            icon={Clock}
            title="Geen activiteiten"
            description={filter ? "Geen items gevonden voor dit filter." : "Voeg een notitie toe om de tijdlijn te starten. E-mails, documenten, betalingen en uren verschijnen hier automatisch."}
          />
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t border-border px-5 py-3">
            <button
              type="button"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-30 transition-colors"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
              Vorige
            </button>
            <span className="text-xs text-muted-foreground">
              Pagina {page} van {totalPages}
            </span>
            <button
              type="button"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-30 transition-colors"
            >
              Volgende
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
