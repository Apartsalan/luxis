"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Building2,
  CalendarDays,
  ChevronRight,
  Euro,
  Mail,
  PanelRightClose,
  PanelRightOpen,
  Phone,
  User,
} from "lucide-react";
import { useFinancialSummary } from "@/hooks/use-collections";
import { useTimeEntrySummary } from "@/hooks/use-time-entries";
import { formatCurrency, formatDate } from "@/lib/utils";
import { STATUS_LABELS, TYPE_LABELS, INTEREST_LABELS } from "../types";

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
  zaak: any;
  isIncasso: boolean;
}) {
  const [isOpen, setIsOpen] = useState(getInitialOpen);
  const { data: financials } = useFinancialSummary(
    isIncasso ? zaak.id : undefined
  );
  const { data: timeSummary } = useTimeEntrySummary({ case_id: zaak.id });

  const toggle = () => {
    const next = !isOpen;
    setIsOpen(next);
    localStorage.setItem(SIDEBAR_KEY, String(next));
  };

  const currentLawyer = zaak.parties?.find(
    (p: any) => p.role === "advocaat_wederpartij"
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
                <dt className="text-xs text-muted-foreground">Referentie</dt>
                <dd className="text-xs font-medium text-foreground font-mono truncate max-w-[120px]">
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
