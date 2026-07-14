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
 * De historie-check gebruikt `history.state.idx` die Next.js' App Router bijhoudt
 * voor scroll-restauratie: 0 = eerste pagina in deze tab-sessie, >0 = er is een
 * vorige pagina om naar terug te keren.
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
    const idx =
      typeof window !== "undefined"
        ? (window.history.state as { idx?: number } | null)?.idx ?? 0
        : 0;
    if (idx > 0) {
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
