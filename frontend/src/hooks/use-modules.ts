"use client";

import { useTenant } from "@/hooks/use-settings";

export type LuxisModule = "incasso" | "tijdschrijven" | "facturatie";

const ALL_MODULES: LuxisModule[] = ["incasso", "tijdschrijven", "facturatie"];

export function useModules() {
  const { data: tenant, isLoading } = useTenant();

  const modules = tenant?.modules_enabled ?? [];

  function hasModule(mod: LuxisModule): boolean {
    return modules.includes(mod);
  }

  function hasAnyModule(...mods: LuxisModule[]): boolean {
    return mods.some((m) => modules.includes(m));
  }

  return {
    modules,
    hasModule,
    hasAnyModule,
    isLoading,
    allModules: ALL_MODULES,
  };
}
