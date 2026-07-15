"use client";

import { AlertTriangle } from "lucide-react";
import { useConflictCheck } from "@/hooks/use-cases";
import type { CaseDetail } from "@/hooks/use-cases";

/**
 * Conflictcontrole-waarschuwing voor cliënt + wederpartij van dit dossier.
 * Verhuisd uit het (opgeheven) Partijen-tabblad naar het Overzicht (S216) zodat
 * de tegenstrijdig-belang-waarschuwing prominenter is en niet met het tabblad
 * verdwijnt. Rendert niets als er geen conflict is.
 */
export default function CaseConflictBanner({ zaak }: { zaak: CaseDetail }) {
  const { data: clientConflict } = useConflictCheck(
    zaak.client?.id || undefined,
    "client"
  );
  const { data: opponentConflict } = useConflictCheck(
    zaak.opposing_party?.id || undefined,
    "opposing_party"
  );

  const hasClient = clientConflict?.has_conflict;
  const hasOpponent = opponentConflict?.has_conflict;
  if (!hasClient && !hasOpponent) return null;

  return (
    <div className="space-y-3">
      {hasClient && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium text-amber-800">
                Conflict gedetecteerd — cliënt
              </p>
              <p className="mt-0.5 text-xs text-amber-700">
                {zaak.client?.name} is in {clientConflict.conflicts.length === 1 ? "een ander dossier" : `${clientConflict.conflicts.length} andere dossiers`} wederpartij:
              </p>
              <ul className="mt-1 space-y-0.5">
                {clientConflict.conflicts.map((c) => (
                  <li key={c.case_id} className="text-xs text-amber-700">
                    <span className="font-mono font-medium">{c.case_number}</span>
                    {" — wederpartij van "}
                    <span className="font-medium">{c.client_name}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
      {hasOpponent && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium text-amber-800">
                Conflict gedetecteerd — wederpartij
              </p>
              <p className="mt-0.5 text-xs text-amber-700">
                {zaak.opposing_party?.name} is in {opponentConflict.conflicts.length === 1 ? "een ander dossier" : `${opponentConflict.conflicts.length} andere dossiers`} cliënt:
              </p>
              <ul className="mt-1 space-y-0.5">
                {opponentConflict.conflicts.map((c) => (
                  <li key={c.case_id} className="text-xs text-amber-700">
                    <span className="font-mono font-medium">{c.case_number}</span>
                    {" — cliënt"}
                    {c.opposing_party_name && (
                      <span> vs. {c.opposing_party_name}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
