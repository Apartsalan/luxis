"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Mail,
  RefreshCw,
  Sparkles,
  Tag,
  X,
  ChevronDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  useCaseActionFeed,
  useDismissFeedItem,
  useSnoozeFeedItem,
  SNOOZE_OPTIONS,
  type FeedFilter,
} from "@/hooks/use-case-action-feed";
import type { Notification } from "@/hooks/use-notifications";
import { formatNotificationTime } from "@/hooks/use-notifications";

const MAX_VISIBLE = 3;

interface CaseActionFeedProps {
  caseId: string;
  /** Active tab id passed from the parent — when user navigates away to another
   *  feed action (correspondentie, pipeline, etc.) we want to forward via callback. */
  onNavigate?: (tab: string) => void;
}

/**
 * One activity-feed widget at the top of the case Overzicht-tab.
 *
 * Bundles four notification types into clickable cards so Lisanne sees every
 * AI-driven event in one place instead of scattered banners (S134 lesson).
 *
 * UX rules (S146 design):
 *   - Max 3 cards visible, rest behind "Toon alle" toggle
 *   - Default filter: only items requiring action
 *   - Persistent — items only disappear after Lisanne dismisses or acts
 *   - 30s polling + refetch-on-focus (no WebSocket yet)
 */
export function CaseActionFeed({ caseId, onNavigate }: CaseActionFeedProps) {
  const [filter, setFilter] = useState<FeedFilter>("wachtend");
  const [showAll, setShowAll] = useState(false);
  const { items, isLoading, refetch } = useCaseActionFeed({ caseId, filter });
  // Counts in other filters so we can hint the user when "Wachtend" is empty
  // but there are still items under "Afgehandeld" / "Alles".
  const allFeed = useCaseActionFeed({ caseId, filter: "alles" });
  const dismiss = useDismissFeedItem();
  const snooze = useSnoozeFeedItem();

  if (isLoading) return null;
  // Hide entirely on a fresh case with zero activity ever
  if (items.length === 0 && allFeed.items.length === 0) return null;

  // Deadline cards always first; rest sorted by created_at desc (already from API)
  const sorted = [...items].sort((a, b) => {
    if (a.type === "deadline_overdue" && b.type !== "deadline_overdue") return -1;
    if (b.type === "deadline_overdue" && a.type !== "deadline_overdue") return 1;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  const visible = showAll ? sorted : sorted.slice(0, MAX_VISIBLE);
  const hiddenCount = sorted.length - visible.length;

  return (
    <div className="mb-6 rounded-lg border border-border bg-card">
      <div className="flex items-center justify-between gap-3 border-b border-border px-5 py-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-violet-500" />
          <h3 className="text-sm font-semibold text-foreground">
            Wat moet u doen?
          </h3>
          {sorted.length > 0 && (
            <Badge variant="secondary" className="ml-1">
              {sorted.length}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 rounded-md bg-muted p-0.5">
            <FilterTab active={filter === "wachtend"} onClick={() => setFilter("wachtend")}>
              Wachtend
            </FilterTab>
            <FilterTab active={filter === "afgehandeld"} onClick={() => setFilter("afgehandeld")}>
              Afgehandeld
            </FilterTab>
            <FilterTab active={filter === "alles"} onClick={() => setFilter("alles")}>
              Alles
            </FilterTab>
          </div>
          <button
            type="button"
            onClick={() => { refetch(); allFeed.refetch(); }}
            aria-label="Verversen"
            title="Verversen"
            className="rounded p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {sorted.length === 0 ? (
        <div className="flex flex-col items-center justify-center px-5 py-8 text-center">
          <CheckCircle2 className="mb-2 h-8 w-8 text-emerald-500" />
          <p className="text-sm font-medium text-foreground">
            {filter === "wachtend" ? "Niets meer te doen — goed bezig!" : "Geen berichten."}
          </p>
          {filter === "wachtend" && allFeed.items.length > 0 && (
            <button
              type="button"
              onClick={() => setFilter("alles")}
              className="mt-2 text-xs text-primary hover:underline"
            >
              Bekijk {allFeed.items.length} afgehandeld bericht{allFeed.items.length === 1 ? "" : "en"}
            </button>
          )}
        </div>
      ) : (
        <ul className="divide-y divide-border">
          {visible.map((item) => (
            <FeedCard
              key={item.id}
              item={item}
              onDismiss={() => dismiss.mutate(item.id)}
              onSnooze={(hours) => snooze.mutate({ id: item.id, hours })}
              onNavigate={onNavigate}
            />
          ))}
        </ul>
      )}

      {hiddenCount > 0 && (
        <button
          type="button"
          onClick={() => setShowAll(true)}
          className="flex w-full items-center justify-center gap-1 border-t border-border py-2 text-xs text-muted-foreground hover:bg-muted/40 hover:text-foreground transition-colors"
        >
          <ChevronDown className="h-3 w-3" />
          Toon alle {sorted.length} berichten
        </button>
      )}
      {showAll && sorted.length > MAX_VISIBLE && (
        <button
          type="button"
          onClick={() => setShowAll(false)}
          className="flex w-full items-center justify-center border-t border-border py-2 text-xs text-muted-foreground hover:bg-muted/40 hover:text-foreground transition-colors"
        >
          Toon minder
        </button>
      )}
    </div>
  );
}

// ─── Filter tab ───────────────────────────────────────────────────

function FilterTab({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded px-2 py-1 text-xs font-medium transition-colors ${
        active
          ? "bg-background text-foreground shadow-sm"
          : "text-muted-foreground hover:text-foreground"
      }`}
    >
      {children}
    </button>
  );
}

// ─── Card router ──────────────────────────────────────────────────

interface FeedCardProps {
  item: Notification;
  onDismiss: () => void;
  onSnooze: (hours: number) => void;
  onNavigate?: (tab: string) => void;
}

function FeedCard({ item, onDismiss, onSnooze, onNavigate }: FeedCardProps) {
  const shared = { item, onDismiss, onSnooze, onNavigate };
  switch (item.type) {
    case "ai_draft_ready":
      return <DraftReadyCard {...shared} />;
    case "email_received":
      return <EmailReceivedCard {...shared} />;
    case "classification_done":
      return <ClassificationDoneCard {...shared} />;
    case "deadline_overdue":
    case "deadline_approaching":
    case "verjaring_warning":
      return <DeadlineCard {...shared} />;
    default:
      return null;
  }
}

// ─── Individual cards ─────────────────────────────────────────────

function CardShell({
  icon,
  iconClass,
  title,
  time,
  message,
  actions,
  onDismiss,
  onSnooze,
  isRead,
  snoozedUntil,
}: {
  icon: React.ReactNode;
  iconClass: string;
  title: string;
  time: string;
  message?: string;
  actions: React.ReactNode;
  onDismiss: () => void;
  onSnooze: (hours: number) => void;
  isRead: boolean;
  snoozedUntil?: string | null;
}) {
  const isSnoozed = snoozedUntil != null && new Date(snoozedUntil).getTime() > Date.now();
  return (
    <li
      className={`group flex items-start gap-3 px-5 py-4 transition-colors hover:bg-muted/30 ${
        isRead ? "opacity-60" : ""
      }`}
    >
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${iconClass}`}>
        {icon}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-2">
          <p className="truncate text-sm font-medium text-foreground">{title}</p>
          <span className="shrink-0 text-xs text-muted-foreground">{time}</span>
        </div>
        {message && (
          <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{message}</p>
        )}
        {isSnoozed && (
          <p className="mt-1 inline-flex items-center gap-1 text-[11px] text-muted-foreground">
            <Clock className="h-3 w-3" />
            Sluimert tot{" "}
            {new Date(snoozedUntil!).toLocaleDateString("nl-NL", {
              weekday: "short",
              day: "numeric",
              month: "short",
            })}
            <button
              type="button"
              onClick={() => onSnooze(0)}
              className="ml-1 text-primary hover:underline"
            >
              Nu tonen
            </button>
          </p>
        )}
        <div className="mt-2 flex flex-wrap items-center gap-2">{actions}</div>
      </div>
      <div className="flex shrink-0 items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
        <SnoozeMenu onSnooze={onSnooze} />
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Verwijder uit lijst"
          className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </li>
  );
}

/** Small clock-icon button revealing the fixed snooze durations. */
function SnoozeMenu({ onSnooze }: { onSnooze: (hours: number) => void }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label="Uitstellen"
        title="Uitstellen"
        className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
      >
        <Clock className="h-3.5 w-3.5" />
      </button>
      {open && (
        <>
          {/* click-away backdrop */}
          <button
            type="button"
            aria-hidden="true"
            tabIndex={-1}
            className="fixed inset-0 z-10 cursor-default"
            onClick={() => setOpen(false)}
          />
          <div className="absolute right-0 z-20 mt-1 w-32 overflow-hidden rounded-md border border-border bg-popover py-1 shadow-md">
            <p className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Uitstellen
            </p>
            {SNOOZE_OPTIONS.map((opt) => (
              <button
                key={opt.hours}
                type="button"
                onClick={() => {
                  onSnooze(opt.hours);
                  setOpen(false);
                }}
                className="block w-full px-3 py-1.5 text-left text-xs text-foreground hover:bg-muted"
              >
                {opt.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function DraftReadyCard({ item, onDismiss, onSnooze, onNavigate }: FeedCardProps) {
  const router = useRouter();
  const openTaken = () => {
    if (onNavigate) onNavigate("taken");
    else if (item.case_id) router.push(`/zaken/${item.case_id}?tab=taken`);
  };
  return (
    <CardShell
      icon={<Sparkles className="h-4 w-4 text-violet-600" />}
      iconClass="bg-violet-100 dark:bg-violet-950"
      title={item.title}
      message={item.message}
      time={formatNotificationTime(item.created_at)}
      isRead={item.is_read}
      snoozedUntil={item.snoozed_until}
      onDismiss={onDismiss}
      onSnooze={onSnooze}
      actions={
        <Button size="sm" variant="default" onClick={openTaken}>
          Openen
        </Button>
      }
    />
  );
}

function EmailReceivedCard({ item, onDismiss, onSnooze, onNavigate }: FeedCardProps) {
  const router = useRouter();
  const openCorrespondentie = () => {
    if (onNavigate) onNavigate("correspondentie");
    else if (item.case_id) router.push(`/zaken/${item.case_id}?tab=correspondentie`);
  };
  return (
    <CardShell
      icon={<Mail className="h-4 w-4 text-blue-600" />}
      iconClass="bg-blue-100 dark:bg-blue-950"
      title={item.title}
      message={item.message}
      time={formatNotificationTime(item.created_at)}
      isRead={item.is_read}
      snoozedUntil={item.snoozed_until}
      onDismiss={onDismiss}
      onSnooze={onSnooze}
      actions={
        <Button size="sm" variant="outline" onClick={openCorrespondentie}>
          Bekijken
        </Button>
      }
    />
  );
}

function ClassificationDoneCard({ item, onDismiss, onSnooze, onNavigate }: FeedCardProps) {
  const router = useRouter();
  const openCorrespondentie = () => {
    if (onNavigate) onNavigate("correspondentie");
    else if (item.case_id) router.push(`/zaken/${item.case_id}?tab=correspondentie`);
  };
  return (
    <CardShell
      icon={<Tag className="h-4 w-4 text-amber-600" />}
      iconClass="bg-amber-100 dark:bg-amber-950"
      title={item.title}
      message={item.message}
      time={formatNotificationTime(item.created_at)}
      isRead={item.is_read}
      snoozedUntil={item.snoozed_until}
      onDismiss={onDismiss}
      onSnooze={onSnooze}
      actions={
        <Button size="sm" variant="default" onClick={openCorrespondentie}>
          Antwoord opstellen
        </Button>
      }
    />
  );
}

function DeadlineCard({ item, onDismiss, onSnooze, onNavigate }: FeedCardProps) {
  const router = useRouter();
  const openStaphistorie = () => {
    if (onNavigate) onNavigate("staphistorie");
    else if (item.case_id) router.push(`/zaken/${item.case_id}?tab=staphistorie`);
  };
  return (
    <CardShell
      icon={<AlertTriangle className="h-4 w-4 text-red-600" />}
      iconClass="bg-red-100 dark:bg-red-950"
      title={item.title}
      message={item.message}
      time={formatNotificationTime(item.created_at)}
      isRead={item.is_read}
      snoozedUntil={item.snoozed_until}
      onDismiss={onDismiss}
      onSnooze={onSnooze}
      actions={
        <Button size="sm" variant="destructive" onClick={openStaphistorie}>
          Naar pipeline
        </Button>
      }
    />
  );
}
