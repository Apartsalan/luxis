"use client";

import { VorderingenTab } from "./VorderingenTab";
import { FinancieelTab } from "./FinancieelTab";
import { ProvisieSettingsSection } from "./ProvisieSettingsSection";

export function VorderingenFinancieelTab({ caseId }: { caseId: string }) {
  return (
    <div className="space-y-8">
      <VorderingenTab caseId={caseId} />
      <div className="border-t border-border" />
      <FinancieelTab caseId={caseId} />
      <div className="border-t border-border" />
      <ProvisieSettingsSection caseId={caseId} />
    </div>
  );
}
