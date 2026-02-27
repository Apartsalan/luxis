"use client";

import { useState, useMemo } from "react";
import {
  Gavel,
  Settings2,
  Workflow,
  Plus,
  Trash2,
  ChevronUp,
  ChevronDown,
  Save,
  X,
  Loader2,
  CheckSquare,
  Square,
  ArrowRight,
  FileText,
  Calculator,
  AlertTriangle,
  Users,
  Clock,
  Filter,
} from "lucide-react";
import { toast } from "sonner";
import {
  useIncassoPipelineSteps,
  useCreatePipelineStep,
  useUpdatePipelineStep,
  useDeletePipelineStep,
  useSeedPipelineSteps,
  useIncassoPipeline,
  useBatchPreview,
  useBatchExecute,
  useIncassoQueueCounts,
  type PipelineStep,
  type CaseInPipeline,
  type DeadlineStatus,
} from "@/hooks/use-incasso";
import {
  useDocxTemplates,
  getTemplateLabel,
} from "@/hooks/use-documents";
import {
  useManagedTemplates,
  getTemplateKeyLabel,
} from "@/hooks/use-managed-templates";

// ── Tabs ─────────────────────────────────────────────────────────────────

const TABS = [
  { id: "werkstroom", label: "Werkstroom", icon: Workflow },
  { id: "stappen", label: "Stappen beheren", icon: Settings2 },
] as const;

type TabId = (typeof TABS)[number]["id"];

// ── Queue filter types ──────────────────────────────────────────────────

type QueueFilter = "all" | "ready_next_step" | "wik_expired" | "action_required";

// ── Main Page ────────────────────────────────────────────────────────────

export default function IncassoPage() {
  const [activeTab, setActiveTab] = useState<TabId>("werkstroom");

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Gavel className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-foreground">Incasso</h1>
            <p className="text-sm text-muted-foreground">
              Batch-werkstroom voor incassodossiers
            </p>
          </div>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-border">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "werkstroom" && <WerkstroomTab />}
      {activeTab === "stappen" && <StappenTab />}
    </div>
  );
}

// ── Pipeline Editor (Stappen beheren) ────────────────────────────────────

