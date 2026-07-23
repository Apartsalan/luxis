// Bouwt de voor-invulling voor Beantwoorden / Doorsturen op basis van een
// bestaande mail. Het originele bericht wordt als geciteerd blok onder de
// (lege) schrijfruimte gezet, Gmail/Outlook-stijl.

import { api } from "@/lib/api";
import type { SyncedEmailDetail } from "@/hooks/use-email-sync";

export interface ReplyPrefill {
  to: string;
  toName: string;
  subject: string;
  bodyHtml: string;
  // S244 — true als bodyHtml al de volledige huisstijl draagt (vrij-bericht-
  // shell); de verzendkant slaat de server-aankleding dan over.
  branded?: boolean;
  replyToMessageId: string | null;
  // Wortel van de gespreksdraad (References-root van het origineel). Zo krijgt
  // het verzonden antwoord dezelfde draad-identiteit als de rest van de keten —
  // ook bij een antwoord op een mail middenin een lang gesprek.
  referencesRoot: string | null;
  // Bij doorsturen: het id van de oorspronkelijke mail, zodat de achterkant de
  // bijlagen daarvan meestuurt. Bij beantwoorden null (geen bijlagen meesturen).
  forwardFromEmailId: string | null;
}

function stripPrefix(subject: string, prefixes: string[]): string {
  const s = subject.trim();
  for (const p of prefixes) {
    if (s.toLowerCase().startsWith(p.toLowerCase())) return s; // al aanwezig
  }
  return s;
}

function quoteBlock(email: SyncedEmailDetail): string {
  const when = new Date(email.email_date).toLocaleString("nl-NL", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
  const sender = email.from_name
    ? `${email.from_name} &lt;${email.from_email}&gt;`
    : email.from_email;
  const original =
    email.body_html ||
    `<p>${(email.body_text || email.snippet || "").replace(/\n/g, "<br>")}</p>`;
  return (
    `<p></p><p></p>` +
    `<div style="border-left:2px solid #ccc;padding-left:12px;color:#555;margin-top:8px">` +
    `<p style="color:#888;font-size:12px">Op ${when} schreef ${sender}:</p>` +
    original +
    `</div>`
  );
}

/** Beantwoorden: naar de afzender, "Re:", geciteerd origineel, gekoppeld aan de keten. */
export function buildReplyPrefill(email: SyncedEmailDetail): ReplyPrefill {
  const subject = stripPrefix(email.subject, ["re:"]);
  return {
    to: email.from_email,
    toName: email.from_name || "",
    subject: subject.toLowerCase().startsWith("re:") ? subject : `Re: ${subject}`,
    bodyHtml: quoteBlock(email),
    replyToMessageId: email.provider_message_id ?? null,
    referencesRoot: email.provider_thread_id ?? null,
    forwardFromEmailId: null, // beantwoorden = geen bijlagen meesturen
  };
}

/**
 * S244 — Beantwoorden met de vrij-bericht-shell: aanhef + huisstijl +
 * handtekening al ingevuld, geciteerd origineel onderaan — Lisanne typt
 * alleen nog de inhoud. Alleen voor dossier-gekoppelde mail (de shell wordt
 * met dossiergegevens opgebouwd); anders — of als het renderen faalt — valt
 * dit terug op de kale reply (huisstijl komt dan bij verzenden alsnog).
 */
export async function buildReplyPrefillWithShell(
  email: SyncedEmailDetail
): Promise<ReplyPrefill> {
  const base = buildReplyPrefill(email);
  if (!email.case_id) return base;
  try {
    const res = await api(`/api/email/compose/cases/${email.case_id}/render-template`, {
      method: "POST",
      body: JSON.stringify({ template_type: "vrij_bericht", quoted_html: base.bodyHtml }),
    });
    if (!res.ok) return base;
    const d = await res.json();
    if (d.supported && d.body_html) {
      return { ...base, bodyHtml: d.body_html, branded: true };
    }
  } catch {
    /* val terug op kale reply */
  }
  return base;
}

/** Doorsturen: lege ontvanger, "Fwd:", geciteerd origineel, nieuwe keten. */
export function buildForwardPrefill(email: SyncedEmailDetail): ReplyPrefill {
  const subject = stripPrefix(email.subject, ["fwd:", "fw:"]);
  const to = email.to_emails.join(", ");
  const header =
    `<p style="color:#888;font-size:12px">` +
    `--- Doorgestuurd bericht ---<br>` +
    `Van: ${email.from_name ? `${email.from_name} &lt;${email.from_email}&gt;` : email.from_email}<br>` +
    `Onderwerp: ${email.subject}<br>` +
    `Aan: ${to}</p>`;
  const original =
    email.body_html ||
    `<p>${(email.body_text || email.snippet || "").replace(/\n/g, "<br>")}</p>`;
  return {
    to: "",
    toName: "",
    subject: subject.toLowerCase().startsWith("fwd:") ? subject : `Fwd: ${subject}`,
    bodyHtml: `<p></p><p></p>${header}${original}`,
    replyToMessageId: null,
    referencesRoot: null, // doorsturen = nieuwe keten
    forwardFromEmailId: email.id, // bijlagen van het origineel meesturen
  };
}
