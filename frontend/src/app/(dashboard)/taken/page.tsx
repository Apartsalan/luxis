"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  Circle,
  AlertTriangle,
  Clock,
  SkipForward,
  Filter,
  Briefcase,
  CalendarDays,
  CheckSquare,
  Inbox,
  Plus,
  Loader2,
  Repeat,
  X,
  Zap,
  Eye,
  ArrowUpRight,
  RotateCcw,
} from "lucide-react";
import { toast } from "sonner";

import { cn, formatDateShort } from "@/lib/utils";
import { TASK_STATUS_BADGE, TASK_STATUS_BADGE_FALLBACK } from "@/lib/status-constants";
import {
  useMyTasks,
  useCompleteTask,
  useSkipTask,
  useRestoreTask,
  useCreateTask,
  TASK_TYPE_LABELS,
  TASK_STATUS_LABELS,
  RECURRENCE_LABELS,
  type WorkflowTask,
} from "@/hooks/use-workflow";
import { useAuth } from "@/hooks/use-auth";
import { useCases } from "@/hooks/use-cases";
import { useFollowupPendingCount } from "@/hooks/use-followup";
import { useIntakePendingCount } from "@/hooks/use-intake";

// ── Helpers ──────────────────────────────────────────────────────────────────

type TaskFilter = "all" | "open" | "completed";

function getRelativeDateLabel(dateStr: string): string {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const d = new Date(dateStr);
  d.setHours(0, 0, 0, 0);
  const diff = d.getTime() - today.getTime();
  const diffDays = Math.round(diff / (1000 * 60 * 60 * 24));

  if (diffDays < 0) return `${Math.abs(diffDays)} dag${Math.abs(diffDays) === 1 ? "" : "en"} te laat`;
  if (diffDays === 0) return "Vandaag";
  if (diffDays === 1) return "Morgen";
  if (diffDays <= 7) return `Over ${diffDays} dagen`;
  return formatDateShort(dateStr);
}

function getStatusIcon(status: string) {
  switch (status) {
    case "overdue":
      return <AlertTriangle className="h-4 w-4 text-destructive" />;
    case "due":
      return <Clock className="h-4 w-4 text-amber-500" />;
    case "pending":
      return <Circle className="h-4 w-4 text-muted-foreground" />;
    case "completed":
      return <CheckCircle2 className="h-4 w-4 text-emerald-500" />;
    case "skipped":
      return <SkipForward className="h-4 w-4 text-muted-foreground" />;
    default:
      return <Circle className="h-4 w-4 text-muted-foreground" />;
  }
}

function getStatusBadgeClass(status: string): string {
  return TASK_STATUS_BADGE[status] ?? TASK_STATUS_BADGE_FALLBACK;
}

function groupTasksByDate(tasks: WorkflowTask[]) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const endOfWeek = new Date(today);
  endOfWeek.setDate(today.getDate() + (7 - today.getDay()));

  const groups: { label: string; tasks: WorkflowTask[] }[] = [
    { label: "Te laat", tasks: [] },
    { label: "Vandaag", tasks: [] },
    { label: "Deze week", tasks: [] },
    { label: "Later", tasks: [] },
    { label: "Afgerond", tasks: [] },
  ];

  for (const task of tasks) {
    if (task.status === "completed" || task.status === "skipped") {
      groups[4].tasks.push(task);
      continue;
    }

    const due = new Date(task.due_date);
    due.setHours(0, 0, 0, 0);

    if (due < today) {
      groups[0].tasks.push(task);
    } else if (due.getTime() === today.getTime()) {
      groups[1].tasks.push(task);
    } else if (due <= endOfWeek) {
      groups[2].tasks.push(task);
    } else {
      groups[3].tasks.push(task);
    }
  }

  return groups.filter((g) => g.tasks.length > 0);
}

// ── Component: TaskRow ───────────────────────────────────────────────────────

