"use client";

import { useState } from "react";
import { ChevronDown, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

/**
 * S246-nacht — "Verstuur later"-knop met presets, herbruikbaar naast een
 * primaire verzendknop (batch-venster, follow-up-voorvertoning). De browser
 * staat in Nederlandse tijd; toISOString() levert de UTC-tijd die de server
 * bewaart.
 */
export function VerstuurLaterMenu({
  disabled = false,
  onSchedule,
}: {
  disabled?: boolean;
  /** Krijgt het gekozen moment als ISO-string (UTC). */
  onSchedule: (iso: string) => void;
}) {
  const [showCustom, setShowCustom] = useState(false);
  const [customMoment, setCustomMoment] = useState("");
  const [fout, setFout] = useState("");

  const preset = (dagen: number, uur: number) => {
    const d = new Date();
    d.setDate(d.getDate() + dagen);
    d.setHours(uur, 0, 0, 0);
    onSchedule(d.toISOString());
  };

  const custom = () => {
    if (!customMoment) return;
    const d = new Date(customMoment); // datetime-local = lokale (NL) kloktijd
    if (d.getTime() <= Date.now()) {
      setFout("Kies een tijdstip in de toekomst");
      return;
    }
    setShowCustom(false);
    onSchedule(d.toISOString());
  };

  if (showCustom) {
    return (
      <div className="flex items-end gap-2">
        <div className="space-y-1">
          <Input
            type="datetime-local"
            value={customMoment}
            onChange={(e) => { setCustomMoment(e.target.value); setFout(""); }}
            className="h-9"
            aria-label="Verstuur op (Nederlandse tijd)"
          />
          {fout && <p className="text-xs text-destructive">{fout}</p>}
        </div>
        <Button type="button" variant="ghost" size="sm"
                onClick={() => { setShowCustom(false); setCustomMoment(""); setFout(""); }}>
          Terug
        </Button>
        <Button type="button" size="sm" disabled={!customMoment || disabled}
                onClick={custom} className="gap-1.5">
          <Clock className="h-3.5 w-3.5" /> Inplannen
        </Button>
      </div>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button type="button" variant="outline" size="sm" disabled={disabled} className="gap-1.5">
          <Clock className="h-3.5 w-3.5" /> Verstuur later
          <ChevronDown className="h-3 w-3 opacity-60" />
        </Button>
      </DropdownMenuTrigger>
      {/* S247-review: boven élke dialoog waar deze knop in staat — het batch-
          venster tilt zichzelf naar z-[60] (boven de selectie-toolbar) en de
          standaard z-50 van het menu verdween daarachter (presets onzichtbaar). */}
      <DropdownMenuContent align="end" className="z-[70]">
        <DropdownMenuItem onClick={() => preset(1, 9)}>Morgen 09:00</DropdownMenuItem>
        <DropdownMenuItem onClick={() => preset(1, 15)}>Morgen 15:00</DropdownMenuItem>
        <DropdownMenuItem onClick={() => setShowCustom(true)}>Eigen tijdstip…</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
