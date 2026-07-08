// Bouwt de voor-invulling voor Beantwoorden / Doorsturen op basis van een
// bestaande mail. Het originele bericht wordt als geciteerd blok onder de
// (lege) schrijfruimte gezet, Gmail/Outlook-stijl.

import type { SyncedEmailDetail } from "@/hooks/use-email-sync";

export interface ReplyPrefill {
  to: string;
  toName: string;
  subject: string;
  bodyHtml: string;
  replyToMessageId: string | null;
  // Wortel van de gespreksdraad (References-root van het origineel). Zo krijgt
  // het verzonden antwoord dezelfde draad-identiteit als de rest van de keten —
  // ook bij een antwoord op een mail middenin een lang gesprek.
  referencesRoot: string | null;
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
  };
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
  };
}
