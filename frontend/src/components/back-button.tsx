"use client";

import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";

/**
 * Slimme terug-knop: gaat terug naar de pagina van herkomst (router.back), zodat
 * het terug-pijltje werkt zoals in elke normale tool. Is er geen in-app historie
 * (een direct bezochte of ge-bookmarkte URL, of een verse tab), dan valt hij terug
 * op de vaste ouderpagina `fallbackHref` — zo breekt een directe URL nooit.
 *
 * De historie-check gebruikt `window.history.length`: 1 = deze pagina is de enige
 * entry in de tab (direct bezocht/ge-bookmarkt/verse tab) → val terug op de vaste
 * ouder; >1 = er is een vorige pagina → ga daar echt naartoe. (Next.js' App Router
 * bewaart geen bruikbare index in `history.state`, dus die kunnen we niet gebruiken.)
 */
export function BackButton({
  fallbackHref,
  className,
  title = "Terug",
  children,
}: {
  fallbackHref: string;
  className?: string;
  title?: string;
  children?: ReactNode;
}) {
  const router = useRouter();

  const handleBack = () => {
    if (typeof window !== "undefined" && window.history.length > 1) {
      router.back();
    } else {
      router.push(fallbackHref);
    }
  };

  return (
    <button type="button" onClick={handleBack} title={title} className={className}>
      {children ?? <ArrowLeft className="h-5 w-5 text-muted-foreground" />}
    </button>
  );
}
