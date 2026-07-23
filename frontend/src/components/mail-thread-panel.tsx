"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Mail, Loader2, ArrowDownLeft, ArrowUpRight } from "lucide-react";
import { sanitizeHtml } from "@/lib/sanitize";
import { cn } from "@/lib/utils";
import {
  useCaseEmails,
  useSyncedEmailDetail,
  type SyncedEmailDetail,
  type SyncedEmailSummary,
} from "@/hooks/use-email-sync";

// ── Mailgeschiedenis in het antwoord-zijpaneel (S233) ────────────────────────
// Toont onderin het compose-paneel de mail waarop je antwoordt (uitklapbaar,
// standaard open) plus de eerdere mailtjes van dezelfde draad eronder — zodat
// je kunt blijven lezen terwijl je het antwoord schrijft. Alleen-lezen.

function fmtDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString("nl-NL", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function MailBody({
  bodyHtml,
  bodyText,
  snippet,
}: {
  bodyHtml?: string | null;
  bodyText?: string | null;
  snippet?: string | null;
}) {
  if (bodyHtml) {
    return (
      <div
        className="prose prose-sm max-w-none text-foreground"
        dangerouslySetInnerHTML={{ __html: sanitizeHtml(bodyHtml) }}
      />
    );
  }
  return (
    <pre className="whitespace-pre-wrap font-sans text-sm text-foreground">
      {bodyText || snippet || "(geen inhoud)"}
    </pre>
  );
}

/** Eerdere mail uit de draad — lazy: haalt de volledige inhoud pas op bij uitklappen. */
function ThreadRow({ summary }: { summary: SyncedEmailSummary }) {
  const [open, setOpen] = useState(false);
  const { data: detail, isLoading } = useSyncedEmailDetail(open ? summary.id : undefined);
  const inbound = summary.direction === "inbound";

  return (
    <div className="rounded-md border border-border bg-background">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left text-xs"
      >
        {open ? (
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        )}
        {inbound ? (
          <ArrowDownLeft className="h-3.5 w-3.5 shrink-0 text-blue-600" />
        ) : (
          <ArrowUpRight className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
        )}
        <span className="min-w-0 flex-1 truncate font-medium text-foreground">
          {summary.from_name || summary.from_email}
        </span>
        <span className="shrink-0 text-muted-foreground">{fmtDate(summary.email_date)}</span>
      </button>
      {open && (
        <div className="border-t border-border px-3 py-2">
          {isLoading ? (
            <div className="flex items-center gap-2 py-2 text-xs text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin" /> Laden...
            </div>
          ) : (
            <div className="max-h-[280px] overflow-auto">
              <MailBody
                bodyHtml={detail?.body_html}
                bodyText={detail?.body_text}
                snippet={summary.snippet}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function MailThreadPanel({
  sourceEmail,
  hideSource = false,
}: {
  sourceEmail: SyncedEmailDetail;
  // S244 — in het Mail-leesvenster staat de bronmail al volledig in beeld;
  // dan tonen we alleen de eerdere mailtjes van de draad eronder.
  hideSource?: boolean;
}) {
  const [openSource, setOpenSource] = useState(true);
  // S234-review: 200 i.p.v. de default 50 — het drukste dossier heeft ~83 mails,
  // met 50 vielen oudere draadmails stil weg (zelfde cap als CorrespondentieTab).
  const { data: caseEmails } = useCaseEmails(sourceEmail.case_id ?? undefined, 200);

  // Eerdere mailtjes van dezelfde draad, nieuwste eerst. S244: sleutel =
  // genormaliseerd onderwerp (Re:/Fwd: eraf) — prod-meting: antwoorden krijgen
  // regelmatig een nieuw provider-conversation-id en BaseNet-import-mails
  // hebben er geen, dus alleen thread-id liet de geschiedenis bijna altijd
  // leeg. Zelfde thread-id telt óók mee (dekt lege onderwerpen).
  const normalize = (s: string | null | undefined) =>
    (s || "").trim().replace(/^((re|fwd|fw)\s*:\s*)+/i, "").toLowerCase();
  const sourceNorm = normalize(sourceEmail.subject);
  const threadEmails = (caseEmails?.emails ?? [])
    .filter(
      (e) =>
        e.id !== sourceEmail.id &&
        ((!!sourceNorm && normalize(e.subject) === sourceNorm) ||
          (!!sourceEmail.provider_thread_id &&
            e.provider_thread_id === sourceEmail.provider_thread_id))
    )
    .sort((a, b) => (a.email_date < b.email_date ? 1 : -1));

  if (hideSource && threadEmails.length === 0) return null;

  return (
    <div className="space-y-2">
      {/* De mail waarop je antwoordt — uitklapbaar, standaard open. */}
      {!hideSource && (
      <div className="rounded-md border border-border bg-muted/20">
        <button
          type="button"
          onClick={() => setOpenSource((v) => !v)}
          className="flex w-full items-center gap-2 px-3 py-2 text-left"
        >
          {openSource ? (
            <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
          )}
          <Mail className="h-4 w-4 shrink-0 text-primary" />
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-medium text-foreground">
              {sourceEmail.subject || "(Geen onderwerp)"}
            </span>
            <span className="block truncate text-xs text-muted-foreground">
              {sourceEmail.from_name
                ? `${sourceEmail.from_name} <${sourceEmail.from_email}>`
                : sourceEmail.from_email}
              {" · "}
              {fmtDate(sourceEmail.email_date)}
            </span>
          </span>
        </button>
        {openSource && (
          <div className="border-t border-border px-3 py-2">
            <div className="max-h-[320px] overflow-auto">
              <MailBody
                bodyHtml={sourceEmail.body_html}
                bodyText={sourceEmail.body_text}
                snippet={sourceEmail.snippet}
              />
            </div>
          </div>
        )}
      </div>
      )}

      {/* Eerdere mailtjes van de draad. */}
      {threadEmails.length > 0 && (
        <div className={cn("space-y-1.5")}>
          <p className="px-1 text-xs font-medium text-muted-foreground">
            Eerdere mailtjes in deze draad ({threadEmails.length})
          </p>
          {threadEmails.map((e) => (
            <ThreadRow key={e.id} summary={e} />
          ))}
        </div>
      )}
    </div>
  );
}
