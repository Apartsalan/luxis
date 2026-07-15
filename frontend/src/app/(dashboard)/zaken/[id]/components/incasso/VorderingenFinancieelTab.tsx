"use client";

import { VorderingenTab } from "./VorderingenTab";
import { FinancieelTab } from "./FinancieelTab";

// S216: ProvisieSettingsSection is verhuisd naar het Facturen-tabblad (hoort bij
// cliëntfacturatie, niet bij de debiteur-vorderingen).
export function VorderingenFinancieelTab({ caseId }: { caseId: string }) {
  return (
    <div className="space-y-8">
      <VorderingenTab caseId={caseId} />
      <div className="border-t border-border" />
      <FinancieelTab caseId={caseId} />
    </div>
  );
}
