"use client";

import { useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Clock,
  FileText,
  Loader2,
  Plus,
  Send,
} from "lucide-react";
import { EmptyState } from "@/components/empty-state";
import { toast } from "sonner";
import { useCaseActivities, useAddCaseActivity, type CaseActivity } from "@/hooks/use-cases";
import { formatRelativeTime } from "@/lib/utils";
import { ACTIVITY_ICONS, ACTIVITY_COLORS, ACTIVITY_TYPE_LABELS, renderNoteContent } from "../types";
import { RichNoteEditor, isNoteEmpty } from "@/components/rich-note-editor";

import type { CaseDetail } from "@/hooks/use-cases";

export default function ActiviteitenTab({ zaak }: { zaak: CaseDetail }) {
  const [page, setPage] = useState(1);
  const [noteText, setNoteText] = useState("");
  const [isAddingNote, setIsAddingNote] = useState(false);
  const { data, isLoading } = useCaseActivities(zaak.id, page);
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

  const activities = data?.items ?? [];
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

      {/* Activity timeline */}
      <div className="rounded-xl border border-border bg-card">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold text-card-foreground">
              Alle activiteiten
            </h2>
            {data && (
              <span className="text-xs text-muted-foreground">
                ({data.total})
              </span>
            )}
          </div>
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
        ) : activities.length > 0 ? (
          <div className="relative">
            <div className="absolute left-[2.375rem] top-0 bottom-0 w-px bg-border" />

            {activities.map((activity: CaseActivity) => {
              const Icon =
                ACTIVITY_ICONS[activity.activity_type] ?? FileText;
              const colorClass =
                ACTIVITY_COLORS[activity.activity_type] ??
                "bg-muted text-muted-foreground";
              const typeLabel =
                ACTIVITY_TYPE_LABELS[activity.activity_type] ??
                activity.activity_type;

              return (
                <div
                  key={activity.id}
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
                          {activity.title}
                        </p>
                        {activity.description && (
                          <div className="text-sm text-muted-foreground mt-0.5">
                            {activity.activity_type === "note"
                              ? renderNoteContent(activity.description)
                              : <p className="whitespace-pre-wrap">{activity.description}</p>
                            }
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0">
                        {(activity.activity_type === "ai_action" || activity.activity_type === "automation") && (
                          <span className="rounded-md bg-violet-100 dark:bg-violet-900/30 px-1.5 py-0.5 text-[9px] font-semibold text-violet-700 dark:text-violet-400 uppercase tracking-wider">
                            AI
                          </span>
                        )}
                        <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
                          {typeLabel}
                        </span>
                      </div>
                    </div>
                    <div className="mt-1.5 flex items-center gap-2 text-xs text-muted-foreground/70">
                      <span>{formatRelativeTime(activity.created_at)}</span>
                      {activity.user && (
                        <>
                          <span>·</span>
                          <span>{activity.user.full_name}</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <EmptyState
            icon={Clock}
            title="Nog geen activiteiten"
            description="Voeg een notitie toe om de timeline te starten. Activiteiten zoals e-mails, documenten en statuswijzigingen verschijnen hier automatisch."
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
