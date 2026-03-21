"use client";

import { ToggleLeft, ToggleRight } from "lucide-react";
import { toast } from "sonner";
import { useTenant, useUpdateTenant } from "@/hooks/use-settings";
import { useAuth } from "@/hooks/use-auth";

const MODULE_INFO: Record<string, { label: string; description: string }> = {
  incasso: {
    label: "Incasso",
    description:
      "Vorderingen, betalingen, renteberekeningen, WIK-staffel en incassoworkflow",
  },
  tijdschrijven: {
    label: "Tijdschrijven",
    description:
      "Urenregistratie, timer, weekoverzicht en declarabel/niet-declarabel",
  },
  facturatie: {
    label: "Facturatie",
    description:
      "Facturen aanmaken, versturen en bijhouden op basis van uren en kosten",
  },
  wwft: {
    label: "WWFT/KYC",
    description:
      "Cli\u00ebntidentificatie, UBO-registratie, PEP/sanctiecontrole en risicoclassificatie (WWFT-compliance)",
  },
  budget: {
    label: "Budget",
    description:
      "Budgetbeheer per dossier met voortgangsbalk en overschrijdingswaarschuwingen",
  },
};

export function ModulesTab() {
  const { data: tenant, isLoading } = useTenant();
  const updateTenant = useUpdateTenant();
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center justify-between rounded-xl border border-border bg-card p-5">
            <div className="flex items-center gap-4">
              <div className="h-10 w-10 rounded-lg skeleton" />
              <div className="space-y-2">
                <div className="h-4 w-32 rounded skeleton" />
                <div className="h-3 w-48 rounded skeleton" />
              </div>
            </div>
            <div className="h-6 w-11 rounded-full skeleton" />
          </div>
        ))}
      </div>
    );
  }

  const enabledModules = tenant?.modules_enabled ?? [];

  const handleToggle = (moduleKey: string) => {
    if (!isAdmin) return;
    const isEnabled = enabledModules.includes(moduleKey);
    const updated = isEnabled
      ? enabledModules.filter((m) => m !== moduleKey)
      : [...enabledModules, moduleKey];

    updateTenant.mutate(
      { modules_enabled: updated },
      {
        onSuccess: () =>
          toast.success(
            isEnabled
              ? `${MODULE_INFO[moduleKey]?.label} uitgeschakeld`
              : `${MODULE_INFO[moduleKey]?.label} ingeschakeld`
          ),
      }
    );
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold text-foreground mb-2">
          Modules
        </h2>
        <p className="text-sm text-muted-foreground mb-6">
          Schakel modules in of uit voor je kantoor. Uitgeschakelde modules
          worden verborgen in de navigatie en op pagina&apos;s.
        </p>

        <div className="space-y-3">
          {Object.entries(MODULE_INFO).map(([key, info]) => {
            const isEnabled = enabledModules.includes(key);
            return (
              <div
                key={key}
                className={`flex items-center justify-between rounded-lg border p-4 transition-colors ${
                  isEnabled
                    ? "border-primary/20 bg-primary/5"
                    : "border-border bg-background"
                }`}
              >
                <div>
                  <p className="text-sm font-medium text-foreground">
                    {info.label}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {info.description}
                  </p>
                </div>
                <button
                  onClick={() => handleToggle(key)}
                  disabled={!isAdmin || updateTenant.isPending}
                  className="shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
                  title={
                    !isAdmin
                      ? "Alleen admins kunnen modules wijzigen"
                      : isEnabled
                      ? "Uitschakelen"
                      : "Inschakelen"
                  }
                >
                  {isEnabled ? (
                    <ToggleRight className="h-7 w-7 text-primary" />
                  ) : (
                    <ToggleLeft className="h-7 w-7 text-muted-foreground" />
                  )}
                </button>
              </div>
            );
          })}
        </div>

        {!isAdmin && (
          <p className="mt-4 text-xs text-muted-foreground">
            Alleen beheerders kunnen modules in- of uitschakelen.
          </p>
        )}
      </div>
    </div>
  );
}
