"use client";

import { createContext, useContext, useState, useCallback, useEffect } from "react";
import type { BreadcrumbOverride } from "@/components/layout/breadcrumbs";

interface BreadcrumbContextValue {
  overrides: BreadcrumbOverride[];
  setOverrides: (overrides: BreadcrumbOverride[]) => void;
}

const BreadcrumbContext = createContext<BreadcrumbContextValue>({
  overrides: [],
  setOverrides: () => {},
});

export function BreadcrumbProvider({ children }: { children: React.ReactNode }) {
  const [overrides, setOverrides] = useState<BreadcrumbOverride[]>([]);
  return (
    <BreadcrumbContext.Provider value={{ overrides, setOverrides }}>
      {children}
    </BreadcrumbContext.Provider>
  );
}

export function useBreadcrumbContext() {
  return useContext(BreadcrumbContext);
}

/**
 * Hook for detail pages to set breadcrumb labels for dynamic segments.
 * Example: useBreadcrumbs([{ segment: "abc-123", label: "Z-2026-0001" }])
 */
export function useBreadcrumbs(overrides: BreadcrumbOverride[]) {
  const { setOverrides } = useBreadcrumbContext();

  useEffect(() => {
    if (overrides.length > 0) {
      setOverrides(overrides);
    }
    return () => setOverrides([]);
  }, [JSON.stringify(overrides), setOverrides]);
}
