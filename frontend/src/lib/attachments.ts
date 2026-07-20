/**
 * Bijlagen openen — één gedeelde route (S231).
 *
 * Aanleiding: elke plek die bijlagen toonde had zijn eigen manier van openen —
 * en drie ervan konden het helemaal niet. De dossier-chip in de mail-dialoog
 * had een klikbare knop die stilletjes niets deed, de "gaat automatisch mee"-
 * etiketten waren doodlopende labels, en de Mail-pagina linkte kaal naar de
 * download-route zonder inlogbewijs (de server weigert dat met 401).
 * Klassiek kruispunt: één effect, vijf implementaties, drie gaten.
 *
 * Alles loopt nu via `openBlobInTab`, dat het inlogbewijs meestuurt (`api()`),
 * de bytes ophaalt en ze in een nieuw tabblad toont. De aanroepers verschillen
 * alleen in wélke URL de bytes levert.
 */

import { api } from "@/lib/api";

/** Popup-blokkade: open het tabblad synchroon bij de klik, vul het daarna. */
function openTab(): Window | null {
  return window.open("", "_blank");
}

async function openBlobInTab(
  url: string,
  init: RequestInit | undefined,
  tab: Window | null,
): Promise<void> {
  try {
    const res = await api(url, init);
    if (!res.ok) throw new Error(`Openen mislukt (${res.status})`);
    const blob = await res.blob();
    const objectUrl = URL.createObjectURL(blob);
    if (tab) {
      tab.location.href = objectUrl;
    } else {
      // Popup geblokkeerd → val terug op hetzelfde tabblad.
      window.location.href = objectUrl;
    }
    // Ruim de URL pas op als de browser hem geladen heeft.
    setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
  } catch (err) {
    tab?.close();
    throw err;
  }
}

/** Bestand dat al in een dossier zit (upload, factuur, opgeslagen bijlage). */
export async function openCaseFile(caseId: string, fileId: string): Promise<void> {
  await openBlobInTab(`/api/cases/${caseId}/files/${fileId}/download`, undefined, openTab());
}

/** Bijlage van een ontvangen/verstuurde e-mail. */
export async function openEmailAttachment(attachmentId: string): Promise<void> {
  await openBlobInTab(`/api/email/attachments/${attachmentId}/download`, undefined, openTab());
}

/**
 * Bijlage die de server pas bij verzending maakt (renteoverzicht,
 * concept-verzoekschrift). Wordt hier vers gerenderd zodat je hem vooraf kunt
 * inzien — exact hetzelfde sjabloon en dezelfde dossierdata als bij verzending.
 */
export async function openRenderedTemplate(
  caseId: string,
  templateType: string,
): Promise<void> {
  const tab = openTab();
  try {
    const res = await api(`/api/documents/docx/cases/${caseId}/render-pdf`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ template_type: templateType }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Renderen mislukt (${res.status})`);
    }
    const data = (await res.json()) as { data_base64: string; content_type: string };
    const bytes = Uint8Array.from(atob(data.data_base64), (c) => c.charCodeAt(0));
    const objectUrl = URL.createObjectURL(
      new Blob([bytes], { type: data.content_type || "application/pdf" }),
    );
    if (tab) tab.location.href = objectUrl;
    else window.location.href = objectUrl;
    setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
  } catch (err) {
    tab?.close();
    throw err;
  }
}

/** Al in het geheugen geladen bijlage (upload, bibliotheek-sjabloon). */
export function openInlineBase64(
  dataBase64: string,
  contentType = "application/pdf",
): void {
  const bytes = Uint8Array.from(atob(dataBase64), (c) => c.charCodeAt(0));
  const objectUrl = URL.createObjectURL(new Blob([bytes], { type: contentType }));
  window.open(objectUrl, "_blank");
  setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
}

/**
 * De ene functie die elke bijlage-weergave aanroept. Kiest de juiste route op
 * basis van wat er bekend is; gooit als er niets te openen valt, zodat een
 * nieuwe bijlagesoort niet stil in een dode knop eindigt.
 */
export async function openAttachment(opts: {
  caseId?: string;
  fileId?: string;
  templateType?: string;
  emailAttachmentId?: string;
  inlineBase64?: string;
  contentType?: string;
}): Promise<void> {
  if (opts.inlineBase64) return openInlineBase64(opts.inlineBase64, opts.contentType);
  if (opts.emailAttachmentId) return openEmailAttachment(opts.emailAttachmentId);
  if (opts.caseId && opts.fileId) return openCaseFile(opts.caseId, opts.fileId);
  if (opts.caseId && opts.templateType)
    return openRenderedTemplate(opts.caseId, opts.templateType);
  throw new Error("Deze bijlage heeft geen bron om te openen");
}
