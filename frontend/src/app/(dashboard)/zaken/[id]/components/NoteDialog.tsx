"use client";

import { useEffect, useState } from "react";
import { Loader2, MessageSquare, Phone } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAddCaseActivity } from "@/hooks/use-cases";
import { RichNoteEditor, isNoteEmpty } from "@/components/rich-note-editor-lazy";

export type NoteMode = "note" | "phone";

// S216 blok 2: één venster voor Notitie én Telefoonnotitie. Vervangt het
// tab-gespring (Notitie sprong naar Activiteiten, Telefoonnotitie naar Overzicht)
// én de kapotte cursor-sprong (die zocht een <textarea> die sinds de rijke-
// teksteditor niet meer bestaat). RichNoteEditor.autoFocus zet de cursor nu wél goed.
function phoneTemplate(stamp: string): string {
  return `<p><strong>Telefoonnotitie ${stamp}</strong></p><p>Gesprek met: </p><p>Onderwerp: </p><p></p>`;
}

export default function NoteDialog({
  caseId,
  open,
  mode,
  onOpenChange,
}: {
  caseId: string;
  open: boolean;
  mode: NoteMode;
  onOpenChange: (open: boolean) => void;
}) {
  const [text, setText] = useState("");
  const addActivity = useAddCaseActivity();

  useEffect(() => {
    if (!open) return;
    if (mode === "phone") {
      // Date in een client-effect (niet in de render) — stempel bij het openen.
      const stamp = new Date().toLocaleString("nl-NL", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
      setText(phoneTemplate(stamp));
    } else {
      setText("");
    }
  }, [open, mode]);

  const save = async () => {
    if (isNoteEmpty(text)) return;
    try {
      await addActivity.mutateAsync({
        caseId,
        data: {
          activity_type: "note",
          title: mode === "phone" ? "Telefoonnotitie" : "Notitie toegevoegd",
          description: text,
        },
      });
      toast.success(mode === "phone" ? "Telefoonnotitie opgeslagen" : "Notitie toegevoegd");
      onOpenChange(false);
    } catch {
      toast.error("Kon notitie niet opslaan");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {mode === "phone" ? (
              <Phone className="h-4 w-4" />
            ) : (
              <MessageSquare className="h-4 w-4" />
            )}
            {mode === "phone" ? "Telefoonnotitie" : "Notitie"}
          </DialogTitle>
        </DialogHeader>
        <RichNoteEditor
          content={text}
          onChange={setText}
          autoFocus
          placeholder="Schrijf een notitie..."
        />
        <div className="flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="rounded-lg px-3 py-1.5 text-sm font-medium text-muted-foreground hover:bg-muted transition-colors"
          >
            Annuleren
          </button>
          <button
            type="button"
            onClick={save}
            disabled={isNoteEmpty(text) || addActivity.isPending}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {addActivity.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Opslaan
          </button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
