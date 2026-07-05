"use client";

import Link from "next/link";
import {
  ArrowUpRight,
  CheckCircle2,
  Circle,
  Clock,
  FileText,
  Lock,
  Scale,
  Wallet,
} from "lucide-react";
import { toast } from "sonner";
import {
  useSettlement,
  useUpdateSettlementRoute,
  type SettlementRoute,
} from "@/hooks/use-collections";
import { formatCurrency } from "@/lib/utils";

type StepState = "done" | "pending" | "todo";

function StepRow({
  state,
  title,
  detail,
  action,
}: {
  state: StepState;
  title: string;
  detail?: string;
  action?: React.ReactNode;
}) {
  const Icon = state === "done" ? CheckCircle2 : state === "pending" ? Clock : Circle;
  const iconColor =
    state === "done"
      ? "text-emerald-600"
      : state === "pending"
        ? "text-amber-500"
        : "text-muted-foreground/50";
  return (
    <div className="flex items-start gap-3 py-2.5">
      <Icon className={`h-4 w-4 mt-0.5 shrink-0 ${iconColor}`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground">{title}</p>
        {detail && <p className="text-xs text-muted-foreground mt-0.5">{detail}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

const ROUTES: { value: SettlementRoute; label: string; hint: string }[] = [
  {
    value: "verrekenen",
    label: "Verrekenen",
    hint: "Honorarium van het saldo afhalen, restant uitbetalen aan de cliënt.",
  },
  {
    value: "doorbetalen",
    label: "Alles doorbetalen",
    hint: "Volledig saldo naar de cliënt, later een losse factuur sturen.",
  },
];

export function AfwikkelingPanel({
  caseId,
  onStartDisbursement,
  onStartOffset,
}: {
  caseId: string;
  onStartDisbursement: (amount: string) => void;
  onStartOffset: () => void;
}) {
  const { data } = useSettlement(caseId);
  const updateRoute = useUpdateSettlementRoute();

  // Paneel verschijnt op basis van het geld: is er saldo of een gekozen route.
  // NB: de API serialiseert Decimal als string — coerce vóór rekenen/vergelijken.
  if (!data) return null;
  const totalBalance = Number(data.total_balance);
  const available = Number(data.available);
  const payout = Number(data.suggested_payout);
  if (totalBalance <= 0 && !data.settlement_route) return null;

  const route = data.settlement_route;
  const settled = data.unsettled_reason === null;

  const hasInvoice = data.invoices.length > 0;
  const offsetApproved = data.offsets.some((o) => o.status === "approved");
  const offsetPending = data.offsets.some((o) => o.status === "pending_approval");
  const disbApproved = data.disbursements.some((d) => d.status === "approved");
  const disbPending = data.disbursements.some((d) => d.status === "pending_approval");

  const payoutBtn = (
    <button
      onClick={() => onStartDisbursement(payout.toFixed(2))}
      disabled={payout <= 0}
      className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <ArrowUpRight className="h-3.5 w-3.5" />
      Uitbetalen ({formatCurrency(payout)})
    </button>
  );
  const invoiceBtn = (
    <Link
      href={`/facturen/nieuw?case_id=${caseId}`}
      className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted transition-colors"
    >
      <FileText className="h-3.5 w-3.5" />
      Factuur maken
    </Link>
  );
  const offsetBtn = (
    <button
      onClick={onStartOffset}
      disabled={available <= 0}
      className="inline-flex items-center gap-1.5 rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-violet-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <Scale className="h-3.5 w-3.5" />
      Verrekenen
    </button>
  );

  const disbState: StepState = disbApproved ? "done" : disbPending ? "pending" : "todo";
  const invoiceState: StepState = hasInvoice ? "done" : "todo";
  const offsetState: StepState = offsetApproved ? "done" : offsetPending ? "pending" : "todo";

  return (
    <div className="rounded-xl border border-primary/20 bg-primary/5 p-5">
      <div className="flex items-center gap-2 mb-1">
        <Wallet className="h-4 w-4 text-primary" />
        <h3 className="text-sm font-semibold text-foreground">Dossier afwikkelen</h3>
      </div>
      <p className="text-xs text-muted-foreground mb-4">
        {settled
          ? "Alle derdengelden zijn afgewikkeld — het dossier kan afgesloten worden."
          : `Er staat ${formatCurrency(data.total_balance)} op de stichtingsrekening dat afgewikkeld moet worden.`}
      </p>

      {/* Routekeuze */}
      <div className="grid gap-2 sm:grid-cols-2 mb-4">
        {ROUTES.map((r) => {
          const active = route === r.value;
          return (
            <button
              key={r.value}
              onClick={() =>
                updateRoute.mutate(
                  { caseId, route: r.value },
                  { onError: (e) => toast.error(e instanceof Error ? e.message : "Mislukt") },
                )
              }
              className={`text-left rounded-lg border p-3 transition-colors ${
                active
                  ? "border-primary bg-background ring-1 ring-primary"
                  : "border-border bg-background/50 hover:border-primary/40"
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`flex h-4 w-4 items-center justify-center rounded-full border ${
                    active ? "border-primary" : "border-muted-foreground/40"
                  }`}
                >
                  {active && <span className="h-2 w-2 rounded-full bg-primary" />}
                </span>
                <span className="text-sm font-medium text-foreground">{r.label}</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1 ml-6">{r.hint}</p>
            </button>
          );
        })}
      </div>

      {/* Checklist per route */}
      {route && (
        <div className="rounded-lg border border-border bg-background divide-y divide-border px-4">
          {route === "verrekenen" ? (
            <>
              <StepRow
                state={invoiceState}
                title="Factuur naar cliënt"
                detail={
                  hasInvoice
                    ? `${data.invoices.length} factuur/facturen aangemaakt`
                    : "Reken je honorarium af met een declaratie."
                }
                action={invoiceBtn}
              />
              <StepRow
                state={offsetState}
                title="Verrekenen met het saldo"
                detail={
                  offsetPending
                    ? "Verrekening wacht op tweede goedkeuring (vier-ogen)."
                    : offsetApproved
                      ? "Verrekening geboekt."
                      : "Verreken de factuur met het derdengelden-saldo."
                }
                action={offsetBtn}
              />
              <StepRow
                state={disbState}
                title="Restant uitbetalen aan cliënt"
                detail={
                  disbPending
                    ? "Uitbetaling wacht op tweede goedkeuring (vier-ogen)."
                    : disbApproved
                      ? "Uitbetaling geboekt."
                      : `Nog uit te betalen: ${formatCurrency(payout)}.`
                }
                action={payoutBtn}
              />
            </>
          ) : (
            <>
              <StepRow
                state={disbState}
                title="Volledig saldo uitbetalen aan cliënt"
                detail={
                  disbPending
                    ? "Uitbetaling wacht op tweede goedkeuring (vier-ogen)."
                    : disbApproved
                      ? "Uitbetaling geboekt."
                      : `Uit te betalen: ${formatCurrency(payout)}.`
                }
                action={payoutBtn}
              />
              <StepRow
                state={invoiceState}
                title="Factuur naar cliënt"
                detail={
                  hasInvoice
                    ? `${data.invoices.length} factuur/facturen aangemaakt`
                    : "Stuur je declaratie; de cliënt betaalt die zelf."
                }
                action={invoiceBtn}
              />
            </>
          )}
          <StepRow
            state="todo"
            title="Dossier afsluiten"
            detail={
              settled
                ? "Klaar — sluit het dossier af op het pipeline-bord."
                : data.unsettled_reason ?? undefined
            }
            action={
              settled ? undefined : (
                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                  <Lock className="h-3.5 w-3.5" />
                  Geblokkeerd
                </span>
              )
            }
          />
        </div>
      )}
    </div>
  );
}
