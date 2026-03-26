"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import { Euro, FileText, Loader2, Save } from "lucide-react";
import { toast } from "sonner";
import { useCase, useUpdateCase } from "@/hooks/use-cases";
import { useProvisie } from "@/hooks/use-invoices";
import { formatCurrency } from "@/lib/utils";

export function ProvisieSettingsSection({ caseId }: { caseId: string }) {
  const { data: zaak } = useCase(caseId);
  const updateCase = useUpdateCase();
  const { data: provisie } = useProvisie(caseId);
  const [editing, setEditing] = useState(false);
  const [provPerc, setProvPerc] = useState(
    zaak?.provisie_percentage?.toString() || ""
  );
  const [fixedCosts, setFixedCosts] = useState(
    zaak?.fixed_case_costs?.toString() || ""
  );
  const [minFee, setMinFee] = useState(
    zaak?.minimum_fee?.toString() || ""
  );
  const [provBase, setProvBase] = useState(
    zaak?.provisie_base || "collected_amount"
  );

  // Sync state when zaak data changes
  const zaakRef = useRef(zaak);
  if (zaak && zaak !== zaakRef.current) {
    zaakRef.current = zaak;
    if (!editing) {
      setProvPerc(zaak.provisie_percentage?.toString() || "");
      setFixedCosts(zaak.fixed_case_costs?.toString() || "");
      setMinFee(zaak.minimum_fee?.toString() || "");
      setProvBase(zaak.provisie_base || "collected_amount");
    }
  }

  const handleSave = async () => {
    try {
      await updateCase.mutateAsync({
        id: caseId,
        data: {
          provisie_percentage: provPerc || null,
          fixed_case_costs: fixedCosts || null,
          minimum_fee: minFee || null,
          provisie_base: provBase,
        },
      });
      toast.success("Provisie-instellingen opgeslagen");
      setEditing(false);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Opslaan mislukt");
    }
  };

  const inputClass =
    "w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
          <Euro className="h-5 w-5 text-primary" />
          Facturatie-instellingen
        </h2>
        {!editing && (
          <button
            onClick={() => setEditing(true)}
            className="text-xs font-medium text-primary hover:text-primary/80 transition-colors"
          >
            Wijzigen
          </button>
        )}
      </div>

      {editing ? (
        <div className="rounded-xl border border-primary/20 bg-card p-5 space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Provisiepercentage (%)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={provPerc}
                onChange={(e) => setProvPerc(e.target.value)}
                placeholder="bijv. 15"
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Vaste dossierkosten (€)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={fixedCosts}
                onChange={(e) => setFixedCosts(e.target.value)}
                placeholder="0.00"
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">
                Minimumkosten (€)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={minFee}
                onChange={(e) => setMinFee(e.target.value)}
                placeholder="0.00"
                className={inputClass}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Berekeningsbasis
            </label>
            <div className="flex gap-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="provisie_base"
                  value="collected_amount"
                  checked={provBase === "collected_amount"}
                  onChange={() => setProvBase("collected_amount")}
                  className="text-primary"
                />
                <span className="text-sm">Over geïncasseerd bedrag</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="provisie_base"
                  value="total_claim"
                  checked={provBase === "total_claim"}
                  onChange={() => setProvBase("total_claim")}
                  className="text-primary"
                />
                <span className="text-sm">Over totale vordering</span>
              </label>
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={updateCase.isPending}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {updateCase.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Opslaan
            </button>
            <button
              onClick={() => {
                setEditing(false);
                setProvPerc(zaak?.provisie_percentage?.toString() || "");
                setFixedCosts(zaak?.fixed_case_costs?.toString() || "");
                setMinFee(zaak?.minimum_fee?.toString() || "");
                setProvBase(zaak?.provisie_base || "collected_amount");
              }}
              className="rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-muted transition-colors"
            >
              Annuleren
            </button>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-card p-5">
          <dl className="grid grid-cols-4 gap-4">
            <div>
              <dt className="text-xs text-muted-foreground">Provisie</dt>
              <dd className="text-sm font-medium text-foreground mt-0.5">
                {zaak?.provisie_percentage != null ? `${zaak.provisie_percentage}%` : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Vaste dossierkosten</dt>
              <dd className="text-sm font-medium text-foreground mt-0.5">
                {zaak?.fixed_case_costs != null ? formatCurrency(zaak.fixed_case_costs) : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Minimumkosten</dt>
              <dd className="text-sm font-medium text-foreground mt-0.5">
                {zaak?.minimum_fee != null ? formatCurrency(zaak.minimum_fee) : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Berekeningsbasis</dt>
              <dd className="text-sm font-medium text-foreground mt-0.5">
                {zaak?.provisie_base === "total_claim" ? "Totale vordering" : "Geïncasseerd bedrag"}
              </dd>
            </div>
          </dl>

          {/* Berekend provisie bedrag */}
          {provisie && provisie.collected_amount > 0 && (
            <div className="mt-4 pt-4 border-t border-border">
              <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">
                Berekend honorarium
              </p>
              <dl className="grid grid-cols-2 gap-3">
                <div>
                  <dt className="text-xs text-muted-foreground">Geïnd bedrag</dt>
                  <dd className="text-sm font-medium text-foreground">
                    {formatCurrency(provisie.collected_amount)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Provisie ({provisie.provisie_percentage}%)</dt>
                  <dd className="text-sm font-medium text-foreground">
                    {formatCurrency(provisie.provisie_amount)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">Dossierkosten</dt>
                  <dd className="text-sm font-medium text-foreground">
                    {formatCurrency(provisie.fixed_case_costs)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground font-semibold">Totaal honorarium</dt>
                  <dd className="text-sm font-bold text-primary">
                    {formatCurrency(provisie.total_fee)}
                  </dd>
                </div>
              </dl>
              {provisie.minimum_fee > 0 && provisie.total_fee <= provisie.minimum_fee && (
                <p className="mt-2 text-xs text-amber-600">
                  Minimumkosten van {formatCurrency(provisie.minimum_fee)} zijn van toepassing
                </p>
              )}
              <div className="mt-4">
                <Link
                  href={`/facturen/nieuw?case_id=${caseId}&provisie=true`}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  <FileText className="h-4 w-4" />
                  Provisie factureren
                </Link>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
