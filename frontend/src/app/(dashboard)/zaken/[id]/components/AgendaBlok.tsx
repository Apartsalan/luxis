"use client";

import Link from "next/link";
import { CalendarDays, ChevronRight } from "lucide-react";
import {
  useCaseEvents,
  EVENT_TYPE_LABELS,
  eventColor,
} from "@/hooks/use-calendar-events";
import { formatDateTime } from "@/lib/utils";

/**
 * S216 blok 3: komende afspraken/zittingen van dit dossier op het Overzicht.
 * Grootste gemis voor gewone (advies)zaken t.o.v. Clio/Smokeball. Rendert niets
 * als er geen toekomstige afspraken zijn (nu bij elk dossier — verschijnt zodra
 * Lisanne afspraken aan het dossier koppelt). Werkt voor beide zaaktypes.
 */
export default function AgendaBlok({ caseId }: { caseId: string }) {
  const { data: events } = useCaseEvents(caseId);
  const now = Date.now();
  const upcoming = (events ?? [])
    .filter((e) => e.start_time && new Date(e.start_time).getTime() >= now)
    .sort(
      (a, b) =>
        new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
    )
    .slice(0, 4);

  if (upcoming.length === 0) return null;

  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border px-5 py-4">
        <div className="flex items-center gap-2">
          <CalendarDays className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold text-card-foreground">
            Komende afspraken
          </h2>
        </div>
        <Link href="/agenda" className="text-xs text-primary hover:underline">
          Agenda
        </Link>
      </div>
      <ul className="divide-y divide-border">
        {upcoming.map((e) => (
          <li key={e.id}>
            <Link
              href="/agenda"
              className="flex items-center gap-3 px-5 py-3 transition-colors hover:bg-muted/50"
            >
              <span
                className="h-2.5 w-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: eventColor(e.color) }}
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">
                  {e.title}
                </p>
                <p className="text-xs text-muted-foreground">
                  {EVENT_TYPE_LABELS[e.event_type] ?? e.event_type} ·{" "}
                  {formatDateTime(e.start_time)}
                </p>
              </div>
              <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
