"use client";

import { AlertTriangle } from "lucide-react";
import type { CaseDetail } from "@/hooks/use-cases";

const MARKER = "[BaseNet-waarschuwing]";

/**
 * Haalt de waarschuwingstekst uit `debtor_notes`: alles tussen de
 * `[BaseNet-waarschuwing]`-markering en de volgende `[BaseNet-...]`-markering.
 * Geëxporteerd zodat de logica los te testen is. Retourneert "" als er geen
 * waarschuwing is.
 */
export function extractBasenetWarning(notes: string | null | undefined): string {
  if (!notes) return "";
  const idx = notes.indexOf(MARKER);
  if (idx < 0) return "";
  const after = notes.slice(idx + MARKER.length);
  const next = after.search(/\[BaseNet-/);
  const raw = next >= 0 ? after.slice(0, next) : after;
  // meerdere lege regels inklappen tot één, randen trimmen
  return raw.replace(/\n{2,}/g, "\n").trim();
}

/**
 * S216 blok 2: geïmporteerde BaseNet-waarschuwingen ("Failliet", "NIET REAGEREN
 * — procedure loopt", "PROCEDEREN") stonden verstopt onderin het veld
 * Debiteurnotities. Nu als oranje balk bovenaan het dossier. Rendert niets als
 * er geen waarschuwing is.
 */
export default function BasenetWarningBanner({ zaak }: { zaak: CaseDetail }) {
  const text = extractBasenetWarning(zaak.debtor_notes);
  if (!text) return null;

  return (
    <div className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3">
      <div className="flex items-start gap-2">
        <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
        <div className="min-w-0">
          <p className="text-sm font-medium text-amber-800">Let op (uit BaseNet)</p>
          <p className="mt-0.5 whitespace-pre-wrap text-sm text-amber-700">{text}</p>
        </div>
      </div>
    </div>
  );
}
