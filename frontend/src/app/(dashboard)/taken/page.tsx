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
  Bot,
  Check,
  Eye,
  ArrowUpRight,
} from "lucide-react";
import { toast } from "sonner";

import { cn, formatDateShort, formatCurrency } from "@/lib/utils";
import { TASK_STATUS_BADGE, TASK_STATUS_BADGE_FALLBACK } from "@/lib/status-constants";
import {
  useMyTasks,
  useCompleteTask,
  useSkipTask,
  useCreateTask,
  TASK_TYPE_LABELS,
  TASK_STATUS_LABELS,
  RECURRENCE_LABELS,
  type WorkflowTask,
} from "@/hooks/use-workflow";
import { useAuth } from "@/hooks/use-auth";
import { useCases } from "@/hooks/use-cases";
import {
  useFollowupRecommendations,
  useApproveAndExecuteFollowup,
  useRejectFollowup,
  type FollowupRecommendation,
} from "@/hooks/use-followup";
import { useIntakes, type IntakeResponse } from "@/hooks/use-intake";

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
  isCompleting,
  isSkipping,
}: {
  task: WorkflowTask;
  onComplete: (id: string) => void;
  onSkip: (id: string) => void;
  isCompleting: boolean;
  isSkipping: boolean;
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
      </div>

      {/* Skip button */}
      {isOpen && (
        <button
          onClick={() => onSkip(task.id)}
          disabled={isSkipping}
          className="shrink-0 mt-0.5 rounded-md p-1.5 text-muted-foreground opacity-0 group-hover:opacity-100 hover:bg-muted hover:text-foreground transition-all"
          title="Overslaan"
        >
          <SkipForward className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}

// ── AI Aanbevelingen (Follow-ups) ────────────────────────────────────────────

const URGENCY_STYLES: Record<string, string> = {
  high: "border-red-200 bg-red-50/50",
  medium: "border-amber-200 bg-amber-50/50",
  low: "border-border bg-card",
};

const URGENCY_BADGE: Record<string, string> = {
  high: "bg-red-50 text-red-700 ring-red-600/20",
  medium: "bg-amber-50 text-amber-700 ring-amber-600/20",
  low: "bg-slate-50 text-slate-600 ring-slate-500/20",
};

function FollowupSection() {
  const { data, isLoading } = useFollowupRecommendations("pending", 1, 5);
  const approveAndExecute = useApproveAndExecuteFollowup();
  const reject = useRejectFollowup();

  const items = data?.items ?? [];

  if (isLoading || items.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Zap className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-semibold text-foreground">AI Aanbevelingen</h2>
        <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
          {data?.total ?? items.length}
        </span>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <div
            key={item.id}
            className={cn(
              "rounded-lg border p-3 transition-colors",
              URGENCY_STYLES[item.urgency] ?? URGENCY_STYLES.low,
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <Link
                  href={`/zaken/${item.case_id}`}
                  className="text-sm font-medium text-foreground hover:text-primary transition-colors"
                >
                  {item.case_number}
                </Link>
                <p className="text-xs text-muted-foreground truncate mt-0.5">
                  {item.opposing_party_name ?? item.client_name ?? ""}
                </p>
              </div>
              <span
                className={cn(
                  "shrink-0 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset",
                  URGENCY_BADGE[item.urgency] ?? URGENCY_BADGE.low,
                )}
              >
                {item.urgency_label || item.urgency}
              </span>
            </div>
            <p className="mt-2 text-xs text-foreground font-medium">
              {item.action_label || item.recommended_action}
            </p>
            <p className="mt-0.5 text-[11px] text-muted-foreground line-clamp-2">
              {item.reasoning}
            </p>
            <div className="mt-2.5 flex items-center gap-1.5">
              <button
                onClick={() => approveAndExecute.mutate({ id: item.id }, {
                  onSuccess: () => toast.success("Aanbeveling uitgevoerd"),
                  onError: (err) => toast.error(err.message),
                })}
                disabled={approveAndExecute.isPending}
                className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                <Check className="h-3 w-3" />
                Akkoord
              </button>
              <button
                onClick={() => reject.mutate({ id: item.id }, {
                  onSuccess: () => toast.success("Aanbeveling afgewezen"),
                  onError: (err) => toast.error(err.message),
                })}
                disabled={reject.isPending}
                className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium text-muted-foreground hover:bg-muted disabled:opacity-50 transition-colors"
              >
                <X className="h-3 w-3" />
                Afwijzen
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Nieuwe Dossiers (Intakes) ────────────────────────────────────────────────

function confidenceBadge(confidence: number | null) {
  if (!confidence) return "bg-slate-50 text-slate-600 ring-slate-500/20";
  if (confidence >= 80) return "bg-emerald-50 text-emerald-700 ring-emerald-600/20";
  if (confidence >= 60) return "bg-amber-50 text-amber-700 ring-amber-600/20";
  return "bg-red-50 text-red-700 ring-red-600/20";
}

function IntakeSection() {
  const { data: intakes, isLoading } = useIntakes("pending", 1, 5);

  const items = intakes ?? [];

  if (isLoading || items.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Bot className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-semibold text-foreground">Nieuwe Dossiers</h2>
        <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
          {items.length}
        </span>
      </div>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <div
            key={item.id}
            className="rounded-lg border bg-card p-3 hover:bg-accent/5 transition-colors"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-foreground truncate">
                  {item.email_subject}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {item.email_from}
                </p>
              </div>
              <span
                className={cn(
                  "shrink-0 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset",
                  confidenceBadge(item.ai_confidence),
                )}
              >
                {item.ai_confidence ? `${Math.round(item.ai_confidence)}%` : "?"}
              </span>
            </div>
            {(item.debtor_name || item.principal_amount) && (
              <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                {item.debtor_name && <span>{item.debtor_name}</span>}
                {item.principal_amount && (
                  <span className="font-medium text-foreground tabular-nums">
                    {formatCurrency(item.principal_amount)}
                  </span>
                )}
              </div>
            )}
            <div className="mt-2.5">
              <Link
                href={`/intake/${item.id}`}
                className="inline-flex items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium text-foreground hover:bg-muted transition-colors"
              >
                <Eye className="h-3 w-3" />
                Bekijken
              </Link>
            </div>
          </div>
        ))}
      </div>
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
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleComplete = (id: string) => {
    completeTask.mutate(id, {
      onSuccess: () => toast.success("Taak afgerond"),
      onError: (err) => toast.error(err.message),
    });
  };

  const handleSkip = (id: string) => {
    skipTask.mutate(id, {
      onSuccess: () => toast.success("Taak overgeslagen"),
      onError: (err) => toast.error(err.message),
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

      {/* AI Sections */}
      <FollowupSection />
      <IntakeSection />

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
              className="rounded-md p-1 hover:bg-muted transition-colors"
            >
              <X className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-foreground">
                Dossier *
              </label>
              <select
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
              <label className="block text-xs font-medium text-foreground">
                Titel *
              </label>
              <input
                type="text"
                required
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                placeholder="Bijv. Bel debiteur voor betalingsherinnering"
                className="mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Type
              </label>
              <select
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
              <label className="block text-xs font-medium text-foreground">
                Deadline *
              </label>
              <input
                type="date"
                required
                value={form.due_date}
                onChange={(e) => setForm((f) => ({ ...f, due_date: e.target.value }))}
                className="mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
              />
            </div>
            {/* G9: Recurrence dropdown */}
            <div>
              <label className="block text-xs font-medium text-foreground">
                Herhaling
              </label>
              <select
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
                <label className="block text-xs font-medium text-foreground">
                  Herhalen tot
                </label>
                <input
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
              <label className="block text-xs font-medium text-foreground">
                Omschrijving
              </label>
              <input
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
                    isCompleting={completeTask.isPending}
                    isSkipping={skipTask.isPending}
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
          <CheckSquare className="h-8 w-8 text-muted-foreground/50" />
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
