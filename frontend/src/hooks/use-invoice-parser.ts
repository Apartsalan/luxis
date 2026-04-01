"use client";

import { useMutation } from "@tanstack/react-query";
import { tokenStore } from "@/lib/token-store";

// ── Types ────────────────────────────────────────────────────────────────

export interface InvoiceParseResult {
  debtor_name: string | null;
  debtor_contact_person: string | null;
  debtor_type: "company" | "person" | null;
  debtor_address: string | null;
  debtor_postcode: string | null;
  debtor_city: string | null;
  debtor_postal_address: string | null;
  debtor_postal_postcode: string | null;
  debtor_postal_city: string | null;
  debtor_kvk: string | null;
  debtor_email: string | null;
  creditor_name: string | null;
  creditor_contact_person: string | null;
  creditor_type: "company" | "person" | null;
  creditor_address: string | null;
  creditor_postcode: string | null;
  creditor_city: string | null;
  creditor_postal_address: string | null;
  creditor_postal_postcode: string | null;
  creditor_postal_city: string | null;
  creditor_kvk: string | null;
  creditor_btw: string | null;
  creditor_email: string | null;
  invoice_number: string | null;
  invoice_date: string | null;
  due_date: string | null;
  principal_amount: number | null;
  description: string | null;
  confidence: Record<string, number>;
  model: string;
}

// ── Hook ─────────────────────────────────────────────────────────────────

export function useParseInvoice() {
  return useMutation<InvoiceParseResult, Error, File>({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);

      const token = tokenStore.getAccess();
      const res = await fetch("/api/ai-agent/parse-invoice", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Factuur parsing mislukt" }));
        throw new Error(err.detail || "Factuur parsing mislukt");
      }

      return res.json();
    },
  });
}
