"use client";

import { useState } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { api } from "@/lib/api";
import { toast } from "sonner";
import type { SyncedEmailDetail } from "@/hooks/use-email-sync";

// ── AI-antwoord maken (S223) ────────────────────────────────────────────────
// Gedeeld tussen de Mail-pagina en het dossier-tabblad Correspondentie (S227).
// Backend is identiek (POST /api/ai/draft, intent reply_to_email); alleen het
// openen van het concept verschilt per route → geparametriseerd via onOpenDraft:
//   - Mail-pagina: router.push(/zaken/{case_id}?draft={id})  (andere pagina)
//   - Dossier-tab: openDraftDialog(id) direct  (zelfde pagina — ?draft= is in
//     Next 15 onbetrouwbaar bij same-page navigatie, zie BUG-73 in zaken/[id]).

const AI_TONES = [
  { value: "mild", label: "Mild" },
  { value: "zakelijk", label: "Zakelijk" },
  { value: "streng", label: "Streng" },
];

export function AiReplyDialog({
  email,
  onClose,
  onOpenDraft,
}: {
  email: SyncedEmailDetail;
  onClose: () => void;
  onOpenDraft: (draftId: string) => void;
}) {
  const [instruction, setInstruction] = useState("");
  const [tone, setTone] = useState("zakelijk");
  const [busy, setBusy] = useState(false);
  const [existingDraftId, setExistingDraftId] = useState<string | null>(null);

  const openDraft = (draftId: string) => {
    onClose();
    onOpenDraft(draftId);
  };

  const generate = async (forceNew: boolean) => {
    setBusy(true);
    try {
      const res = await api("/api/ai/draft", {
        method: "POST",
        body: JSON.stringify({
          case_id: email.case_id,
          intent: "reply_to_email",
          source_email_id: email.id,
          instruction: instruction.trim() || null,
          tone,
          force_new: forceNew,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Concept genereren mislukt");
      }
      const draft = await res.json();
      toast.success("AI-concept gemaakt");
      openDraft(draft.id);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Concept genereren mislukt");
      setBusy(false);
    }
  };

  const handleSubmit = async () => {
    setBusy(true);
    try {
      const res = await api(
        `/api/ai/draft/existing?case_id=${email.case_id}&source_email_id=${email.id}`
      );
      const data = res.ok ? await res.json() : { draft_id: null };
      if (data.draft_id) {
        setExistingDraftId(data.draft_id);
        setBusy(false);
        return;
      }
    } catch {
      // check faalt → behandel als 'geen bestaand concept'
    }
    await generate(false);
  };

  return (
    <Dialog open onOpenChange={(open) => !open && !busy && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" /> AI-antwoord maken
          </DialogTitle>
          <DialogDescription>
            De AI leest deze mail én het dossier en schrijft zelf een passend
            concept. U kijkt het na vóór verzending.
          </DialogDescription>
        </DialogHeader>

        {existingDraftId ? (
          <div className="space-y-3">
            <p className="text-sm text-foreground">
              Er staat al een AI-concept op deze mail. Wilt u dat openen, of een
              nieuw concept maken (het oude vervalt dan)?
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="rounded-md border border-border bg-muted/30 p-3 text-xs text-muted-foreground">
              <p className="font-medium text-foreground">Antwoord op:</p>
              <p className="truncate">{email.subject || "(Geen onderwerp)"}</p>
              <p className="truncate">
                {email.from_name
                  ? `${email.from_name} <${email.from_email}>`
                  : email.from_email}
              </p>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">
                Instructie (optioneel)
              </label>
              <Textarea
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                placeholder="Bijv. 'zeg dat ik erop terugkom' of 'zeg dat het niet klopt en dat het openstaande bedrag verschuldigd blijft'"
                rows={3}
                disabled={busy}
              />
              <p className="text-xs text-muted-foreground">
                Laat leeg om de AI zelf een passend antwoord te laten kiezen.
              </p>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Toon</label>
              <Select value={tone} onValueChange={setTone} disabled={busy}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AI_TONES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        )}

        <DialogFooter>
          {existingDraftId ? (
            <>
              <Button variant="outline" onClick={() => openDraft(existingDraftId)} disabled={busy}>
                Bestaand openen
              </Button>
              <Button onClick={() => generate(true)} disabled={busy}>
                {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Nieuw maken (vervangt)
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={onClose} disabled={busy}>
                Annuleren
              </Button>
              <Button onClick={handleSubmit} disabled={busy}>
                {busy && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Concept maken
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
