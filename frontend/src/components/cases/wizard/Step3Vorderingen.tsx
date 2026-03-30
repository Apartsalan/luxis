import { FileText, Plus, Trash2 } from "lucide-react";
import { ConfidenceDot } from "./ConfidenceDot";
import type { ClaimForm } from "./types";
import type { InvoiceParseResult } from "@/hooks/use-invoice-parser";

interface Step3Props {
  claims: ClaimForm[];
  updateClaim: (index: number, field: keyof ClaimForm, value: string) => void;
  addClaim: () => void;
  removeClaim: (index: number) => void;
  inputClass: string;
  fieldConfidence: Record<string, number>;
  invoiceData: InvoiceParseResult | null;
}

export function Step3Vorderingen({
  claims,
  updateClaim,
  addClaim,
  removeClaim,
  inputClass,
  fieldConfidence,
  invoiceData,
}: Step3Props) {
  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border bg-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-foreground">
              Vorderingen
            </h2>
            <p className="text-xs text-muted-foreground">
              Voeg een of meerdere vorderingen toe aan dit dossier.
              Dit kan ook later.
            </p>
          </div>
        </div>

        {claims.map((claim, index) => (
          <div
            key={index}
            className="rounded-lg border border-border bg-background p-4 space-y-3"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium text-foreground">
                  Vordering {index + 1}
                </span>
              </div>
              {claims.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeClaim(index)}
                  className="rounded-md p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-foreground">
                  Omschrijving
                  {index === 0 && invoiceData && <ConfidenceDot field="description" confidence={fieldConfidence} />}
                </label>
                <input
                  type="text"
                  value={claim.description}
                  onChange={(e) =>
                    updateClaim(index, "description", e.target.value)
                  }
                  className={inputClass}
                  placeholder="Bijv. Factuur nr. 2025-001"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground">
                  Hoofdsom
                  {index === 0 && invoiceData && <ConfidenceDot field="principal_amount" confidence={fieldConfidence} />}
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={claim.principal_amount}
                  onChange={(e) =>
                    updateClaim(
                      index,
                      "principal_amount",
                      e.target.value
                    )
                  }
                  className={inputClass}
                  placeholder="0.00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground">
                  Verzuimdatum
                  {index === 0 && invoiceData && <ConfidenceDot field="due_date" confidence={fieldConfidence} />}
                </label>
                <input
                  type="date"
                  value={claim.default_date}
                  onChange={(e) =>
                    updateClaim(index, "default_date", e.target.value)
                  }
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground">
                  Factuurnummer
                  {index === 0 && invoiceData && <ConfidenceDot field="invoice_number" confidence={fieldConfidence} />}
                </label>
                <input
                  type="text"
                  value={claim.invoice_number}
                  onChange={(e) =>
                    updateClaim(index, "invoice_number", e.target.value)
                  }
                  className={inputClass}
                  placeholder="Optioneel"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground">
                  Factuurdatum
                  {index === 0 && invoiceData && <ConfidenceDot field="invoice_date" confidence={fieldConfidence} />}
                </label>
                <input
                  type="date"
                  value={claim.invoice_date}
                  onChange={(e) =>
                    updateClaim(index, "invoice_date", e.target.value)
                  }
                  className={inputClass}
                />
              </div>
            </div>
          </div>
        ))}

        <button
          type="button"
          onClick={addClaim}
          className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Nog een vordering toevoegen
        </button>
      </div>
    </div>
  );
}
