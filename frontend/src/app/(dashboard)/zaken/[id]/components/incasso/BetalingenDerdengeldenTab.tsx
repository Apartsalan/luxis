"use client";

import { BetalingenTab } from "./BetalingenTab";
import { BetalingsregelingSection } from "./BetalingsregelingSection";
import { DerdengeldenTab } from "./DerdengeldenTab";

export function BetalingenDerdengeldenTab({ caseId }: { caseId: string }) {
  return (
    <div className="space-y-8">
      <BetalingenTab caseId={caseId} />
      <div className="border-t border-border" />
      <BetalingsregelingSection caseId={caseId} />
      <div className="border-t border-border" />
      <DerdengeldenTab caseId={caseId} />
    </div>
  );
}
