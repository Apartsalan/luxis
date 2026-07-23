"use client";

import { Clock, Loader2, X, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  SCHEDULED_STATUS_LABELS,
  useCancelScheduledEmail,
  useScheduledEmails,
  type ScheduledEmail,
} from "@/hooks/use-scheduled-emails";

/** Verzendmoment in Nederlandse tijd — de server bewaart UTC. */
function formatMoment(iso: string): string {
  return new Date(iso).toLocaleString("nl-NL", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function StatusBadge({ status }: { status: ScheduledEmail["status"] }) {
  const variant =
    status === "failed" ? "destructive" : status === "sending" ? "secondary" : "outline";
  return (
    <Badge variant={variant} className="text-[10px] shrink-0">
      {SCHEDULED_STATUS_LABELS[status]}
    </Badge>
  );
}

export interface ScheduledEmailsPanelProps {
  /** Alleen dit dossier; weglaten = alle geplande mails van het kantoor. */
  caseId?: string;
  /** Verberg het blok volledig als er niets klaarstaat (dossierpagina). */
  hideWhenEmpty?: boolean;
}

/**
 * S246 — "Verstuur later": wat staat er klaar, en haal het weg als het niet meer
 * moet. Zichtbaar op het dossier én op de Mail-pagina.
 */
export function ScheduledEmailsPanel({ caseId, hideWhenEmpty = false }: ScheduledEmailsPanelProps) {
  const { data: items, isLoading } = useScheduledEmails(caseId);
  const cancel = useCancelScheduledEmail();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground p-4">
        <Loader2 className="h-4 w-4 animate-spin" /> Geplande e-mails laden…
      </div>
    );
  }

  if (!items || items.length === 0) {
    if (hideWhenEmpty) return null;
    return (
      <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
        <Clock className="h-5 w-5 mx-auto mb-2 opacity-50" />
        Geen e-mails ingepland.
      </div>
    );
  }

  const handleCancel = (item: ScheduledEmail) => {
    cancel.mutate(item.id, {
      onSuccess: () => toast.success("Geplande e-mail geannuleerd"),
      onError: (e: unknown) =>
        toast.error(e instanceof Error ? e.message : "Annuleren mislukt"),
    });
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm font-medium">
        <Clock className="h-4 w-4 text-muted-foreground" />
        Staat klaar om te versturen
        <span className="text-muted-foreground font-normal">({items.length})</span>
      </div>
      <div className="rounded-lg border divide-y">
        {items.map((item) => (
          <div key={item.id} className="flex items-start gap-3 p-3 min-w-0">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm font-medium truncate">
                  {item.subject || "(geen onderwerp)"}
                </span>
                <StatusBadge status={item.status} />
              </div>
              <p className="text-xs text-muted-foreground truncate">
                Aan {item.recipients}
              </p>
              <p className="text-xs text-muted-foreground">
                {item.status === "failed" ? "Zou verstuurd worden" : "Verstuurt"}{" "}
                <span className="font-medium text-foreground">
                  {formatMoment(item.scheduled_at)}
                </span>
              </p>
              {item.status === "failed" && item.last_error && (
                <p className="mt-1 flex items-start gap-1.5 text-xs text-destructive">
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0 mt-0.5" />
                  <span className="min-w-0">{item.last_error}</span>
                </p>
              )}
            </div>
            {item.status === "pending" && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="shrink-0 gap-1.5 text-muted-foreground"
                disabled={cancel.isPending}
                onClick={() => handleCancel(item)}
              >
                <X className="h-3.5 w-3.5" /> Annuleren
              </Button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