function StappenTab() {
  const { data: steps, isLoading } = useIncassoPipelineSteps(false);
  const createStep = useCreatePipelineStep();
  const updateStep = useUpdatePipelineStep();
  const deleteStep = useDeletePipelineStep();
  const seedSteps = useSeedPipelineSteps();
  const { data: managedTemplates } = useManagedTemplates();

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ name: "", min_wait_days: 0, max_wait_days: 0, template_type: "" });
  const [showAddForm, setShowAddForm] = useState(false);
  const [newStep, setNewStep] = useState({ name: "", min_wait_days: 0, max_wait_days: 0, template_type: "" });

  const activeSteps = useMemo(
    () => (steps ?? []).filter((s) => s.is_active).sort((a, b) => a.sort_order - b.sort_order),
    [steps]
  );

  // Dynamic template options from managed templates (deduplicated by template_key)
  const templateTypeOptions = useMemo(() => {
    const seen = new Set<string>();
    return (managedTemplates ?? [])
      .filter((t) => {
        if (seen.has(t.template_key)) return false;
        seen.add(t.template_key);
        return true;
      })
      .map((t) => ({ value: t.template_key, label: getTemplateKeyLabel(t.template_key) }));
  }, [managedTemplates]);

  const handleSeed = () => {
    seedSteps.mutate(undefined, {
      onSuccess: () => toast.success("Standaard incassostappen aangemaakt"),
      onError: (err) => toast.error(err.message),
    });
  };

  const handleAdd = () => {
    if (!newStep.name.trim()) return;
    const maxOrder = activeSteps.length > 0 ? Math.max(...activeSteps.map((s) => s.sort_order)) : 0;
    createStep.mutate(
      {
        name: newStep.name.trim(),
        sort_order: maxOrder + 1,
        min_wait_days: newStep.min_wait_days,
        max_wait_days: newStep.max_wait_days,
        template_type: newStep.template_type || null,
      },
      {
        onSuccess: () => {
          toast.success("Stap toegevoegd");
          setNewStep({ name: "", min_wait_days: 0, max_wait_days: 0, template_type: "" });
          setShowAddForm(false);
        },
        onError: (err) => toast.error(err.message),
      }
    );
  };

  const handleDelete = (step: PipelineStep) => {
    if (!confirm(`Weet je zeker dat je "${step.name}" wilt verwijderen?`)) return;
    deleteStep.mutate(step.id, {
      onSuccess: () => toast.success(`"${step.name}" verwijderd`),
      onError: (err) => toast.error(err.message),
    });
  };

  const handleMoveUp = (step: PipelineStep, index: number) => {
    if (index === 0) return;
    const prev = activeSteps[index - 1];
    updateStep.mutate({ id: step.id, sort_order: prev.sort_order });
    updateStep.mutate({ id: prev.id, sort_order: step.sort_order });
  };

  const handleMoveDown = (step: PipelineStep, index: number) => {
    if (index === activeSteps.length - 1) return;
    const next = activeSteps[index + 1];
    updateStep.mutate({ id: step.id, sort_order: next.sort_order });
    updateStep.mutate({ id: next.id, sort_order: step.sort_order });
  };

  const handleStartEdit = (step: PipelineStep) => {
    setEditingId(step.id);
    setEditForm({
      name: step.name,
      min_wait_days: step.min_wait_days,
      max_wait_days: step.max_wait_days,
      template_type: step.template_type || "",
    });
  };

  const handleSaveEdit = (step: PipelineStep) => {
    updateStep.mutate(
      {
        id: step.id,
        name: editForm.name.trim(),
        min_wait_days: editForm.min_wait_days,
        max_wait_days: editForm.max_wait_days,
        template_type: editForm.template_type || null,
      },
      {
        onSuccess: () => {
          toast.success("Stap bijgewerkt");
          setEditingId(null);
        },
        onError: (err) => toast.error(err.message),
      }
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!steps || activeSteps.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-muted/30 p-12 text-center">
        <Settings2 className="mx-auto h-10 w-10 text-muted-foreground/50" />
        <h3 className="mt-4 text-base font-semibold text-foreground">
          Geen incassostappen geconfigureerd
        </h3>
        <p className="mt-1.5 text-sm text-muted-foreground">
          Maak standaard incassostappen aan om de pipeline te gebruiken.
        </p>
        <button
          onClick={handleSeed}
          disabled={seedSteps.isPending}
          className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {seedSteps.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Plus className="h-4 w-4" />
          )}
          Standaardstappen aanmaken
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Configureer de stappen in het incassoproces. De volgorde bepaalt de workflow.
        </p>
        <button
          onClick={() => setShowAddForm(true)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Stap toevoegen
        </button>
      </div>

      {/* Steps list */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/50">
              <th className="w-10 px-3 py-2.5 text-left text-xs font-medium text-muted-foreground uppercase">#</th>
              <th className="px-3 py-2.5 text-left text-xs font-medium text-muted-foreground uppercase">Naam</th>
              <th className="w-24 px-3 py-2.5 text-left text-xs font-medium text-muted-foreground uppercase">Min. dagen</th>
              <th className="w-24 px-3 py-2.5 text-left text-xs font-medium text-muted-foreground uppercase" title="Grens voor rode status (te laat)">Grens rood</th>
              <th className="w-48 px-3 py-2.5 text-left text-xs font-medium text-muted-foreground uppercase">Briefsjabloon</th>
              <th className="w-32 px-3 py-2.5 text-right text-xs font-medium text-muted-foreground uppercase">Acties</th>
            </tr>
          </thead>
          <tbody>
            {activeSteps.map((step, i) => (
              <tr key={step.id} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                <td className="px-3 py-2.5 text-muted-foreground">{i + 1}</td>
                <td className="px-3 py-2.5">
                  {editingId === step.id ? (
                    <input
                      type="text"
                      value={editForm.name}
                      onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
                      className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20"
                      autoFocus
                    />
                  ) : (
                    <span
                      className="cursor-pointer hover:text-primary transition-colors"
                      onClick={() => handleStartEdit(step)}
                    >
                      {step.name}
                    </span>
                  )}
                </td>
                <td className="px-3 py-2.5">
                  {editingId === step.id ? (
                    <input
                      type="number"
                      min={0}
                      value={editForm.min_wait_days}
                      onChange={(e) => setEditForm((f) => ({ ...f, min_wait_days: parseInt(e.target.value) || 0 }))}
                      className="w-20 rounded-md border border-input bg-background px-2 py-1 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20"
                    />
                  ) : (
                    <span className="text-muted-foreground">
                      {step.min_wait_days > 0 ? `${step.min_wait_days}d` : "—"}
                    </span>
                  )}
                </td>
                <td className="px-3 py-2.5">
                  {editingId === step.id ? (
                    <input
                      type="number"
                      min={0}
                      value={editForm.max_wait_days}
                      onChange={(e) => setEditForm((f) => ({ ...f, max_wait_days: parseInt(e.target.value) || 0 }))}
                      className="w-20 rounded-md border border-input bg-background px-2 py-1 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20"
                    />
                  ) : (
                    <span className="text-muted-foreground">
                      {step.max_wait_days > 0 ? `${step.max_wait_days}d` : "—"}
                    </span>
                  )}
                </td>
                <td className="px-3 py-2.5">
                  {editingId === step.id ? (
                    <select
                      value={editForm.template_type}
                      onChange={(e) => setEditForm((f) => ({ ...f, template_type: e.target.value }))}
                      className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20"
                    >
                      <option value="">Geen</option>
                      {templateTypeOptions.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <span className="text-muted-foreground">
                      {step.template_type ? (
                        <span className="inline-flex items-center gap-1">
                          <FileText className="h-3.5 w-3.5" />
                          {getTemplateLabel(step.template_type)}
                        </span>
                      ) : (
                        "—"
                      )}
                    </span>
                  )}
                </td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center justify-end gap-1">
                    {editingId === step.id ? (
                      <>
                        <button
                          onClick={() => handleSaveEdit(step)}
                          className="rounded-md p-1.5 text-primary hover:bg-primary/10 transition-colors"
                          title="Opslaan"
                        >
                          <Save className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          className="rounded-md p-1.5 text-muted-foreground hover:bg-muted transition-colors"
                          title="Annuleren"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() => handleMoveUp(step, i)}
                          disabled={i === 0}
                          className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors disabled:opacity-30"
                          title="Omhoog"
                        >
                          <ChevronUp className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleMoveDown(step, i)}
                          disabled={i === activeSteps.length - 1}
                          className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors disabled:opacity-30"
                          title="Omlaag"
                        >
                          <ChevronDown className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(step)}
                          className="rounded-md p-1.5 text-muted-foreground hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 transition-colors"
                          title="Verwijderen"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}

            {/* Add step row */}
            {showAddForm && (
              <tr className="border-b border-border bg-primary/5">
                <td className="px-3 py-2.5 text-muted-foreground">
                  {activeSteps.length + 1}
                </td>
                <td className="px-3 py-2.5">
                  <input
                    type="text"
                    placeholder="Naam van de stap..."
                    value={newStep.name}
                    onChange={(e) => setNewStep((f) => ({ ...f, name: e.target.value }))}
                    className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20"
                    autoFocus
                    onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                  />
                </td>
                <td className="px-3 py-2.5">
                  <input
                    type="number"
                    min={0}
                    value={newStep.min_wait_days}
                    onChange={(e) => setNewStep((f) => ({ ...f, min_wait_days: parseInt(e.target.value) || 0 }))}
                    className="w-20 rounded-md border border-input bg-background px-2 py-1 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20"
                  />
                </td>
                <td className="px-3 py-2.5">
                  <input
                    type="number"
                    min={0}
                    value={newStep.max_wait_days}
                    onChange={(e) => setNewStep((f) => ({ ...f, max_wait_days: parseInt(e.target.value) || 0 }))}
                    className="w-20 rounded-md border border-input bg-background px-2 py-1 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20"
                  />
                </td>
                <td className="px-3 py-2.5">
                  <select
                    value={newStep.template_type}
                    onChange={(e) => setNewStep((f) => ({ ...f, template_type: e.target.value }))}
                    className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20"
                  >
                    <option value="">Geen</option>
                    {templateTypeOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={handleAdd}
                      disabled={!newStep.name.trim() || createStep.isPending}
                      className="rounded-md p-1.5 text-primary hover:bg-primary/10 transition-colors disabled:opacity-30"
                      title="Toevoegen"
                    >
                      {createStep.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Save className="h-4 w-4" />
                      )}
                    </button>
                    <button
                      onClick={() => {
                        setShowAddForm(false);
                        setNewStep({ name: "", min_wait_days: 0, max_wait_days: 0, template_type: "" });
                      }}
                      className="rounded-md p-1.5 text-muted-foreground hover:bg-muted transition-colors"
                      title="Annuleren"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Werkstroom Tab (main batch view) ─────────────────────────────────────

function WerkstroomTab() {
  const { data: pipeline, isLoading } = useIncassoPipeline();
  const { data: steps } = useIncassoPipelineSteps();
  const { data: queueCounts } = useIncassoQueueCounts();
  const batchPreview = useBatchPreview();
  const batchExecute = useBatchExecute();

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showPreview, setShowPreview] = useState(false);
  const [batchAction, setBatchAction] = useState<string | null>(null);
  const [targetStepId, setTargetStepId] = useState<string | null>(null);
  const [queueFilter, setQueueFilter] = useState<QueueFilter>("all");

  const allCases = useMemo(() => {
    if (!pipeline) return [];
    const cases: CaseInPipeline[] = [];
    for (const col of pipeline.columns) {
      cases.push(...col.cases);
    }
    cases.push(...pipeline.unassigned);
    return cases;
  }, [pipeline]);

  // Build a step lookup for queue filtering
  const stepLookup = useMemo(() => {
    if (!steps) return new Map<string, PipelineStep>();
    return new Map(steps.map((s) => [s.id, s]));
  }, [steps]);

  // Next-step lookup: step_id -> next step
  const nextStepMap = useMemo(() => {
    if (!steps) return new Map<string, PipelineStep>();
    const sorted = [...steps].sort((a, b) => a.sort_order - b.sort_order);
    const map = new Map<string, PipelineStep>();
    for (let i = 0; i < sorted.length - 1; i++) {
      map.set(sorted[i].id, sorted[i + 1]);
    }
    return map;
  }, [steps]);

  // First step id for WIK filter
  const firstStepId = useMemo(() => {
    if (!steps || steps.length === 0) return null;
    const sorted = [...steps].sort((a, b) => a.sort_order - b.sort_order);
    return sorted[0].id;
  }, [steps]);

  // Filter cases based on queue selection
  const filterCase = (c: CaseInPipeline): boolean => {
    if (queueFilter === "all") return true;
    if (queueFilter === "action_required") {
      if (!c.incasso_step_id) return true; // unassigned
      const nextStep = nextStepMap.get(c.incasso_step_id);
      if (nextStep && c.days_in_step >= nextStep.min_wait_days) return true;
      return false;
    }
    if (queueFilter === "ready_next_step") {
      if (!c.incasso_step_id) return false;
      const nextStep = nextStepMap.get(c.incasso_step_id);
      return !!nextStep && c.days_in_step >= nextStep.min_wait_days;
    }
    if (queueFilter === "wik_expired") {
      return c.incasso_step_id === firstStepId && c.days_in_step >= 14;
    }
    return true;
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAllInStep = (stepCases: CaseInPipeline[]) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      const allSelected = stepCases.every((c) => next.has(c.id));
      if (allSelected) {
        stepCases.forEach((c) => next.delete(c.id));
      } else {
        stepCases.forEach((c) => next.add(c.id));
      }
      return next;
    });
  };

  const handleBatchAction = (action: string) => {
    setBatchAction(action);
    if (action === "advance_step" && steps && steps.length > 0) {
      setTargetStepId(steps[0].id);
    }
    setShowPreview(true);

    batchPreview.mutate(
      {
        case_ids: Array.from(selectedIds),
        action,
        target_step_id: action === "advance_step" && steps ? steps[0].id : undefined,
      },
      {
        onError: (err) => toast.error(err.message),
      }
    );
  };

  const handleExecuteBatch = () => {
    if (!batchAction) return;
    batchExecute.mutate(
      {
        case_ids: Array.from(selectedIds),
        action: batchAction,
        target_step_id: targetStepId || null,
        auto_assign_step: true,
      },
      {
        onSuccess: (result) => {
          const parts: string[] = [`${result.processed} dossier(s) verwerkt`];
          if (result.skipped > 0) parts.push(`${result.skipped} overgeslagen`);
          const docCount = result.generated_document_ids?.length ?? 0;
          if (docCount > 0) parts.push(`${docCount} brief/brieven gegenereerd`);
          if (result.tasks_auto_completed > 0)
            parts.push(`${result.tasks_auto_completed} taak/taken afgerond`);
          if (result.cases_auto_advanced > 0)
            parts.push(`${result.cases_auto_advanced} dossier(s) doorgeschoven`);
          toast.success(parts.join(", "));
          setShowPreview(false);
          setSelectedIds(new Set());
          setBatchAction(null);
        },
        onError: (err) => toast.error(err.message),
      }
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!pipeline || pipeline.total_cases === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-muted/30 p-12 text-center">
        <Gavel className="mx-auto h-10 w-10 text-muted-foreground/50" />
        <h3 className="mt-4 text-base font-semibold text-foreground">
          Geen incassodossiers
        </h3>
        <p className="mt-1.5 text-sm text-muted-foreground">
          Maak een dossier aan met type &quot;Incasso&quot; om de werkstroom te gebruiken.
        </p>
      </div>
    );
  }

  // Queue filter tabs
  const queueTabs: { id: QueueFilter; label: string; count: number; icon: typeof Filter }[] = [
    { id: "all", label: "Alle dossiers", count: pipeline.total_cases, icon: Workflow },
    { id: "ready_next_step", label: "Klaar voor volgende stap", count: queueCounts?.ready_next_step ?? 0, icon: ArrowRight },
    { id: "wik_expired", label: "14d verlopen", count: queueCounts?.wik_expired ?? 0, icon: Clock },
    { id: "action_required", label: "Actie vereist", count: queueCounts?.action_required ?? 0, icon: AlertTriangle },
  ];

  return (
    <div className="space-y-4">
      {/* Summary bar + queue filters */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 flex-wrap">
          {queueTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setQueueFilter(tab.id);
                setSelectedIds(new Set());
              }}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                queueFilter === tab.id
                  ? "bg-primary text-primary-foreground"
                  : "border border-border hover:bg-muted"
              }`}
            >
              <tab.icon className="h-3.5 w-3.5" />
              {tab.label}
              {tab.count > 0 && (
                <span className={`ml-0.5 flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-[10px] font-semibold ${
                  queueFilter === tab.id
                    ? "bg-primary-foreground/20 text-primary-foreground"
                    : tab.id === "action_required" && tab.count > 0
                      ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                      : "bg-muted text-muted-foreground"
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Pipeline columns */}
      {pipeline.columns.map((col) => {
        const filteredCases = col.cases.filter(filterCase);
        if (queueFilter !== "all" && filteredCases.length === 0) return null;

        return (
          <PipelineColumnView
            key={col.step.id}
            column={{ ...col, cases: filteredCases, count: filteredCases.length }}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelect}
            onSelectAll={() => selectAllInStep(filteredCases)}
          />
        );
      })}

      {/* Unassigned cases */}
      {pipeline.unassigned.length > 0 && (queueFilter === "all" || queueFilter === "action_required") && (
        <PipelineColumnView
          column={{
            step: {
              id: "unassigned", name: "Zonder stap", sort_order: 999, min_wait_days: 0, max_wait_days: 0,
              template_id: null, template_type: null, template_name: null,
              is_active: true, created_at: "", updated_at: "",
            },
            cases: pipeline.unassigned,
            count: pipeline.unassigned.length,
          }}
          selectedIds={selectedIds}
          onToggleSelect={toggleSelect}
          onSelectAll={() => selectAllInStep(pipeline.unassigned)}
          isUnassigned
        />
      )}

      {/* Floating action bar */}
      {selectedIds.size > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 rounded-xl border border-border bg-card px-5 py-3 shadow-xl">
          <span className="text-sm font-medium text-foreground">
            {selectedIds.size} geselecteerd
          </span>
          <div className="h-5 w-px bg-border" />
          <button
            onClick={() => handleBatchAction("advance_step")}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <ArrowRight className="h-3.5 w-3.5" />
            Wijzig stap
          </button>
          <button
            onClick={() => handleBatchAction("generate_document")}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors"
          >
            <FileText className="h-3.5 w-3.5" />
            Verstuur brief
          </button>
          <button
            onClick={() => handleBatchAction("recalculate_interest")}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm font-medium hover:bg-muted transition-colors"
          >
            <Calculator className="h-3.5 w-3.5" />
            Herbereken rente
          </button>
          <button
            onClick={() => setSelectedIds(new Set())}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Pre-flight wizard dialog */}
      {showPreview && (
        <PreFlightDialog
          action={batchAction || ""}
          preview={batchPreview.data}
          isLoading={batchPreview.isPending}
          isExecuting={batchExecute.isPending}
          steps={steps ?? []}
          targetStepId={targetStepId}
          onTargetStepChange={setTargetStepId}
          onConfirm={handleExecuteBatch}
          onClose={() => {
            setShowPreview(false);
            setBatchAction(null);
          }}
        />
      )}
    </div>
  );
}

// ── Pipeline Column Component ────────────────────────────────────────────

function PipelineColumnView({
  column,
  selectedIds,
  onToggleSelect,
  onSelectAll,
  isUnassigned = false,
}: {
  column: { step: PipelineStep; cases: CaseInPipeline[]; count: number };
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onSelectAll: () => void;
  isUnassigned?: boolean;
}) {
  const allSelected = column.cases.length > 0 && column.cases.every((c) => selectedIds.has(c.id));

  if (column.cases.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-foreground">{column.step.name}</h3>
            <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-muted px-1.5 text-[10px] font-semibold text-muted-foreground">
              0
            </span>
          </div>
        </div>
        <div className="px-4 py-6 text-center text-sm text-muted-foreground">
          Geen dossiers in deze stap
        </div>
      </div>
    );
  }

  return (
    <div className={`rounded-xl border bg-card ${isUnassigned ? "border-amber-300 dark:border-amber-700" : "border-border"}`}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          {isUnassigned && <AlertTriangle className="h-4 w-4 text-amber-500" />}
          <h3 className="text-sm font-semibold text-foreground">{column.step.name}</h3>
          <span className={`flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-[10px] font-semibold ${isUnassigned ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400" : "bg-primary/10 text-primary"}`}>
            {column.count}
          </span>
          {column.step.min_wait_days > 0 && (
            <span className="text-xs text-muted-foreground">
              (min. {column.step.min_wait_days} dagen)
            </span>
          )}
          {column.step.template_type && (
            <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
              <FileText className="h-3 w-3" />
              {getTemplateLabel(column.step.template_type)}
            </span>
          )}
        </div>
        <button
          onClick={onSelectAll}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          {allSelected ? "Deselecteer alles" : "Selecteer alles"}
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/30">
              <th className="w-10 px-3 py-2 text-left">
                <button onClick={onSelectAll}>
                  {allSelected ? (
                    <CheckSquare className="h-4 w-4 text-primary" />
                  ) : (
                    <Square className="h-4 w-4 text-muted-foreground" />
                  )}
                </button>
              </th>
              <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Dossiernr.</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Cli&euml;nt</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Wederpartij</th>
              <th className="px-3 py-2 text-right text-xs font-medium text-muted-foreground">Hoofdsom</th>
              <th className="px-3 py-2 text-right text-xs font-medium text-muted-foreground">Openstaand</th>
              <th className="px-3 py-2 text-right text-xs font-medium text-muted-foreground">Dagen</th>
            </tr>
          </thead>
          <tbody>
            {column.cases.map((c) => {
              const isSelected = selectedIds.has(c.id);
              return (
                <tr
                  key={c.id}
                  className={`border-b border-border last:border-0 cursor-pointer transition-colors ${
                    isSelected ? "bg-primary/5" : "hover:bg-muted/30"
                  }`}
                  onClick={() => onToggleSelect(c.id)}
                >
                  <td className="px-3 py-2">
                    {isSelected ? (
                      <CheckSquare className="h-4 w-4 text-primary" />
                    ) : (
                      <Square className="h-4 w-4 text-muted-foreground" />
                    )}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs">
                    <span className="inline-flex items-center gap-1.5">
                      <span
                        className={`inline-block h-2 w-2 rounded-full shrink-0 ${DEADLINE_STYLES[c.deadline_status as DeadlineStatus]?.dot ?? DEADLINE_STYLES.gray.dot}`}
                        title={DEADLINE_STYLES[c.deadline_status as DeadlineStatus]?.label ?? ""}
                      />
                      {c.case_number}
                    </span>
                  </td>
                  <td className="px-3 py-2">{c.client_name}</td>
                  <td className="px-3 py-2 text-muted-foreground">{c.opposing_party_name || "—"}</td>
                  <td className="px-3 py-2 text-right font-mono">
                    {formatCurrency(c.total_principal)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    <span className={c.outstanding > 0 ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"}>
                      {formatCurrency(c.outstanding)}
                    </span>
                  </td>
                  <td className={`px-3 py-2 text-right font-medium ${DEADLINE_STYLES[c.deadline_status as DeadlineStatus]?.text ?? "text-muted-foreground"}`}>
                    {c.days_in_step}d
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Pre-flight Dialog ────────────────────────────────────────────────────

function PreFlightDialog({
  action,
  preview,
  isLoading,
  isExecuting,
  steps,
  targetStepId,
  onTargetStepChange,
  onConfirm,
  onClose,
}: {
  action: string;
  preview: ReturnType<typeof useBatchPreview>["data"];
  isLoading: boolean;
  isExecuting: boolean;
  steps: PipelineStep[];
  targetStepId: string | null;
  onTargetStepChange: (id: string) => void;
  onConfirm: () => void;
  onClose: () => void;
}) {
  const actionLabels: Record<string, string> = {
    advance_step: "Stap wijzigen",
    generate_document: "Brief genereren",
    recalculate_interest: "Rente herberekenen",
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-foreground">
            {actionLabels[action] || action}
          </h2>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">Controle uitvoeren...</span>
          </div>
        ) : preview ? (
          <div className="space-y-4">
            {/* Summary */}
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-lg bg-muted/50 p-3 text-center">
                <div className="text-lg font-bold text-foreground">{preview.total_selected}</div>
                <div className="text-xs text-muted-foreground">Geselecteerd</div>
              </div>
              <div className="rounded-lg bg-emerald-50 dark:bg-emerald-900/20 p-3 text-center">
                <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400">{preview.ready}</div>
                <div className="text-xs text-muted-foreground">Gereed</div>
              </div>
              <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-3 text-center">
                <div className="text-lg font-bold text-red-600 dark:text-red-400">{preview.blocked.length}</div>
                <div className="text-xs text-muted-foreground">Geblokkeerd</div>
              </div>
            </div>

            {/* Target step selector for advance_step */}
            {action === "advance_step" && (
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Verplaats naar stap
                </label>
                <select
                  value={targetStepId || ""}
                  onChange={(e) => onTargetStepChange(e.target.value)}
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                >
                  {steps.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Info for generate_document */}
            {action === "generate_document" && preview.ready > 0 && (
              <div className="rounded-lg border border-primary/20 bg-primary/5 p-3">
                <p className="text-sm text-foreground flex items-center gap-1.5">
                  <FileText className="h-4 w-4 text-primary" />
                  {preview.ready} brief/brieven worden gegenereerd op basis van het briefsjabloon per stap.
                </p>
              </div>
            )}

            {/* Blockers */}
            {preview.blocked.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-red-600 dark:text-red-400 mb-2 flex items-center gap-1.5">
                  <AlertTriangle className="h-4 w-4" />
                  Geblokkeerde dossiers
                </h3>
                <div className="max-h-32 overflow-y-auto rounded-lg border border-red-200 dark:border-red-800">
                  {preview.blocked.map((b) => (
                    <div key={b.case_id} className="flex items-center justify-between px-3 py-1.5 text-sm border-b border-red-100 dark:border-red-900 last:border-0">
                      <span className="font-mono text-xs">{b.case_number}</span>
                      <span className="text-xs text-red-600 dark:text-red-400">{b.reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Needs step assignment (only show for non-advance_step actions) */}
            {action !== "advance_step" && preview.needs_step_assignment.length > 0 && (
              <div className="rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-900/10 p-3">
                <p className="text-sm text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
                  <Users className="h-4 w-4" />
                  {preview.needs_step_assignment.length} dossier(s) zonder stap — wijs eerst een stap toe.
                </p>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground py-4">
            Kon de preview niet laden.
          </p>
        )}

        {/* Actions */}
        <div className="mt-6 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
          >
            Annuleren
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading || isExecuting || !preview || preview.ready === 0}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {isExecuting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : null}
            Uitvoeren ({preview?.ready ?? 0} dossiers)
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────

const DEADLINE_STYLES: Record<DeadlineStatus, { dot: string; text: string; label: string }> = {
  green:  { dot: "bg-emerald-500", text: "text-emerald-600 dark:text-emerald-400", label: "Wachtperiode" },
  orange: { dot: "bg-amber-500",   text: "text-amber-600 dark:text-amber-400",     label: "Klaar voor actie" },
  red:    { dot: "bg-red-500",     text: "text-red-600 dark:text-red-400",         label: "Te laat" },
  gray:   { dot: "bg-gray-400",    text: "text-muted-foreground",                  label: "Geen stap" },
};

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("nl-NL", {
    style: "currency",
    currency: "EUR",
  }).format(amount);
}
