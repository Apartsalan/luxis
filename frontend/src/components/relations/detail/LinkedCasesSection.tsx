import Link from "next/link";
import { Briefcase } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import {
  CASE_STATUS_LABELS as STATUS_LABELS,
  CASE_STATUS_BADGE as STATUS_BADGE,
} from "@/lib/status-constants";
import type { CaseSummary } from "@/hooks/use-cases";

interface LinkedCasesSectionProps {
  contactId: string;
  contactName: string;
  cases: CaseSummary[] | undefined;
}

export function LinkedCasesSection({
  contactId,
  contactName,
  cases,
}: LinkedCasesSectionProps) {
  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between px-5 py-4 border-b border-border">
        <div className="flex items-center gap-2">
          <Briefcase className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold text-card-foreground">
            Gekoppelde dossiers
            {cases && cases.length > 0 && (
              <span className="ml-1.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                {cases.length}
              </span>
            )}
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href={`/zaken/nieuw?client_id=${contactId}&client_name=${encodeURIComponent(contactName)}`}
            className="text-xs text-primary hover:underline"
          >
            + Als client
          </Link>
          <span className="text-xs text-muted-foreground">|</span>
          <Link
            href={`/zaken/nieuw?opposing_party_id=${contactId}&opposing_party_name=${encodeURIComponent(contactName)}`}
            className="text-xs text-amber-600 hover:underline"
          >
            + Als wederpartij
          </Link>
        </div>
      </div>
      {cases && cases.length > 0 ? (
        <div className="divide-y divide-border">
          {cases.map((zaak) => (
            <Link
              key={zaak.id}
              href={`/zaken/${zaak.id}`}
              className="flex items-center justify-between px-5 py-3.5 hover:bg-muted/40 transition-colors"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono font-semibold text-foreground">
                    {zaak.case_number}
                  </span>
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset ${
                      STATUS_BADGE[zaak.status] ??
                      "bg-slate-50 text-slate-600 ring-slate-500/20"
                    }`}
                  >
                    {STATUS_LABELS[zaak.status] ?? zaak.status}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5 truncate">
                  {zaak.client?.id === contactId && zaak.opposing_party
                    ? `vs. ${zaak.opposing_party.name}`
                    : zaak.client?.name ?? zaak.description ?? ""}
                </p>
              </div>
              <div className="text-right shrink-0 ml-3">
                <p className="text-sm font-semibold text-foreground tabular-nums">
                  {formatCurrency(zaak.total_principal)}
                </p>
                <span
                  className={`text-[10px] font-medium ${
                    zaak.client?.id === contactId
                      ? "text-primary"
                      : zaak.opposing_party?.id === contactId
                      ? "text-amber-600"
                      : "text-violet-600"
                  }`}
                >
                  {zaak.client?.id === contactId ? "Client" : zaak.opposing_party?.id === contactId ? "Wederpartij" : "Partij"}
                </span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="px-5 py-8 text-center">
          <Briefcase className="mx-auto h-8 w-8 text-muted-foreground/30 mb-2" />
          <p className="text-sm text-muted-foreground">
            Nog geen gekoppelde dossiers
          </p>
          <Link
            href={`/zaken/nieuw?client_id=${contactId}&client_name=${encodeURIComponent(contactName)}`}
            className="mt-1 inline-block text-sm text-primary hover:underline"
          >
            Maak een nieuw dossier aan
          </Link>
        </div>
      )}
    </div>
  );
}
