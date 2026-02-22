"use client";

import Link from "next/link";
import { AlertTriangle, Building2, User } from "lucide-react";
import { useConflictCheck } from "@/hooks/use-cases";

export default function PartijenTab({ zaak }: { zaak: any }) {
  const { data: clientConflict } = useConflictCheck(
    zaak.client?.id || undefined,
    "client"
  );
  const { data: opponentConflict } = useConflictCheck(
    zaak.opposing_party?.id || undefined,
    "opposing_party"
  );

  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <h2 className="mb-4 text-sm font-semibold text-card-foreground uppercase tracking-wider">
        Partijen
      </h2>
      <div className="grid gap-3 sm:grid-cols-2">
        {zaak.client && (
          <Link
            href={`/relaties/${zaak.client.id}`}
            className="flex items-center gap-3 rounded-lg border border-border p-4 hover:border-primary/30 hover:bg-muted/50 transition-all"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
              <Building2 className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">
                {zaak.client.name}
              </p>
              <span className="text-xs font-medium text-primary">Client</span>
            </div>
          </Link>
        )}
        {zaak.opposing_party && (
          <Link
            href={`/relaties/${zaak.opposing_party.id}`}
            className="flex items-center gap-3 rounded-lg border border-border p-4 hover:border-amber-300/50 hover:bg-muted/50 transition-all"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-50">
              <User className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">
                {zaak.opposing_party.name}
              </p>
              <span className="text-xs font-medium text-amber-600">
                Wederpartij
              </span>
            </div>
          </Link>
        )}
        {zaak.parties &&
          zaak.parties.map((party: any) => (
            <Link
              key={party.id}
              href={`/relaties/${party.contact.id}`}
              className="flex items-center gap-3 rounded-lg border border-border p-4 hover:bg-muted/50 transition-all"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                <User className="h-5 w-5 text-muted-foreground" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">
                  {party.contact.name}
                </p>
                <span className="text-xs font-medium text-muted-foreground">
                  {party.role}
                </span>
                {party.external_reference && (
                  <p className="text-xs text-muted-foreground font-mono mt-0.5">
                    Ref: {party.external_reference}
                  </p>
                )}
              </div>
            </Link>
          ))}
      </div>

      {/* Conflict warnings */}
      {clientConflict?.has_conflict && (
        <div className="mt-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium text-amber-800">
                Conflict gedetecteerd — client
              </p>
              <p className="mt-0.5 text-xs text-amber-700">
                {zaak.client.name} is in {clientConflict.conflicts.length === 1 ? "een ander dossier" : `${clientConflict.conflicts.length} andere dossiers`} wederpartij:
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
      {opponentConflict?.has_conflict && (
        <div className="mt-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium text-amber-800">
                Conflict gedetecteerd — wederpartij
              </p>
              <p className="mt-0.5 text-xs text-amber-700">
                {zaak.opposing_party.name} is in {opponentConflict.conflicts.length === 1 ? "een ander dossier" : `${opponentConflict.conflicts.length} andere dossiers`} client:
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
