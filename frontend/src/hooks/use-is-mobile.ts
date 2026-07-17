"use client";

import { useEffect, useState } from "react";

// Telefoon = smaller dan Tailwind `md` (768px). Tablet staand en desktop tellen
// als "niet mobiel". Gebruikt door de responsive dialog/drawer-wrapper en de
// onderste navigatiebalk. SSR-veilig: start op false, corrigeert na mount.
const MOBILE_BREAKPOINT = 768;

export function useIsMobile(): boolean {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
    const onChange = () => setIsMobile(mql.matches);
    onChange();
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return isMobile;
}
