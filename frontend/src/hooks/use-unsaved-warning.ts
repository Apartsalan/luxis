"use client";

import { useEffect } from "react";

/**
 * Shows a browser "unsaved changes" warning when the user tries to navigate away
 * or close the tab while there are unsaved changes.
 *
 * @param isDirty - Whether there are unsaved changes
 */
export function useUnsavedWarning(isDirty: boolean) {
  useEffect(() => {
    if (!isDirty) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isDirty]);
}