function TaskRow({
  task,
  onComplete,
  onSkip,
  onRestore,
  isCompleting,
  isSkipping,
  isRestoring,
}: {
  task: WorkflowTask;
  onComplete: (id: string) => void;
  onSkip: (id: string) => void;
  onRestore: (id: string) => void;
  isCompleting: boolean;
  isSkipping: boolean;
  isRestoring: boolean;
}) {
  const isDone = task.status === "completed" || task.status === "skipped";
  const isOpen = task.status === "pending" || task.status === "due" || task.status === "overdue";

  return (
    <div
      className={cn(
        "group flex items-start gap-3 rounded-lg border p-3 transition-colors",
        isDone ? "bg-muted/30 opacity-60" : "bg-card hover:bg-accent/5",
        task.status === "overdue" && "border-destructive/30"
      )}
    >
      {/* Checkbox / complete button */}
      <button
        onClick={() => onComplete(task.id)}
        disabled={isDone || isCompleting}
        className={cn(
          "mt-0.5 shrink-0 rounded-full p-0.5 transition-colors",
          isOpen && "hover:bg-emerald-100 hover:text-emerald-600 cursor-pointer",
          isDone && "cursor-default"
        )}
        title={isDone ? "Al afgerond" : "Markeer als afgerond"}
        aria-label={isDone ? "Al afgerond" : "Markeer als afgerond"}
      >
        {isDone ? (
          <CheckCircle2 className="h-5 w-5 text-emerald-500" />
        ) : (
          <Circle
            className={cn(
              "h-5 w-5",
              task.status === "overdue"
                ? "text-destructive"
                : "text-muted-foreground group-hover:text-emerald-400"
            )}
          />
        )}
      </button>

      {/* Task content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <Link
            href={`/zaken/${task.case_id}`}
            className={cn(
              "text-sm font-medium leading-snug hover:text-primary transition-colors",
              isDone && "line-through text-muted-foreground"
            )}
          >
            {task.title}
          </Link>
          {/* Status badge */}
          <span
            className={cn(
              "shrink-0 inline-flex items-center gap-1 rounded-full ring-1 ring-inset px-2 py-0.5 text-xs font-medium",
              getStatusBadgeClass(task.status)
            )}
          >
            {getStatusIcon(task.status)}
            {TASK_STATUS_LABELS[task.status] || task.status}
          </span>
        </div>

        {/* Meta row */}
        <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
          {/* Due date */}
          <span className="flex items-center gap-1">
            <CalendarDays className="h-3 w-3" />
            {getRelativeDateLabel(task.due_date)}
          </span>

          {/* Case link */}
          {task.case && (
            <Link
              href={`/zaken/${task.case_id}`}
              className="flex items-center gap-1 hover:text-foreground transition-colors"
            >
              <Briefcase className="h-3 w-3" />
              {task.case.case_number}
            </Link>
          )}

          {/* Task type */}
          <span className="flex items-center gap-1">
            {TASK_TYPE_LABELS[task.task_type] || task.task_type}
          </span>

          {/* G9: Recurring badge */}
          {task.recurrence && (
            <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 border border-blue-200 px-1.5 py-0.5 text-[10px] font-medium text-blue-700">
              <Repeat className="h-2.5 w-2.5" />
              {RECURRENCE_LABELS[task.recurrence] || task.recurrence}
            </span>
          )}
        </div>

        {/* Description */}
        {task.description && (
          <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
            {task.description}
          </p>
        )}

        {/* Concept-mail reviewen: directe knop om het concept te heropenen
            (review + versturen). Verse navigatie naar het dossier met
            ?draft=latest → de dossierpagina opent het nieuwste niet-verzonden
            concept in de review/verstuur-dialoog. */}
        {task.task_type === "review_ai_draft" && task.case_id && (
          <Link
            href={`/zaken/${task.case_id}?draft=latest`}
            className="mt-2 inline-flex items-center gap-1.5 rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Eye className="h-3.5 w-3.5" />
            Concept openen
          </Link>
        )}

        {/* S236: verstuur-taak van de follow-up-adviseur → direct door naar de
            Follow-up-pagina waar de brief gecontroleerd en verstuurd wordt. */}
        {task.task_type === "send_letter" &&
          task.action_config?.source === "followup_send" && (
            <Link
              href="/followup"
              className="mt-2 inline-flex items-center gap-1.5 rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <Eye className="h-3.5 w-3.5" />
              Controleren & versturen
            </Link>
          )}

        {/* S237: gespiegelde escalatie-taak van de follow-up-adviseur → door
            naar de Follow-up-pagina waar het advies beoordeeld wordt. */}
        {task.task_type === "manual_review" &&
          task.action_config?.source === "followup_escalate" && (
            <Link
              href="/followup"
              className="mt-2 inline-flex items-center gap-1.5 rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <Eye className="h-3.5 w-3.5" />
              Beoordelen
            </Link>
          )}
      </div>

      {/* Skip button (open taken) */}
      {isOpen && (
        <button
          onClick={() => onSkip(task.id)}
          disabled={isSkipping}
          className="shrink-0 mt-0.5 rounded-md p-1.5 text-muted-foreground max-sm:opacity-100 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 hover:bg-muted hover:text-foreground transition-all"
          title="Overslaan"
          aria-label="Overslaan"
        >
          <SkipForward className="h-4 w-4" />
        </button>
      )}

      {/* Terugzet-knop (overgeslagen/afgeronde taken → terug op de werklijst) */}
      {isDone && (
        <button
          onClick={() => onRestore(task.id)}
          disabled={isRestoring}
          className="shrink-0 mt-0.5 inline-flex items-center gap-1 rounded-md px-2 py-1.5 text-xs font-medium text-muted-foreground max-sm:opacity-100 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 hover:bg-muted hover:text-foreground transition-all"
          title="Terugzetten op werklijst"
          aria-label="Terugzetten op werklijst"
        >
          <RotateCcw className="h-4 w-4" />
          Terugzetten
        </button>
      )}
    </div>
  );
}

