"use client";

import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface DraftSource {
  type: string;
  reference: string;
}

/**
 * AI draft response — matches backend AIDraftResponse schema.
 * Returned by both legacy /api/ai-agent/draft/{case_id} and new
 * /api/ai/draft endpoints; consumers should prefer body_html (branded
 * wrap) when present and fall back to body (plain text).
 */
export interface AiDraft {
  id?: string;
  case_id?: string;
  case_number?: string;
  subject: string;
  body: string;
  body_html?: string | null;
  tone: string;
  sources?: DraftSource[] | null;
  reasoning?: string | null;
  status?: string;
  model_used?: string | null;
  /** Legacy field name — older endpoint returned `model`. Kept for compat. */
  model?: string;
}

export type DraftIntent = "next_step" | "reply_to_email" | "free_compose";

interface GenerateDraftArgs {
  caseId: string;
  intent?: DraftIntent;
  tone?: string;
  sourceEmailId?: string;
  instruction?: string;
}

/**
 * S145: routes via /api/ai/draft (UnifiedDraftService) so the AI draft uses
 * the same branded render path as batch-incasso brieven. Returns body_html
 * with embedded data-URL logo + case_type-aware signature.
 */
export function useGenerateDraft() {
  return useMutation<AiDraft, Error, GenerateDraftArgs>({
    mutationFn: async ({ caseId, intent = "free_compose", tone, sourceEmailId, instruction }) => {
      const res = await api(`/api/ai/draft`, {
        method: "POST",
        body: JSON.stringify({
          case_id: caseId,
          intent,
          tone: tone ?? null,
          source_email_id: sourceEmailId ?? null,
          instruction: instruction ?? null,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Concept genereren mislukt");
      }
      return res.json();
    },
  });
}
