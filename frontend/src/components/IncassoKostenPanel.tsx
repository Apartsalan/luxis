"use client";

import { useState, useEffect, useRef } from "react";
import { Scale, Check, AlertTriangle, Info } from "lucide-react";
import {
  useIncassoInvoicePreview,
  type IncassoInvoicePreview,
} from "@/hooks/use-invoices";
import { formatCurrency } from "@/lib/utils";

interface LineItem {
  description: string;
  quantity: string;
  unit_price: string;
  btw_percentage: string;
}

interface IncassoKostenPanelProps {
  caseId: string;
  onAddLine: (line: LineItem) => void;
}

export function IncassoKostenPanel({
  caseId,
  onAddLine,
}: IncassoKostenPanelProps) {
  const { data: preview, isLoading } = useIncassoInvoicePreview(caseId);

  // Local editable state
  const [bikAmount, setBikAmount] = useState("");
  const [renteAmount, setRenteAmount] = useState("");
  const [provisieBase, setProvisieBase] = useState<
    "collected_amount" | "total_claim"
  >("collected_amount");
  const [provisiePct, setProvisiePct] = useState("");
  const [provisieAmount, setProvisieAmount] = useState("");

  // Track which items have been added
  const [bikAdded, setBikAdded] = useState(false);
  const [renteAdded, setRenteAdded] = useState(false);
  const [provisieAdded, setProvisieAdded] = useState(false);

  // Pre-fill from preview data (only once)
  const initialized = useRef(false);
  useEffect(() => {
    if (preview && !initialized.current) {
      initialized.current = true;
      setBikAmount(Number(preview.bik.amount).toFixed(2));
      setRenteAmount(Number(preview.interest.amount).toFixed(2));
      setProvisieBase(
        preview.provisie.base as "collected_amount" | "total_claim"
      );
      setProvisiePct(String(preview.provisie.percentage));
      // Calculate initial provisie amount
      const base =
        preview.provisie.base === "total_claim"
          ? Number(preview.provisie.over_claim.amount)
          : Number(preview.provisie.over_collected.amount);
      setProvisieAmount(base.toFixed(2));
    }
  }, [preview]);

  // Recalculate provisie when base or percentage changes
  useEffect(() => {
    if (!preview) return;
    const pct = parseFloat(provisiePct) || 0;
    const baseAmount =
      provisieBase === "total_claim"
        ? Number(preview.principal)
        : Number(preview.collected_amount);
    const raw = (baseAmount * pct) / 100;
    const fixedCosts = Number(preview.provisie.fixed_costs);
    const minFee = Number(preview.provisie.minimum_fee);
    const total = Math.max(raw + fixedCosts, minFee);
    setProvisieAmount(total > 0 ? total.toFixed(2) : "0.00");
  }, [provisieBase, provisiePct, preview]);

  // DF117-05: hide the panel entirely when there's nothing relevant to show.
  // The case must have either a vordering (BIK relevant) or a provisie setting.
  const hasRelevantData =
    preview &&
    (Number(preview.principal) > 0 ||
      Number(preview.provisie.percentage) > 0 ||
      Number(preview.provisie.fixed_costs) > 0 ||
      Number(preview.provisie.minimum_fee) > 0);

  if (isLoading) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-5 animate-pulse">
        <div className="h-5 bg-amber-100 rounded w-48 mb-4" />
        <div className="space-y-3">
          <div className="h-10 bg-amber-100 rounded" />
          <div className="h-10 bg-amber-100 rounded" />
          <div className="h-10 bg-amber-100 rounded" />
        </div>
      </div>
    );
  }

  if (!preview) return null;
  if (!hasRelevantData) return null;

  // DF117-09: detect when minimum_fee is currently in play for the active base
  const activeProvOption =
    provisieBase === "total_claim"
      ? preview.provisie.over_claim
      : preview.provisie.over_collected;
  const minimumApplied = activeProvOption?.is_minimum_applied ?? false;

  const baseLabel =
    provisieBase === "total_claim"
      ? `totale vordering (${formatCurrency(Number(preview.principal))})`
      : `geincasseerd bedrag (${formatCurrency(Number(preview.collected_amount))})`;

  const noCollected = Number(preview.collected_amount) <= 0;

  const inputClass =
    "w-28 rounded-lg border border-input bg-background px-3 py-1.5 text-sm text-right font-medium focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50/30 p-5">
      <h3 className="text-sm font-semibold text-foreground flex items-center gap-2 mb-4">
        <Scale className="h-4 w-4 text-amber-600" />
        Incassokosten toevoegen
      </h3>

      <div className="space-y-4">
        {/* BIK row */}
        <CostRow
          label="BIK (art. 6:96 BW)"
          sublabel={preview.bik.source}
          amount={bikAmount}
          onAmountChange={setBikAmount}
          added={bikAdded}
          alreadyInvoiced={preview.already_invoiced.has_bik_line}
          invoices={preview.already_invoiced.invoices}
          inputClass={inputClass}
          onAdd={() => {
            onAddLine({
              description: "Buitengerechtelijke incassokosten (BIK)",
              quantity: "1",
              unit_price: bikAmount,
              btw_percentage: "21.00",
            });
            setBikAdded(true);
          }}
        />

        {/* Rente row */}
        <CostRow
          label="Rente op vordering"
          sublabel={preview.interest.source}
          amount={renteAmount}
          onAmountChange={setRenteAmount}
          added={renteAdded}
          alreadyInvoiced={preview.already_invoiced.has_rente_line}
          invoices={preview.already_invoiced.invoices}
          inputClass={inputClass}
          onAdd={() => {
            onAddLine({
              description: "Rente op vordering",
              quantity: "1",
              unit_price: renteAmount,
              btw_percentage: "21.00",
            });
            setRenteAdded(true);
          }}
        />

        {/* Provisie row */}
        <div className="rounded-lg border border-border bg-card p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-foreground">
                  Provisie
                </span>
                {preview.already_invoiced.has_provisie_line && (
                  <span className="inline-flex items-center gap-1 text-xs text-amber-600 bg-amber-100 px-2 py-0.5 rounded-full">
                    <AlertTriangle className="h-3 w-3" />
                    Al gefactureerd in{" "}
                    {preview.already_invoiced.invoices.join(", ")}
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                {provisiePct}% over {baseLabel}
              </p>
              {minimumApplied && (
                <p className="mt-1 inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-700 ring-1 ring-inset ring-amber-200">
                  <Info className="h-3 w-3" />
                  Minimumtarief van {formatCurrency(Number(preview.provisie.minimum_fee))} toegepast
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">€</span>
              <input
                type="number"
                step="0.01"
                min="0"
                value={provisieAmount}
                onChange={(e) => setProvisieAmount(e.target.value)}
                className={inputClass}
                disabled={provisieAdded}
              />
              {provisieAdded ? (
                <span className="inline-flex items-center gap-1 text-xs text-emerald-600 font-medium px-2">
                  <Check className="h-3.5 w-3.5" /> Toegevoegd
                </span>
              ) : (
                <button
                  onClick={() => {
                    const baseDesc =
                      provisieBase === "total_claim"
                        ? `Provisie ${provisiePct}% over totale vordering (${formatCurrency(Number(preview.principal))})`
                        : `Provisie ${provisiePct}% over geincasseerd bedrag (${formatCurrency(Number(preview.collected_amount))})`;
                    // DF117-09: when the minimum_fee is the binding constraint,
                    // make that explicit in the line description so the client
                    // understands why the amount differs from the percentage math.
                    const desc = minimumApplied
                      ? `${baseDesc} — minimumtarief van ${formatCurrency(Number(preview.provisie.minimum_fee))} toegepast`
                      : baseDesc;
                    onAddLine({
                      description: desc,
                      quantity: "1",
                      unit_price: provisieAmount,
                      btw_percentage: "21.00",
                    });
                    setProvisieAdded(true);
                  }}
                  disabled={
                    noCollected && provisieBase === "collected_amount"
                  }
                  className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors whitespace-nowrap"
                >
                  Toevoegen
                </button>
              )}
            </div>
          </div>

          {/* Provisie options */}
          <div className="mt-3 pt-3 border-t border-border space-y-2">
            <div className="flex gap-4">
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="radio"
                  name="prov_base"
                  checked={provisieBase === "collected_amount"}
                  onChange={() => setProvisieBase("collected_amount")}
                  disabled={provisieAdded}
                  className="text-primary"
                />
                <span className="text-xs">Over geincasseerd bedrag</span>
              </label>
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="radio"
                  name="prov_base"
                  checked={provisieBase === "total_claim"}
                  onChange={() => setProvisieBase("total_claim")}
                  disabled={provisieAdded}
                  className="text-primary"
                />
                <span className="text-xs">Over totale vordering</span>
              </label>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Percentage:</span>
              <input
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={provisiePct}
                onChange={(e) => setProvisiePct(e.target.value)}
                disabled={provisieAdded}
                className="w-16 rounded border border-input bg-background px-2 py-1 text-xs text-right focus:border-primary focus:outline-none"
              />
              <span className="text-xs text-muted-foreground">%</span>
            </div>
            {(Number(preview.provisie.fixed_costs) > 0 ||
              Number(preview.provisie.minimum_fee) > 0) && (
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <Info className="h-3 w-3" />
                {Number(preview.provisie.fixed_costs) > 0 &&
                  `Vaste kosten: ${formatCurrency(Number(preview.provisie.fixed_costs))}`}
                {Number(preview.provisie.fixed_costs) > 0 &&
                  Number(preview.provisie.minimum_fee) > 0 &&
                  " · "}
                {Number(preview.provisie.minimum_fee) > 0 &&
                  `Min. tarief: ${formatCurrency(Number(preview.provisie.minimum_fee))}`}
              </p>
            )}
            {noCollected && provisieBase === "collected_amount" && (
              <p className="text-xs text-amber-600 flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" />
                Nog geen incasso ontvangen
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/** Reusable row for BIK and Rente */
function CostRow({
  label,
  sublabel,
  amount,
  onAmountChange,
  added,
  alreadyInvoiced,
  invoices,
  inputClass,
  onAdd,
}: {
  label: string;
  sublabel: string;
  amount: string;
  onAmountChange: (v: string) => void;
  added: boolean;
  alreadyInvoiced: boolean;
  invoices: string[];
  inputClass: string;
  onAdd: () => void;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-3">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground">{label}</span>
            {alreadyInvoiced && (
              <span className="inline-flex items-center gap-1 text-xs text-amber-600 bg-amber-100 px-2 py-0.5 rounded-full">
                <AlertTriangle className="h-3 w-3" />
                Al gefactureerd in {invoices.join(", ")}
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">{sublabel}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">€</span>
          <input
            type="number"
            step="0.01"
            min="0"
            value={amount}
            onChange={(e) => onAmountChange(e.target.value)}
            className={inputClass}
            disabled={added}
          />
          {added ? (
            <span className="inline-flex items-center gap-1 text-xs text-emerald-600 font-medium px-2">
              <Check className="h-3.5 w-3.5" /> Toegevoegd
            </span>
          ) : (
            <button
              onClick={onAdd}
              disabled={!amount || parseFloat(amount) <= 0}
              className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors whitespace-nowrap"
            >
              Toevoegen
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
