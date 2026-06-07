"use client";

import dynamic from "next/dynamic";

// TipTap is de zwaarste dependency van de frontend-bundle. Lazy laden zodat
// dossier-detail snel opent en TipTap pas binnenkomt wanneer er echt een
// notitie-editor gerenderd wordt.
export const RichNoteEditor = dynamic(
  () => import("./rich-note-editor").then((m) => m.RichNoteEditor),
  {
    ssr: false,
    loading: () => (
      <div className="rounded-lg border border-input bg-background min-h-[118px]" />
    ),
  }
);

/** Check if a note HTML string is effectively empty */
export function isNoteEmpty(html: string | undefined | null): boolean {
  if (!html) return true;
  return html.replace(/<[^>]*>/g, "").trim() === "";
}