// ── Dagstart-verwijzingen (Follow-up + Intake) ───────────────────────────────
// A3 (S198): geen gekopieerde kaartlijsten meer op Taken — Follow-up en Intake
// hebben hun eigen pagina + zijbalk-badge. Hier alleen een compacte verwijzing,
// zodat Taken de dagstart-hub blijft zonder te dubbelen.

function DagstartLinks() {
  const { data: followupData } = useFollowupPendingCount();
  const { data: intakeData } = useIntakePendingCount();
  const followupCount = followupData?.count ?? 0;
  const intakeCount = intakeData?.count ?? 0;

  if (followupCount === 0 && intakeCount === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2">
      {followupCount > 0 && (
        <Link
          href="/followup"
          className="inline-flex items-center gap-2 rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-xs font-medium text-primary hover:bg-primary/10 transition-colors"
        >
          <Zap className="h-3.5 w-3.5" />
          {followupCount} AI-aanbeveling{followupCount !== 1 ? "en" : ""}
          <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
      )}
      {intakeCount > 0 && (
        <Link
          href="/intake"
          className="inline-flex items-center gap-2 rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-xs font-medium text-primary hover:bg-primary/10 transition-colors"
        >
          <Inbox className="h-3.5 w-3.5" />
          {intakeCount} nieuwe aanvra{intakeCount !== 1 ? "gen" : "ag"}
          <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
      )}
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function TakenPage() {
  const [filter, setFilter] = useState<TaskFilter>("open");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    case_id: "",
    title: "",
    task_type: "custom",
    due_date: new Date().toISOString().split("T")[0],
    description: "",
    recurrence: "none",
    recurrence_end_date: "",
  });

  const { user } = useAuth();
  const { data: tasks, isLoading, error } = useMyTasks();
  const { data: casesData } = useCases({ per_page: 100, status: "" });
  const completeTask = useCompleteTask();
  const skipTask = useSkipTask();
  const restoreTask = useRestoreTask();
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
  const TASKS_PER_GROUP = 10;
  const createTask = useCreateTask();

  const cases = casesData?.items ?? [];

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.case_id) {
      toast.error("Selecteer een dossier");
      return;
    }
    try {
      await createTask.mutateAsync({
        case_id: form.case_id,
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
        case_id: "",
        title: "",
        task_type: "custom",
        due_date: new Date().toISOString().split("T")[0],
        description: "",
        recurrence: "none",
        recurrence_end_date: "",
      });
    } catch {}
  };

  const handleComplete = (id: string) => {
    completeTask.mutate(id, {
      onSuccess: () => toast.success("Taak afgerond"),
    });
  };

  const handleRestore = (id: string) => {
    restoreTask.mutate(id, {
      onSuccess: () => toast.success("Taak teruggezet op de werklijst"),
      onError: (e) => toast.error(e instanceof Error ? e.message : "Fout bij terugzetten"),
    });
  };

  const handleSkip = (id: string) => {
    skipTask.mutate(id, {
      onSuccess: () =>
        toast.success("Taak overgeslagen", {
          action: {
            label: "Ongedaan maken",
            onClick: () => handleRestore(id),
          },
        }),
      onError: (e) => toast.error(e instanceof Error ? e.message : "Fout bij overslaan"),
    });
  };

  // Also fetch completed tasks for the "all" and "completed" views
  // The my-tasks endpoint only returns open tasks, so we handle completed separately
  const filteredTasks = useMemo(() => {
    if (!tasks) return [];
    switch (filter) {
      case "open":
        return tasks.filter(
          (t) => t.status !== "completed" && t.status !== "skipped"
        );
      case "completed":
        return tasks.filter(
          (t) => t.status === "completed" || t.status === "skipped"
        );
      default:
        return tasks;
    }
  }, [tasks, filter]);

  const groups = useMemo(() => groupTasksByDate(filteredTasks), [filteredTasks]);

  // Stats
  const openCount = tasks?.filter(
    (t) => t.status !== "completed" && t.status !== "skipped"
  ).length ?? 0;
  const overdueCount = tasks?.filter((t) => t.status === "overdue").length ?? 0;
  const dueToday = tasks?.filter((t) => {
    if (t.status === "completed" || t.status === "skipped") return false;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const due = new Date(t.due_date);
    due.setHours(0, 0, 0, 0);
    return due.getTime() === today.getTime();
  }).length ?? 0;

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Mijn Taken</h1>
          <p className="text-muted-foreground text-sm mt-1">Laden...</p>
        </div>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="h-20 rounded-lg border skeleton"
            />
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Mijn Taken</h1>
        </div>
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center">
          <AlertTriangle className="h-8 w-8 text-destructive mx-auto" />
          <p className="mt-2 text-sm text-destructive">
            Kon taken niet laden. Probeer het opnieuw.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Mijn Taken</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {openCount === 0
              ? "Geen openstaande taken"
              : `${openCount} openstaand${overdueCount > 0 ? `, ${overdueCount} te laat` : ""}${dueToday > 0 ? `, ${dueToday} vandaag` : ""}`}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowForm(!showForm)}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Nieuwe taak
          </button>

        {/* Filter buttons */}
        <div className="flex items-center gap-1 rounded-lg border bg-muted/30 p-1">
          {(
            [
              { value: "open", label: "Openstaand" },
              { value: "all", label: "Alles" },
              { value: "completed", label: "Afgerond" },
            ] as const
          ).map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={cn(
                "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                filter === f.value
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
        </div>
      </div>

      {/* A3 (S198): Taken = pure werklijst. Follow-up en Intake hebben hun eigen
          pagina + zijbalk-badge; hier alleen een compacte verwijzing (dagstart-hub)
          i.p.v. de volledige gekopieerde kaartlijsten. */}
      <DagstartLinks />

      {/* Create task form */}
      {showForm && (
        <form
          onSubmit={handleCreate}
          className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-3"
        >
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-sm font-semibold text-foreground">Nieuwe taak</h3>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              aria-label="Sluiten"
              className="rounded-md p-1 hover:bg-muted transition-colors"
            >
              <X className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label htmlFor="taak-dossier" className="block text-xs font-medium text-foreground">
                Dossier *
              </label>
              <select
                id="taak-dossier"
                required
                value={form.case_id}
                onChange={(e) => setForm((f) => ({ ...f, case_id: e.target.value }))}
                className="mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
              >
                <option value="">Selecteer een dossier...</option>
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.case_number} — {c.client?.name ?? "Geen cliënt"}{c.description ? ` · ${c.description}` : ""}
                  </option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label htmlFor="taak-titel" className="block text-xs font-medium text-foreground">
                Titel *
              </label>
              <input
                id="taak-titel"
                type="text"
                required
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                placeholder="Bijv. Bel debiteur voor betalingsherinnering"
                className="mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
              />
            </div>
            <div>
              <label htmlFor="taak-type" className="block text-xs font-medium text-foreground">
                Type
              </label>
              <select
                id="taak-type"
                value={form.task_type}
                onChange={(e) => setForm((f) => ({ ...f, task_type: e.target.value }))}
                className="mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
              >
                {Object.entries(TASK_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="taak-deadline" className="block text-xs font-medium text-foreground">
                Deadline *
              </label>
              <input
                id="taak-deadline"
                type="date"
                required
                value={form.due_date}
                onChange={(e) => setForm((f) => ({ ...f, due_date: e.target.value }))}
                className="mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
              />
            </div>
            {/* G9: Recurrence dropdown */}
            <div>
              <label htmlFor="taak-herhaling" className="block text-xs font-medium text-foreground">
                Herhaling
              </label>
              <select
                id="taak-herhaling"
                value={form.recurrence}
                onChange={(e) => setForm((f) => ({ ...f, recurrence: e.target.value }))}
                className="mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
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
                <label htmlFor="taak-herhalen-tot" className="block text-xs font-medium text-foreground">
                  Herhalen tot
                </label>
                <input
                  id="taak-herhalen-tot"
                  type="date"
                  value={form.recurrence_end_date}
                  onChange={(e) => setForm((f) => ({ ...f, recurrence_end_date: e.target.value }))}
                  className="mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                  placeholder="Optioneel"
                />
                <p className="mt-0.5 text-[10px] text-muted-foreground">Optioneel — leeg = oneindig</p>
              </div>
            )}
            <div className={form.recurrence !== "none" ? "" : "sm:col-span-2"}>
              <label htmlFor="taak-omschrijving" className="block text-xs font-medium text-foreground">
                Omschrijving
              </label>
              <input
                id="taak-omschrijving"
                type="text"
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                className="mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createTask.isPending}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {createTask.isPending && <Loader2 className="h-3 w-3 animate-spin" />}
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

      {/* Task groups */}
      {groups.length === 0 ? (
        <EmptyState filter={filter} />
      ) : (
        <div className="space-y-6">
          {groups.map((group) => (
            <div key={group.label}>
              <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                {group.label}
                <span className="ml-2 text-xs font-normal">
                  ({group.tasks.length})
                </span>
              </h2>
              <div className="space-y-2">
                {(expandedGroups[group.label] ? group.tasks : group.tasks.slice(0, TASKS_PER_GROUP)).map((task) => (
                  <TaskRow
                    key={task.id}
                    task={task}
                    onComplete={handleComplete}
                    onSkip={handleSkip}
                    onRestore={handleRestore}
                    isCompleting={completeTask.isPending}
                    isSkipping={skipTask.isPending}
                    isRestoring={restoreTask.isPending}
                  />
                ))}
                {group.tasks.length > TASKS_PER_GROUP && !expandedGroups[group.label] && (
                  <button
                    onClick={() => setExpandedGroups(prev => ({ ...prev, [group.label]: true }))}
                    className="w-full py-2 text-sm text-primary hover:text-primary/80 font-medium rounded-lg border border-dashed border-border hover:border-primary/30 transition-colors"
                  >
                    Toon alle {group.tasks.length} taken
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Empty State ──────────────────────────────────────────────────────────────

function EmptyState({ filter }: { filter: TaskFilter }) {
  if (filter === "completed") {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/50 py-20">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
          <CheckSquare className="h-8 w-8 text-muted-foreground" />
        </div>
        <p className="mt-5 text-base font-medium text-muted-foreground">
          Nog geen afgeronde taken
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          Afgeronde taken verschijnen hier.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card/50 py-20">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-50">
        <Inbox className="h-8 w-8 text-emerald-500/50" />
      </div>
      <p className="mt-5 text-base font-medium text-foreground">
        Alles gedaan!
      </p>
      <p className="mt-1 text-sm text-muted-foreground">
        Er zijn geen openstaande taken. Goed werk!
      </p>
    </div>
  );
}
