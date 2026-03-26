"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Building2,
  CalendarDays,
  ChevronRight,
  Euro,
  Loader2,
  Mail,
  PanelRightClose,
  PanelRightOpen,
  Phone,
  Save,
  User,
} from "lucide-react";
import { toast } from "sonner";
import { useFinancialSummary } from "@/hooks/use-collections";
import { useTimeEntrySummary } from "@/hooks/use-time-entries";
import { useModules } from "@/hooks/use-modules";
import { useUpdateCase } from "@/hooks/use-cases";
import type { CaseDetail } from "@/hooks/use-cases";
import { useBudgetStatus } from "@/hooks/use-invoices";
import { formatCurrency, formatDate } from "@/lib/utils";
import { STATUS_LABELS, TYPE_LABELS, INTEREST_LABELS } from "../types";

const BILLING_METHOD_LABELS: Record<string, string> = {
  hourly: "Uurtarief",
  fixed_price: "Vaste prijs",
  budget_cap: "Budgetplafond",
};

// ── Billing Settings Section ────────────────────────────────────────────────

function BillingSettingsSection({ zaak }: { zaak: CaseDetail }) {
  const updateCase = useUpdateCase();
  const [editing, setEditing] = useState(false);
  const [billingMethod, setBillingMethod] = useState<string>(
    zaak.billing_method || "hourly"
  );
  const [fixedPrice, setFixedPrice] = useState(
    zaak.fixed_price_amount?.toString() || ""
  );
  const [budgetAmount, setBudgetAmount] = useState(
    zaak.budget?.toString() || ""
  );
  const [budgetHours, setBudgetHours] = useState(
    zaak.budget_hours?.toString() || ""
  );

  const handleSave = async () => {
    try {
      await updateCase.mutateAsync({
        id: zaak.id,
        data: {
          billing_method: billingMethod,
          fixed_price_amount:
            billingMethod === "fixed_price" ? (fixedPrice || null) : null,
          budget:
            billingMethod === "budget_cap" ? (budgetAmount || null) : null,
          budget_hours:
            billingMethod === "budget_cap" ? (budgetHours || null) : null,
        },
      });
      toast.success("Facturatie-instellingen opgeslagen");
      setEditing(false);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Opslaan mislukt");
    }
  };

  const inputClass =
    "w-full rounded-md border border-input bg-background px-2 py-1 text-xs focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/20 transition-colors";

  if (!editing) {
    return (
      <div className="rounded-xl border border-border bg-card p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Facturatie
          </h3>
          <button
            onClick={() => setEditing(true)}
            className="text-[10px] font-medium text-primary hover:text-primary/80 transition-colors"
          >
            Wijzigen
          </button>
        </div>
        <dl className="space-y-2.5">
          <div className="flex items-center justify-between">
            <dt className="text-xs text-muted-foreground">Methode</dt>
            <dd className="text-xs font-medium text-foreground">
              {BILLING_METHOD_LABELS[zaak.billing_method || "hourly"]}
            </dd>
          </div>
          {zaak.billing_method === "fixed_price" && zaak.fixed_price_amount != null && (
            <div className="flex items-center justify-between">
              <dt className="text-xs text-muted-foreground">Vaste prijs</dt>
              <dd className="text-xs font-medium text-foreground">
                {formatCurrency(zaak.fixed_price_amount)}
              </dd>
            </div>
          )}
          {zaak.billing_method === "budget_cap" && (
            <>
              {zaak.budget != null && (
                <div className="flex items-center justify-between">
                  <dt className="text-xs text-muted-foreground">Max bedrag</dt>
                  <dd className="text-xs font-medium text-foreground">
                    {formatCurrency(zaak.budget)}
                  </dd>
                </div>
              )}
              {zaak.budget_hours != null && (
                <div className="flex items-center justify-between">
                  <dt className="text-xs text-muted-foreground">Max uren</dt>
                  <dd className="text-xs font-medium text-foreground">
                    {zaak.budget_hours} uur
                  </dd>
                </div>
              )}
            </>
          )}
        </dl>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-primary/30 bg-card p-4">
      <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
        Facturatie
      </h3>
      <div className="space-y-3">
        {/* Radio group */}
        <div className="space-y-1.5">
          {(["hourly", "fixed_price", "budget_cap"] as const).map((method) => (
            <label
              key={method}
              className={`flex items-center gap-2 rounded-md px-2 py-1.5 text-xs cursor-pointer transition-colors ${
                billingMethod === method
                  ? "bg-primary/5 ring-1 ring-primary/20"
                  : "hover:bg-muted"
              }`}
            >
              <input
                type="radio"
                name="billing_method"
                value={method}
                checked={billingMethod === method}
                onChange={() => setBillingMethod(method)}
                className="h-3 w-3 text-primary focus:ring-primary/20"
              />
              <span className="font-medium">{BILLING_METHOD_LABELS[method]}</span>
            </label>
          ))}
        </div>

        {/* Fixed price input */}
        {billingMethod === "fixed_price" && (
          <div>
            <label className="block text-[10px] font-medium text-muted-foreground mb-1">
              Bedrag (€)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={fixedPrice}
              onChange={(e) => setFixedPrice(e.target.value)}
              placeholder="0.00"
              className={inputClass}
            />
          </div>
        )}

        {/* Budget cap inputs */}
        {billingMethod === "budget_cap" && (
          <div className="space-y-2">
            <div>
              <label className="block text-[10px] font-medium text-muted-foreground mb-1">
                Max bedrag (€)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={budgetAmount}
                onChange={(e) => setBudgetAmount(e.target.value)}
                placeholder="0.00"
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-[10px] font-medium text-muted-foreground mb-1">
                Max uren
              </label>
              <input
                type="number"
                step="0.5"
                min="0"
                value={budgetHours}
                onChange={(e) => setBudgetHours(e.target.value)}
                placeholder="0"
                className={inputClass}
              />
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-1">
          <button
            onClick={handleSave}
            disabled={updateCase.isPending}
            className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1 text-[10px] font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {updateCase.isPending ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Save className="h-3 w-3" />
            )}
            Opslaan
          </button>
          <button
            onClick={() => {
              setEditing(false);
              setBillingMethod(zaak.billing_method || "hourly");
              setFixedPrice(zaak.fixed_price_amount?.toString() || "");
              setBudgetAmount(zaak.budget?.toString() || "");
              setBudgetHours(zaak.budget_hours?.toString() || "");
            }}
            className="rounded-md px-2.5 py-1 text-[10px] font-medium text-muted-foreground hover:bg-muted transition-colors"
          >
            Annuleren
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Budget Progress Bar (LF-21) ────────────────────────────────────────────

function BudgetProgressBar({ caseId }: { caseId: string }) {
  const { data: budget } = useBudgetStatus(caseId);

  if (!budget) return null;

  const barColorClass =
    budget.status === "red"
      ? "bg-red-500"
      : budget.status === "orange"
        ? "bg-amber-500"
        : "bg-emerald-500";

  const textColorClass =
    budget.status === "red"
      ? "text-red-600 font-medium"
      : budget.status === "orange"
        ? "text-amber-600"
        : "text-muted-foreground";

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
        Budgetvoortgang
      </h3>
      <div className="space-y-3">
        {/* Amount progress */}
        {budget.budget_amount > 0 && (
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-muted-foreground">Bedrag</span>
              <span className="text-xs font-medium text-foreground tabular-nums">
                {formatCurrency(budget.used_amount)} / {formatCurrency(budget.budget_amount)}
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
              <div
                className={`h-full rounded-full ${barColorClass} transition-all`}
                style={{ width: `${Math.min(100, budget.percentage_amount)}%` }}
              />
            </div>
            <p className={`text-[10px] mt-1 text-right ${textColorClass}`}>
              {budget.percentage_amount >= 100
                ? `Budget overschreden (${Math.round(budget.percentage_amount)}%)`
                : `${Math.round(budget.percentage_amount)}% besteed`}
            </p>
          </div>
        )}

        {/* Hours progress */}
        {budget.budget_hours > 0 && (
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-muted-foreground">Uren</span>
              <span className="text-xs font-medium text-foreground tabular-nums">
                {budget.used_hours.toFixed(1)} / {budget.budget_hours} uur
              </span>
            </div>
            <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
              <div
                className={`h-full rounded-full ${barColorClass} transition-all`}
                style={{ width: `${Math.min(100, budget.percentage_hours)}%` }}
              />
            </div>
            <p className={`text-[10px] mt-1 text-right ${textColorClass}`}>
              {budget.percentage_hours >= 100
                ? `Uren overschreden (${Math.round(budget.percentage_hours)}%)`
                : `${Math.round(budget.percentage_hours)}% besteed`}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

const SIDEBAR_KEY = "luxis_sidebar_open";

function getInitialOpen(): boolean {
  if (typeof window === "undefined") return true;
  const stored = localStorage.getItem(SIDEBAR_KEY);
  return stored !== "false";
}

export default function DossierSidebar({
  zaak,
  isIncasso,
}: {
  zaak: CaseDetail;
  isIncasso: boolean;
}) {
  const [isOpen, setIsOpen] = useState(getInitialOpen);
  const { data: financials } = useFinancialSummary(
    isIncasso ? zaak.id : undefined
  );
  const { data: timeSummary } = useTimeEntrySummary({ case_id: zaak.id });
  const { hasModule } = useModules();

  const toggle = () => {
    const next = !isOpen;
    setIsOpen(next);
    localStorage.setItem(SIDEBAR_KEY, String(next));
  };

  const currentLawyer = zaak.parties?.find(
    (p) => p.role === "advocaat_wederpartij"
  );

  // OHW = billable minutes × hourly rate (from time summary)
  const ohwAmount = timeSummary?.total_amount ?? 0;
  const ohwMinutes = timeSummary?.billable_minutes ?? 0;

  if (!isOpen) {
    return (
      <button
        onClick={toggle}
        className="fixed right-4 top-20 z-30 hidden lg:flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-card shadow-sm hover:bg-muted transition-colors"
        title="Sidebar openen"
      >
        <PanelRightOpen className="h-4 w-4 text-muted-foreground" />
      </button>
    );
  }

  return (
    <aside className="hidden lg:block w-72 shrink-0">
      <div className="sticky top-4 space-y-4">
        {/* Toggle button */}
        <div className="flex justify-end">
          <button
            onClick={toggle}
            className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            title="Sidebar sluiten"
          >
            <PanelRightClose className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Dossierinfo */}
        <div className="rounded-xl border border-border bg-card p-4">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Dossierinfo
          </h3>
          <dl className="space-y-2.5">
            <div className="flex items-center justify-between">
              <dt className="text-xs text-muted-foreground">Type</dt>
              <dd className="text-xs font-medium text-foreground">
                {TYPE_LABELS[zaak.case_type] ?? zaak.case_type}
              </dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-xs text-muted-foreground">Status</dt>
              <dd className="text-xs font-medium text-foreground">
                {STATUS_LABELS[zaak.status] ?? zaak.status}
              </dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-xs text-muted-foreground">Geopend</dt>
              <dd className="text-xs font-medium text-foreground flex items-center gap-1">
                <CalendarDays className="h-3 w-3 text-muted-foreground" />
                {formatDate(zaak.date_opened)}
              </dd>
            </div>
            {zaak.debtor_type && (
              <div className="flex items-center justify-between">
                <dt className="text-xs text-muted-foreground">Debiteur</dt>
                <dd className="text-xs font-medium text-foreground uppercase">
                  {zaak.debtor_type}
                </dd>
              </div>
            )}
            {zaak.interest_type && (
              <div className="flex items-center justify-between">
                <dt className="text-xs text-muted-foreground">Rente</dt>
                <dd className="text-xs font-medium text-foreground">
                  {INTEREST_LABELS[zaak.interest_type] ?? zaak.interest_type}
                </dd>
              </div>
            )}
            {zaak.reference && (
              <div className="flex items-center justify-between">
                <dt className="text-xs font-medium text-foreground">Kenmerk cliënt</dt>
                <dd className="text-xs font-semibold text-primary font-mono truncate max-w-[140px]" title={zaak.reference}>
                  {zaak.reference}
                </dd>
              </div>
            )}
            {zaak.court_case_number && (
              <div className="flex items-center justify-between">
                <dt className="text-xs text-muted-foreground">Zaaknr.</dt>
                <dd className="text-xs font-medium text-foreground font-mono truncate max-w-[120px]">
                  {zaak.court_case_number}
                </dd>
              </div>
            )}
            {zaak.hourly_rate != null && (
              <div className="flex items-center justify-between">
                <dt className="text-xs text-muted-foreground">Uurtarief</dt>
                <dd className="text-xs font-medium text-foreground">
                  € {Number(zaak.hourly_rate).toFixed(2)}
                </dd>
              </div>
            )}
            {zaak.payment_term_days != null && (
              <div className="flex items-center justify-between">
                <dt className="text-xs text-muted-foreground">Betaaltermijn</dt>
                <dd className="text-xs font-medium text-foreground">
                  {zaak.payment_term_days} dagen
                </dd>
              </div>
            )}
          </dl>
        </div>

        {/* Client */}
        {zaak.client && (
          <div className="rounded-xl border border-border bg-card p-4">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
              Client
            </h3>
            <Link
              href={`/relaties/${zaak.client.id}`}
              className="flex items-center gap-2.5 group"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 shrink-0">
                <Building2 className="h-3.5 w-3.5 text-primary" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground group-hover:text-primary transition-colors truncate">
                  {zaak.client.name}
                </p>
              </div>
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground ml-auto shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
            </Link>
            {zaak.client.email && (
              <a
                href={`mailto:${zaak.client.email}`}
                className="mt-2 flex items-center gap-2 text-xs text-muted-foreground hover:text-primary transition-colors"
              >
                <Mail className="h-3 w-3" />
                <span className="truncate">{zaak.client.email}</span>
              </a>
            )}
          </div>
        )}

        {/* Wederpartij */}
        {zaak.opposing_party && (
          <div className="rounded-xl border border-border bg-card p-4">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
              Wederpartij
            </h3>
            <Link
              href={`/relaties/${zaak.opposing_party.id}`}
              className="flex items-center gap-2.5 group"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-50 shrink-0">
                <User className="h-3.5 w-3.5 text-amber-600" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground group-hover:text-amber-600 transition-colors truncate">
                  {zaak.opposing_party.name}
                </p>
              </div>
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground ml-auto shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
            </Link>
            {zaak.opposing_party.email && (
              <a
                href={`mailto:${zaak.opposing_party.email}`}
                className="mt-2 flex items-center gap-2 text-xs text-muted-foreground hover:text-amber-600 transition-colors"
              >
                <Mail className="h-3 w-3" />
                <span className="truncate">{zaak.opposing_party.email}</span>
              </a>
            )}
          </div>
        )}

        {/* Advocaat wederpartij */}
        {currentLawyer && (
          <div className="rounded-xl border border-border bg-card p-4">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
              Advocaat wederpartij
            </h3>
            <Link
              href={`/relaties/${currentLawyer.contact.id}`}
              className="flex items-center gap-2.5 group"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-violet-50 shrink-0">
                <User className="h-3.5 w-3.5 text-violet-600" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground group-hover:text-violet-600 transition-colors truncate">
                  {currentLawyer.contact.name}
                </p>
              </div>
              <ChevronRight className="h-3.5 w-3.5 text-muted-foreground ml-auto shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
            </Link>
            {currentLawyer.contact.email && (
              <a
                href={`mailto:${currentLawyer.contact.email}`}
                className="mt-2 flex items-center gap-2 text-xs text-muted-foreground hover:text-violet-600 transition-colors"
              >
                <Mail className="h-3 w-3" />
                <span className="truncate">{currentLawyer.contact.email}</span>
              </a>
            )}
          </div>
        )}

        {/* LF-21: Billing settings */}
        <BillingSettingsSection zaak={zaak} />

        {/* LF-21: Budget progress bar (only for budget_cap billing) */}
        {zaak.billing_method === "budget_cap" && (
          <BudgetProgressBar caseId={zaak.id} />
        )}

        {/* Financieel snapshot */}
        <div className="rounded-xl border border-border bg-card p-4">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Financieel
          </h3>
          <dl className="space-y-2.5">
            {/* OHW — altijd tonen */}
            <div className="flex items-center justify-between">
              <dt className="text-xs text-muted-foreground">OHW</dt>
              <dd className="text-xs font-medium text-foreground">
                {formatCurrency(ohwAmount)}
                {ohwMinutes > 0 && (
                  <span className="text-muted-foreground ml-1">
                    ({Math.floor(ohwMinutes / 60)}:{String(ohwMinutes % 60).padStart(2, "0")})
                  </span>
                )}
              </dd>
            </div>

            {/* G13: Budget progress bar — only when budget module enabled and budget set */}
            {hasModule("budget") && zaak.budget != null && zaak.budget > 0 && (() => {
              const spent = ohwAmount;
              const budget = zaak.budget as number;
              const pct = Math.round((spent / budget) * 100);
              const barColor = pct >= 100 ? "bg-red-500" : pct >= 80 ? "bg-amber-500" : "bg-emerald-500";
              return (
                <div className="pt-1">
                  <div className="flex items-center justify-between mb-1">
                    <dt className="text-xs text-muted-foreground">Budget</dt>
                    <dd className="text-xs font-medium text-foreground">
                      {formatCurrency(spent)} / {formatCurrency(budget)}
                    </dd>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                    <div
                      className={`h-full rounded-full ${barColor} transition-all`}
                      style={{ width: `${Math.min(100, pct)}%` }}
                    />
                  </div>
                  <p className={`text-[10px] mt-1 text-right ${
                    pct >= 100 ? "text-red-600 font-medium" : pct >= 80 ? "text-amber-600" : "text-muted-foreground"
                  }`}>
                    {pct >= 100
                      ? `Budget overschreden (${pct}%)`
                      : `${pct}% besteed`}
                  </p>
                </div>
              );
            })()}

            {/* Incasso financials */}
            {isIncasso && financials && (
              <>
                <div className="flex items-center justify-between">
                  <dt className="text-xs text-muted-foreground">Hoofdsom</dt>
                  <dd className="text-xs font-medium text-foreground">
                    {formatCurrency(financials.total_principal)}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-xs text-muted-foreground">Betaald</dt>
                  <dd className="text-xs font-medium text-emerald-600">
                    {formatCurrency(financials.total_paid)}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-xs text-muted-foreground">Openstaand</dt>
                  <dd className="text-xs font-medium text-foreground">
                    {formatCurrency(financials.total_outstanding)}
                  </dd>
                </div>
                {financials.derdengelden_balance > 0 && (
                  <div className="flex items-center justify-between">
                    <dt className="text-xs text-muted-foreground">Derdengelden</dt>
                    <dd className="text-xs font-medium text-blue-600">
                      {formatCurrency(financials.derdengelden_balance)}
                    </dd>
                  </div>
                )}
                {/* Progress bar */}
                {financials.grand_total > 0 && (
                  <div className="pt-1">
                    <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                      <div
                        className="h-full rounded-full bg-emerald-500 transition-all"
                        style={{
                          width: `${Math.min(100, (financials.total_paid / financials.grand_total) * 100)}%`,
                        }}
                      />
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-1 text-right">
                      {Math.round((financials.total_paid / financials.grand_total) * 100)}% geïnd
                    </p>
                  </div>
                )}
              </>
            )}

            {/* Non-incasso: basic financials from zaak */}
            {!isIncasso && (
              <>
                <div className="flex items-center justify-between">
                  <dt className="text-xs text-muted-foreground">Hoofdsom</dt>
                  <dd className="text-xs font-medium text-foreground">
                    {formatCurrency(zaak.total_principal)}
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-xs text-muted-foreground">Betaald</dt>
                  <dd className="text-xs font-medium text-emerald-600">
                    {formatCurrency(zaak.total_paid)}
                  </dd>
                </div>
              </>
            )}
          </dl>
        </div>
      </div>
    </aside>
  );
}
