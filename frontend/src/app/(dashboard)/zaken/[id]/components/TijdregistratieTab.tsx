"use client";

import { useState } from "react";
import {
  CheckCircle2,
  ChevronRight,
  Clock,
  Loader2,
  Plus,
} from "lucide-react";
import { toast } from "sonner";
import {
  useWorkflowTasks,
  useCompleteTask,
  useSkipTask,
  useCreateTask,
  TASK_TYPE_LABELS,
  TASK_STATUS_LABELS,
  RECURRENCE_LABELS,
} from "@/hooks/use-workflow";
import { useAuth } from "@/hooks/use-auth";
import { formatDateShort } from "@/lib/utils";
import { TASK_STATUS_BADGE } from "../types";

export default function TijdregistratieTab({ caseId }: { caseId: string }) {
  const { user } = useAuth();
  const { data: tasksData, isLoading } = useWorkflowTasks({ case_id: caseId });
  const completeTask = useCompleteTask();
  const skipTask = useSkipTask();
  const createTask = useCreateTask();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    title: "",
    task_type: "custom",
    due_date: new Date().toISOString().split("T")[0],
    description: "",
    recurrence: "none",
    recurrence_end_date: "",
  });

  const handleComplete = async (taskId: string) => {
    try {
      await completeTask.mutateAsync(taskId);
      toast.success("Taak afgerond");
    } catch {}
  };

  const handleSkip = async (taskId: string) => {
    try {
      await skipTask.mutateAsync(taskId);
      toast.success("Taak overgeslagen");
    } catch {}
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createTask.mutateAsync({
        case_id: caseId,
        task_type: form.task_type,
        title: form.title,
        due_date: form.due_date,
        ...(form.description && { description: form.description }),
        ...(user?.id && { assigned_to_id: user.id }),
        ...(form.recurrence !== "none" && { recurrence: form.recurrence }),
        ...(form.recurrence !== "none" && form.recurrence_end_date && { recurrence_end_date: form.recurrence_end_date }),
      });
      toast.success("Taak aangemaakt");
      setShowForm(false);
      setForm({
        title: "",
        task_type: "custom",
        due_date: new Date().toISOString().split("T")[0],
        description: "",
        recurrence: "none",
        recurrence_end_date: "",
      });
    } catch {}
  };

  const tasks = tasksData ?? [];
  const openTasks = tasks.filter(
    (t) => t.status === "pending" || t.status === "due" || t.status === "overdue"
  );
  const completedTasks = tasks.filter(
    (t) => t.status === "completed" || t.status === "skipped"
  );

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-foreground">Taken</h2>
          <p className="text-sm text-muted-foreground">
            {openTasks.length} openstaand
            {completedTasks.length > 0 &&
              ` · ${completedTasks.length} afgerond`}
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          Taak toevoegen
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <form
          onSubmit={handleCreate}
          className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-3"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-foreground">
                Titel *
              </label>
              <input
                type="text"
                required
                value={form.title}
                onChange={(e) =>
                  setForm((f) => ({ ...f, title: e.target.value }))
                }
                placeholder="Bijv. Bel debiteur voor betalingsherinnering"
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Type
              </label>
              <select
                value={form.task_type}
                onChange={(e) =>
                  setForm((f) => ({ ...f, task_type: e.target.value }))
                }
                className={inputClass}
              >
                {Object.entries(TASK_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Deadline *
              </label>
              <input
                type="date"
                required
                value={form.due_date}
                onChange={(e) =>
                  setForm((f) => ({ ...f, due_date: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            {/* G9: Recurrence dropdown */}
            <div>
              <label className="block text-xs font-medium text-foreground">
                Herhaling
              </label>
              <select
                value={form.recurrence}
                onChange={(e) =>
                  setForm((f) => ({ ...f, recurrence: e.target.value }))
                }
                className={inputClass}
              >
                {Object.entries(RECURRENCE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            {form.recurrence !== "none" && (
              <div>
                <label className="block text-xs font-medium text-foreground">
                  Herhalen tot
                </label>
                <input
                  type="date"
                  value={form.recurrence_end_date}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, recurrence_end_date: e.target.value }))
                  }
                  className={inputClass}
                />
                <p className="mt-0.5 text-[10px] text-muted-foreground">Optioneel</p>
              </div>
            )}
            <div className={form.recurrence !== "none" ? "sm:col-span-2" : "sm:col-span-2"}>
              <label className="block text-xs font-medium text-foreground">
                Omschrijving
              </label>
              <input
                type="text"
                value={form.description}
                onChange={(e) =>
                  setForm((f) => ({ ...f, description: e.target.value }))
                }
                className={inputClass}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createTask.isPending}
              className="rounded-lg bg-primary px-4 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              Aanmaken
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="rounded-lg border border-border px-4 py-2 text-xs font-medium hover:bg-muted"
            >
              Annuleren
            </button>
          </div>
        </form>
      )}

      {/* Loading */}
      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg skeleton" />
          ))}
        </div>
      ) : tasks.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <CheckCircle2 className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">
            Geen taken voor dit dossier
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            Taken worden automatisch aangemaakt bij statuswijzigingen
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Open tasks */}
          {openTasks.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Openstaand
              </h3>
              {openTasks.map((task) => (
                <div
                  key={task.id}
                  className={`flex items-start gap-3 rounded-lg border p-4 transition-colors ${
                    task.status === "overdue"
                      ? "border-red-200 bg-red-50/50"
                      : "border-border bg-card"
                  }`}
                >
                  <button
                    onClick={() => handleComplete(task.id)}
                    className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 border-border hover:border-primary hover:bg-primary/10 transition-colors"
                    title="Markeer als afgerond"
                  >
                    {completeTask.isPending ? (
                      <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
                    ) : null}
                  </button>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-medium text-foreground">
                        {task.title}
                      </p>
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${
                          TASK_STATUS_BADGE[task.status] ??
                          "bg-slate-50 text-slate-600 ring-slate-500/20"
                        }`}
                      >
                        {TASK_STATUS_LABELS[task.status] ?? task.status}
                      </span>
                    </div>
                    {task.description && (
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {task.description}
                      </p>
                    )}
                    <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        Deadline: {formatDateShort(task.due_date)}
                      </span>
                      <span>
                        {TASK_TYPE_LABELS[task.task_type] ?? task.task_type}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => handleSkip(task.id)}
                    className="shrink-0 rounded-lg p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                    title="Overslaan"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Completed tasks */}
          {completedTasks.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Afgerond
              </h3>
              {completedTasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-start gap-3 rounded-lg border border-border bg-muted/30 p-4 opacity-60"
                >
                  <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-100">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-medium text-foreground line-through">
                        {task.title}
                      </p>
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${
                          TASK_STATUS_BADGE[task.status] ??
                          "bg-slate-50 text-slate-600 ring-slate-500/20"
                        }`}
                      >
                        {TASK_STATUS_LABELS[task.status] ?? task.status}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {task.completed_at
                        ? formatDateShort(task.completed_at)
                        : ""}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
