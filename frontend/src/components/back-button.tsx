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
 * De historie-check vergelijkt `window.history.length` met het ijkpunt dat de
 * dashboard-omhulling bij binnenkomst in de tab vastlegt
 * (`luxis_entry_history_len`): is de lengte sindsdien gegroeid, dan is er in de app
 * genavigeerd → ga echt terug; staat hij nog op het ijkpunt, dan is dit een direct
 * bezochte/verse URL → val terug op de vaste ouder (breekt niet). Next.js' App
 * Router bewaart geen bruikbare index in `history.state`, en kale `history.length`
 * is onbetrouwbaar (een verse tab kan al op 2 staan), vandaar het ijkpunt.
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
    if (typeof window === "undefined") {
      router.push(fallbackHref);
      return;
    }
    const base = Number(
      sessionStorage.getItem("luxis_entry_history_len") ?? window.history.length,
    );
    if (window.history.length > base) {
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
