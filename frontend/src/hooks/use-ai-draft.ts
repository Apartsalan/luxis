"use client";

import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface DraftSource {
  type: string;
  reference: string;
}

export interface AiDraft {
  subject: string;
  body: string;
  tone: string;
  sources: DraftSource[];
  reasoning: string;
  model: string;
  case_number: string;
}

export function useGenerateDraft() {
  return useMutation<AiDraft, Error, { caseId: string; instruction?: string }>({
    mutationFn: async ({ caseId, instruction }) => {
      const res = await api(`/api/ai-agent/draft/${caseId}`, {
        method: "POST",
        body: JSON.stringify(instruction ? { instruction } : {}),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail ?? "Concept genereren mislukt");
      }
      return res.json();
    },
  });
}
