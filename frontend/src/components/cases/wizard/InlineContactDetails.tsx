import { ChevronDown, ChevronUp } from "lucide-react";
import type { InlineContact } from "./types";

const inputCls = "rounded-md border border-input bg-background px-2 py-1.5 text-sm";

export function InlineContactDetails({
  data,
  onChange,
  expanded,
  onToggle,
}: {
  data: InlineContact;
  onChange: (updates: Partial<InlineContact>) => void;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div>
      <button
        type="button"
        onClick={onToggle}
        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        {expanded ? "Minder details" : "Meer details (adres, telefoon, KvK)"}
      </button>
      {expanded && (
        <div className="mt-2 space-y-2">
          {/* Phone */}
          <input
            type="tel"
            placeholder="Telefoon"
            value={data.phone}
            onChange={(e) => onChange({ phone: e.target.value })}
            className={inputCls}
          />
          {/* KvK + BTW (only for companies) */}
          {data.contact_type === "company" && (
            <div className="grid gap-2 sm:grid-cols-2">
              <input
                type="text"
                placeholder="KvK-nummer"
                value={data.kvk_number}
                onChange={(e) => onChange({ kvk_number: e.target.value })}
                className={inputCls}
              />
              <input
                type="text"
                placeholder="BTW-nummer"
                value={data.btw_number}
                onChange={(e) => onChange({ btw_number: e.target.value })}
                className={inputCls}
              />
            </div>
          )}
          {/* Visit address */}
          <div>
            <p className="text-xs text-muted-foreground mb-1">Bezoekadres</p>
            <div className="grid gap-2 sm:grid-cols-3">
              <input
                type="text"
                placeholder="Straat + huisnr"
                value={data.visit_address}
                onChange={(e) => onChange({ visit_address: e.target.value })}
                className={`${inputCls} sm:col-span-1`}
              />
              <input
                type="text"
                placeholder="Postcode"
                value={data.visit_postcode}
                onChange={(e) => onChange({ visit_postcode: e.target.value })}
                className={inputCls}
              />
              <input
                type="text"
                placeholder="Plaats"
                value={data.visit_city}
                onChange={(e) => onChange({ visit_city: e.target.value })}
                className={inputCls}
              />
            </div>
          </div>
          {/* Postal address */}
          <div>
            <p className="text-xs text-muted-foreground mb-1">Postadres (optioneel)</p>
            <div className="grid gap-2 sm:grid-cols-3">
              <input
                type="text"
                placeholder="Straat + huisnr"
                value={data.postal_address}
                onChange={(e) => onChange({ postal_address: e.target.value })}
                className={`${inputCls} sm:col-span-1`}
              />
              <input
                type="text"
                placeholder="Postcode"
                value={data.postal_postcode}
                onChange={(e) => onChange({ postal_postcode: e.target.value })}
                className={inputCls}
              />
              <input
                type="text"
                placeholder="Plaats"
                value={data.postal_city}
                onChange={(e) => onChange({ postal_city: e.target.value })}
                className={inputCls}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
