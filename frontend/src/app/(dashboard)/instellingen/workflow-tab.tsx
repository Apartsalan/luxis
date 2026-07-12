"use client";

import { Sparkles, ToggleLeft, ToggleRight } from "lucide-react";
import { toast } from "sonner";

import { useTenant, useUpdateTenant } from "@/hooks/use-settings";

export function WorkflowTab() {
  const { data: tenant, isLoading } = useTenant();
  const updateTenant = useUpdateTenant();

  if (isLoading || !tenant) {
    return <div className="h-24 rounded-xl border border-border bg-card p-6 skeleton" />;
  }

  const enabled = tenant.pipeline_auto_drafts_enabled;

  const handleToggle = () => {
    const next = !enabled;
    updateTenant.mutate(
      { pipeline_auto_drafts_enabled: next },
      {
        onSuccess: () =>
          toast.success(
            next
              ? "Automatische concepten ingeschakeld"
              : "Automatische concepten uitgeschakeld"
          ),
        onError: (error) =>
          toast.error(
            error instanceof Error ? error.message : "Bijwerken mislukt"
          ),
      }
    );
  };

  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <h2 className="text-base font-semibold text-foreground">
              Automatische AI-concepten voor incasso-pipeline
            </h2>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Genereer automatisch een conceptbrief zodra een dossier klaar is voor
            een volgende incassostap. De scheduler zet klaar wat beoordeeld kan worden.
          </p>
        </div>
        <button
          onClick={handleToggle}
          disabled={updateTenant.isPending}
          className="mt-0.5 shrink-0 disabled:opacity-50"
          title={enabled ? "Uitschakelen" : "Inschakelen"}
        >
          {enabled ? (
            <ToggleRight className="h-7 w-7 text-primary" />
          ) : (
            <ToggleLeft className="h-7 w-7 text-muted-foreground" />
          )}
        </button>
      </div>
    </div>
  );
}
