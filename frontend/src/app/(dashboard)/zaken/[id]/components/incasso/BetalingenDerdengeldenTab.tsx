"use client";

import { ChevronRight } from "lucide-react";
import { useArrangements, useDerdengelden } from "@/hooks/use-collections";
import { BetalingenTab } from "./BetalingenTab";
import { BetalingsregelingSection } from "./BetalingsregelingSection";
import { DerdengeldenTab } from "./DerdengeldenTab";

// S216: lege secties (regeling/derdengelden) worden ingeklapt tot één regel — niet
// onzichtbaar. Eén klik en de volledige sectie klapt open. Derdengelden is bij
// vrijwel elk incassodossier leeg; een betalingsregeling heeft ~1 op de 16 dossiers.
// De hooks hier delen dezelfde React-Query-cache als de secties zelf → geen extra call.
function InklapbaarBijLeeg({
  titel,
  leeg,
  children,
}: {
  titel: string;
  leeg: boolean;
  children: React.ReactNode;
}) {
  if (!leeg) return <>{children}</>;
  return (
    <details className="group">
      <summary className="flex cursor-pointer list-none items-center gap-2 text-sm font-semibold text-card-foreground select-none">
        <ChevronRight className="h-4 w-4 text-muted-foreground transition-transform group-open:rotate-90" />
        {titel}
        <span className="font-normal text-muted-foreground">— geen</span>
      </summary>
      <div className="mt-4">{children}</div>
    </details>
  );
}

export function BetalingenDerdengeldenTab({ caseId }: { caseId: string }) {
  const { data: arrangements } = useArrangements(caseId);
  const { data: derdengelden } = useDerdengelden(caseId);
  const geenRegeling = (arrangements?.length ?? 0) === 0;
  const geenDerdengelden = (derdengelden?.items?.length ?? 0) === 0;

  return (
    <div className="space-y-8">
      <BetalingenTab caseId={caseId} />
      <div className="border-t border-border" />
      <InklapbaarBijLeeg titel="Betalingsregeling" leeg={geenRegeling}>
        <BetalingsregelingSection caseId={caseId} />
      </InklapbaarBijLeeg>
      <div className="border-t border-border" />
      <InklapbaarBijLeeg titel="Derdengelden" leeg={geenDerdengelden}>
        <DerdengeldenTab caseId={caseId} />
      </InklapbaarBijLeeg>
    </div>
  );
}
