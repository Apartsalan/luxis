"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Check, Clock, Plus, Trash2, Search } from "lucide-react";
import { toast } from "sonner";
import { useCreateInvoice, useCreateVoorschotnota, useAdvanceBalance, useInvoices, useBudgetStatus, useProvisie } from "@/hooks/use-invoices";
import { useDerdengeldenBalance } from "@/hooks/use-collections";
import { useRelations } from "@/hooks/use-relations";
import { useCases, useCase } from "@/hooks/use-cases";
import type { CaseSummary } from "@/hooks/use-cases";
import type { Contact } from "@/hooks/use-relations";
import { useUnbilledTimeEntries, type TimeEntry } from "@/hooks/use-time-entries";
import { useExpenses, type Expense } from "@/hooks/use-expenses";
import { formatCurrency, formatDateShort } from "@/lib/utils";
import { IncassoKostenPanel } from "@/components/IncassoKostenPanel";

interface LineItem {
  description: string;
  quantity: string;
  unit_price: string;
  btw_percentage: string;
  time_entry_id?: string;
  expense_id?: string;
}

export default function NieuweFactuurPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedCaseId = searchParams.get("case_id") || "";
  const preselectedType = searchParams.get("type") || "factuur";
  const isProvisie = searchParams.get("provisie") === "true";
  const createInvoice = useCreateInvoice();
  const createVoorschotnota = useCreateVoorschotnota();

  // LF-21: Invoice type toggle
  const [invoiceType, setInvoiceType] = useState<"factuur" | "voorschotnota">(
    preselectedType === "voorschotnota" ? "voorschotnota" : "factuur"
  );

  // LF-21: Voorschotnota form state
  const [voorschotForm, setVoorschotForm] = useState({
    amount: "",
    description: "",
    settlement_type: "tussentijds" as "tussentijds" | "bij_sluiting",
  });

  // LF-21: Voorschot verrekening state
  const [verrekenEnabled, setVerrekenEnabled] = useState(false);
  const [verrekenAmount, setVerrekenAmount] = useState("");

  // DF-06: BTW mode (preset dropdown + custom option)
  const [btwMode, setBtwMode] = useState<"21" | "0" | "custom">("21");

  const [form, setForm] = useState({
    contact_id: "",
    case_id: preselectedCaseId,
    invoice_date: new Date().toISOString().split("T")[0],
    due_date: new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
    btw_percentage: "21.00",
    reference: "",
    notes: "",
  });

  const [lines, setLines] = useState<LineItem[]>([
    { description: "", quantity: "1", unit_price: "", btw_percentage: "21.00" },
  ]);

  const [contactSearch, setContactSearch] = useState("");
  const [caseSearch, setCaseSearch] = useState("");
  const [showContactResults, setShowContactResults] = useState(false);
  const [showCaseResults, setShowCaseResults] = useState(false);
  const [selectedContactName, setSelectedContactName] = useState("");
  const [selectedCaseNumber, setSelectedCaseNumber] = useState("");
  const [showTimeEntries, setShowTimeEntries] = useState(false);
  const [showExpenses, setShowExpenses] = useState(false);
  const [selectedTimeEntryIds, setSelectedTimeEntryIds] = useState<Set<string>>(new Set());
  const [error, setError] = useState("");
  const [invoiceFieldErrors, setInvoiceFieldErrors] = useState<Record<string, string>>({});

  // UX-16: Warn on unsaved changes
  const formDirty = form.contact_id || form.case_id !== preselectedCaseId || lines.some(l => l.description || l.unit_price);
  useEffect(() => {
    if (!formDirty) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [formDirty]);

  // Pre-fill from case_id URL parameter
  const { data: preselectedCase } = useCase(preselectedCaseId || undefined);

  // DF-05: Provisie pre-fill
  const { data: provisieData } = useProvisie(
    isProvisie && preselectedCaseId ? preselectedCaseId : undefined
  );

  useEffect(() => {
    if (preselectedCase && preselectedCaseId) {
      setSelectedCaseNumber(preselectedCase.case_number);
      if (preselectedCase.client) {
        setSelectedContactName(preselectedCase.client.name);
        setForm((prev) => ({ ...prev, contact_id: preselectedCase.client!.id }));
      }
    }
  }, [preselectedCase, preselectedCaseId]);

  // DF-05: Pre-fill provisie line when provisie data is loaded
  // Skip for incasso cases — the IncassoKostenPanel handles provisie there
  useEffect(() => {
    if (isProvisie && provisieData && provisieData.total_fee > 0 && preselectedCase?.case_type !== "incasso") {
      const feeAmount = provisieData.minimum_fee > 0 && provisieData.total_fee < provisieData.minimum_fee
        ? provisieData.minimum_fee
        : provisieData.total_fee;
      setLines([
        {
          description: `Provisie ${provisieData.provisie_percentage}% over geïnd bedrag (${formatCurrency(provisieData.collected_amount)})`,
          quantity: "1",
          unit_price: Number(feeAmount).toFixed(2),
          btw_percentage: "21.00",
        },
        ...(provisieData.fixed_case_costs > 0
          ? [{
              description: "Vaste dossierkosten",
              quantity: "1",
              unit_price: Number(provisieData.fixed_case_costs).toFixed(2),
              btw_percentage: "21.00",
            }]
          : []),
      ]);
    }
  }, [isProvisie, provisieData, preselectedCase]);

  const { data: contactResults } = useRelations({
    search: contactSearch || undefined,
    per_page: 5,
  });
  const { data: caseResults } = useCases({
    search: caseSearch || undefined,
    per_page: 5,
  });

  // Unbilled time entries for import (only billable + uninvoiced)
  const { data: unbilledEntries } = useUnbilledTimeEntries(
    form.case_id || undefined
  );

  // Filter out entries already imported as lines
  const importedTimeEntryIds = new Set(
    lines.filter((l) => l.time_entry_id).map((l) => l.time_entry_id!)
  );
  const availableEntries = (unbilledEntries ?? []).filter(
    (e) => !importedTimeEntryIds.has(e.id)
  );

  // Uninvoiced expenses for import
  const { data: expenses } = useExpenses({
    case_id: form.case_id || undefined,
    uninvoiced_only: true,
    billable_only: true,
  });

  // LF-21: Advance balance for voorschot verrekening
  const { data: advanceBalance } = useAdvanceBalance(
    invoiceType === "factuur" && form.case_id ? form.case_id : undefined
  );

  // DF-07: Context panel data — existing invoices, derdengelden, budget
  const { data: caseInvoices } = useInvoices({
    case_id: form.case_id || undefined,
    per_page: 100,
  });
  const { data: derdengeldenBalance } = useDerdengeldenBalance(
    form.case_id || undefined
  );
  const { data: budgetStatus } = useBudgetStatus(
    form.case_id || undefined
  );

  const updateField = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (invoiceFieldErrors[field]) {
      setInvoiceFieldErrors((prev) => { const n = { ...prev }; delete n[field]; return n; });
    }
  };

  const updateLine = (index: number, field: keyof LineItem, value: string) => {
    setLines((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  const addLine = () => {
    setLines((prev) => [
      ...prev,
      { description: "", quantity: "1", unit_price: "", btw_percentage: "21.00" },
    ]);
  };

  const removeLine = (index: number) => {
    setLines((prev) => prev.filter((_, i) => i !== index));
  };

  // Toggle time entry selection
  const toggleTimeEntry = (entryId: string) => {
    setSelectedTimeEntryIds((prev) => {
      const next = new Set(prev);
      if (next.has(entryId)) {
        next.delete(entryId);
      } else {
        next.add(entryId);
      }
      return next;
    });
  };

  // Select/deselect all
  const toggleAllTimeEntries = () => {
    if (selectedTimeEntryIds.size === availableEntries.length) {
      setSelectedTimeEntryIds(new Set());
    } else {
      setSelectedTimeEntryIds(new Set(availableEntries.map((e) => e.id)));
    }
  };

  // Batch import selected time entries
  const importSelectedTimeEntries = () => {
    const selected = availableEntries.filter((e) =>
      selectedTimeEntryIds.has(e.id)
    );
    if (selected.length === 0) return;

    const newLines: LineItem[] = selected.map((entry) => {
      const hours = entry.duration_minutes / 60;
      const rate = Number(entry.hourly_rate ?? 0);
      return {
        description: entry.description || "Juridische werkzaamheden",
        quantity: hours.toFixed(2),
        unit_price: rate.toFixed(2),
        btw_percentage: form.btw_percentage,
        time_entry_id: entry.id,
      };
    });

    setLines((prev) => [...prev, ...newLines]);
    setSelectedTimeEntryIds(new Set());
    setShowTimeEntries(false);
    toast.success(`${selected.length} uur${selected.length > 1 ? " " : ""}registratie${selected.length > 1 ? "s" : ""} geimporteerd`);
  };

  const importExpense = (expense: {
    id: string;
    description: string;
    amount: number;
    tax_type?: string;
  }) => {
    // DF2-03: Auto-set BTW based on expense tax_type
    const btw = expense.tax_type === "onbelast" || expense.tax_type === "vrijgesteld"
      ? "0.00" : "21.00";
    setLines((prev) => [
      ...prev,
      {
        description: expense.description,
        quantity: "1",
        unit_price: Number(expense.amount).toFixed(2),
        btw_percentage: btw,
        expense_id: expense.id,
      },
    ]);
    setShowExpenses(false);
  };

  // DF2-03: Calculate totals with per-line VAT
  const subtotal = lines.reduce((sum, line) => {
    const qty = parseFloat(line.quantity) || 0;
    const price = parseFloat(line.unit_price) || 0;
    return sum + qty * price;
  }, 0);

  // Group by BTW rate and calculate per-group BTW
  const btwGroups = new Map<string, { subtotal: number; btw: number }>();
  for (const line of lines) {
    const qty = parseFloat(line.quantity) || 0;
    const price = parseFloat(line.unit_price) || 0;
    const lineTotal = qty * price;
    const pct = line.btw_percentage || "21.00";
    const existing = btwGroups.get(pct) || { subtotal: 0, btw: 0 };
    existing.subtotal += lineTotal;
    btwGroups.set(pct, existing);
  }
  // Calculate BTW per group (round per group, not per line)
  let btwAmount = 0;
  for (const [pct, group] of btwGroups) {
    group.btw = Math.round(group.subtotal * (parseFloat(pct) / 100) * 100) / 100;
    btwAmount += group.btw;
  }
  const total = subtotal + btwAmount;

  // Calculate selected time entries total for preview
  const selectedTotal = availableEntries
    .filter((e) => selectedTimeEntryIds.has(e.id))
    .reduce((sum, e) => {
      const hours = e.duration_minutes / 60;
      return sum + hours * (e.hourly_rate ?? 0);
    }, 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const errors: Record<string, string> = {};

    if (!form.contact_id) {
      errors.contact_id = "Selecteer een relatie";
    }

    // LF-21: Voorschotnota submit
    if (invoiceType === "voorschotnota") {
      if (!form.case_id) {
        errors.case_id = "Selecteer een dossier voor de voorschotnota";
      }
      const amount = parseFloat(voorschotForm.amount);
      if (!amount || amount <= 0) {
        errors.voorschot_amount = "Voer een geldig bedrag in";
      }
      if (Object.keys(errors).length > 0) {
        setInvoiceFieldErrors(errors);
        return;
      }
      try {
        const result = await createVoorschotnota.mutateAsync({
          case_id: form.case_id,
          contact_id: form.contact_id,
          amount: voorschotForm.amount,
          description: voorschotForm.description?.trim() || undefined,
          invoice_date: form.invoice_date,
          due_date: form.due_date,
          btw_percentage: form.btw_percentage,
          settlement_type: voorschotForm.settlement_type,
        });
        toast.success("Voorschotnota aangemaakt");
        router.push(preselectedCaseId ? `/zaken/${preselectedCaseId}` : `/facturen/${result.id}`);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Er ging iets mis");
      }
      return;
    }

    // Regular invoice submit
    const validLines = lines.filter(
      (l) => l.description && parseFloat(l.unit_price) > 0
    );

    // Add voorschot verrekening as negative line
    const allLines = [...validLines];
    if (verrekenEnabled && verrekenAmount) {
      const offsetAmount = parseFloat(verrekenAmount);
      if (offsetAmount > 0) {
        allLines.push({
          description: "Verrekening voorschot",
          quantity: "1",
          unit_price: (-offsetAmount).toFixed(2),
          btw_percentage: form.btw_percentage,
        });
      }
    }

    if (allLines.filter((l) => l.description && parseFloat(l.unit_price) > 0).length === 0 && !verrekenEnabled) {
      errors.lines = "Voeg minimaal een factuurregel toe";
    }

    if (Object.keys(errors).length > 0) {
      setInvoiceFieldErrors(errors);
      return;
    }

    try {
      const result = await createInvoice.mutateAsync({
        contact_id: form.contact_id,
        case_id: form.case_id || null,
        invoice_date: form.invoice_date,
        due_date: form.due_date,
        btw_percentage: form.btw_percentage,
        reference: form.reference?.trim() || null,
        notes: form.notes?.trim() || null,
        lines: allLines.map((l) => ({
          description: l.description,
          quantity: l.quantity || "1",
          unit_price: l.unit_price,
          btw_percentage: l.btw_percentage || "21.00",
          time_entry_id: l.time_entry_id || null,
          expense_id: l.expense_id || null,
        })),
      });
      toast.success("Factuur aangemaakt");
      router.push(preselectedCaseId ? `/zaken/${preselectedCaseId}` : `/facturen/${result.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Er ging iets mis");
    }
  };

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="mx-auto max-w-3xl space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <Link
          href="/facturen"
          className="rounded-lg p-2 hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-muted-foreground" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {invoiceType === "voorschotnota" ? "Nieuwe voorschotnota" : "Nieuwe factuur"}
          </h1>
          <p className="text-sm text-muted-foreground">
            {invoiceType === "voorschotnota"
              ? "Maak een voorschotnota aan voor een dossier"
              : "Maak een nieuwe factuur aan"}
          </p>
        </div>
      </div>

      {/* LF-21: Type selector */}
      <div className="flex gap-1 rounded-lg border border-border bg-muted/30 p-1 w-fit">
        <button
          type="button"
          onClick={() => setInvoiceType("factuur")}
          className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            invoiceType === "factuur"
              ? "bg-card text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Factuur
        </button>
        <button
          type="button"
          onClick={() => setInvoiceType("voorschotnota")}
          className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            invoiceType === "voorschotnota"
              ? "bg-card text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Voorschotnota
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Invoice details */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          <h2 className="text-base font-semibold text-foreground">
            Factuurgegevens
          </h2>

          {/* Contact search */}
          <div className="relative">
            <label htmlFor="inv-contact" className="block text-sm font-medium text-foreground">
              Relatie *
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground mt-0.75" />
              <input
                id="inv-contact"
                type="text"
                placeholder="Zoek relatie..."
                value={selectedContactName || contactSearch}
                onChange={(e) => {
                  setContactSearch(e.target.value);
                  setSelectedContactName("");
                  updateField("contact_id", "");
                  setInvoiceFieldErrors((prev) => ({ ...prev, contact_id: "" }));
                  setShowContactResults(true);
                }}
                onFocus={() => setShowContactResults(true)}
                className={`mt-1.5 w-full rounded-lg border bg-background pl-10 pr-3 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 transition-colors ${
                  invoiceFieldErrors.contact_id
                    ? "border-destructive focus:border-destructive focus:ring-destructive/20"
                    : "border-input focus:border-primary focus:ring-primary/20"
                }`}
              />
            </div>
            {invoiceFieldErrors.contact_id && (
              <p className="mt-1 text-xs text-destructive">{invoiceFieldErrors.contact_id}</p>
            )}
            {showContactResults &&
              contactSearch &&
              contactResults?.items &&
              contactResults.items.length > 0 && (
                <div className="absolute z-10 mt-1 w-full rounded-lg border border-border bg-card shadow-lg">
                  {contactResults.items.map((c: Contact) => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => {
                        updateField("contact_id", c.id);
                        setSelectedContactName(c.name);
                        setContactSearch("");
                        setShowContactResults(false);
                        setInvoiceFieldErrors((prev) => ({ ...prev, contact_id: "" }));
                      }}
                      className="flex w-full items-center px-4 py-2.5 text-sm hover:bg-muted transition-colors first:rounded-t-lg last:rounded-b-lg"
                    >
                      <span className="font-medium">{c.name}</span>
                      <span className="ml-2 text-xs text-muted-foreground">
                        {c.contact_type === "company" ? "Bedrijf" : "Persoon"}
                      </span>
                    </button>
                  ))}
                </div>
              )}
          </div>

          {/* Case search */}
          <div className="relative">
            <label htmlFor="inv-case" className="block text-sm font-medium text-foreground">
              Dossier {invoiceType === "voorschotnota" ? "*" : "(optioneel)"}
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground mt-0.75" />
              <input
                id="inv-case"
                type="text"
                placeholder="Zoek dossier..."
                value={selectedCaseNumber || caseSearch}
                onChange={(e) => {
                  setCaseSearch(e.target.value);
                  setSelectedCaseNumber("");
                  updateField("case_id", "");
                  setShowCaseResults(true);
                }}
                onFocus={() => setShowCaseResults(true)}
                className={`${inputClass} pl-10 ${invoiceFieldErrors.case_id ? "border-destructive ring-1 ring-destructive/30" : ""}`}
              />
            </div>
            {invoiceFieldErrors.case_id && (
              <p className="mt-1 text-xs text-destructive">{invoiceFieldErrors.case_id}</p>
            )}
            {showCaseResults &&
              caseSearch &&
              caseResults?.items &&
              caseResults.items.length > 0 && (
                <div className="absolute z-10 mt-1 w-full rounded-lg border border-border bg-card shadow-lg">
                  {caseResults.items.map((c: CaseSummary) => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => {
                        updateField("case_id", c.id);
                        setSelectedCaseNumber(c.case_number);
                        setCaseSearch("");
                        setShowCaseResults(false);
                      }}
                      className="flex w-full items-center gap-2 px-4 py-2.5 text-sm hover:bg-muted transition-colors first:rounded-t-lg last:rounded-b-lg"
                    >
                      <span className="font-mono font-medium">
                        {c.case_number}
                      </span>
                      {c.description && (
                        <span className="text-xs text-muted-foreground truncate">
                          {c.description}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              )}
          </div>

          {/* DF-07: Context panel — al gefactureerd + derdengelden + budget */}
          {form.case_id && (caseInvoices?.items?.length || derdengeldenBalance || budgetStatus?.budget_amount) && (
            <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-4 space-y-2">
              <p className="text-xs font-medium text-blue-800 uppercase tracking-wider">
                Dossier overzicht
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {caseInvoices?.items && (
                  <div>
                    <p className="text-xs text-muted-foreground">Al gefactureerd</p>
                    <p className="text-sm font-semibold tabular-nums">
                      {formatCurrency(
                        caseInvoices.items
                          .filter((inv) => inv.status !== "cancelled")
                          .reduce((sum, inv) => sum + Number(inv.total), 0)
                      )}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {caseInvoices.items.filter((inv) => inv.status !== "cancelled").length} facturen
                    </p>
                  </div>
                )}
                {derdengeldenBalance && (
                  <div>
                    <p className="text-xs text-muted-foreground">Derdengelden saldo</p>
                    <p className="text-sm font-semibold tabular-nums">
                      {formatCurrency(derdengeldenBalance.total_balance)}
                    </p>
                  </div>
                )}
                {budgetStatus && budgetStatus.budget_amount && (
                  <div>
                    <p className="text-xs text-muted-foreground">Budget verbruikt</p>
                    <p className="text-sm font-semibold tabular-nums">
                      {formatCurrency(Number(budgetStatus.used_amount))} / {formatCurrency(Number(budgetStatus.budget_amount))}
                    </p>
                    {budgetStatus.percentage_amount && (
                      <p className={`text-xs font-medium ${
                        budgetStatus.status === "red" ? "text-red-600" :
                        budgetStatus.status === "orange" ? "text-amber-600" :
                        "text-emerald-600"
                      }`}>
                        {Number(budgetStatus.percentage_amount).toFixed(0)}%
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="inv-invoice-date" className="block text-sm font-medium text-foreground">
                Factuurdatum
              </label>
              <input
                id="inv-invoice-date"
                type="date"
                value={form.invoice_date}
                onChange={(e) => updateField("invoice_date", e.target.value)}
                className={inputClass}
                required
              />
            </div>
            <div>
              <label htmlFor="inv-due-date" className="block text-sm font-medium text-foreground">
                Vervaldatum
              </label>
              <input
                id="inv-due-date"
                type="date"
                value={form.due_date}
                onChange={(e) => updateField("due_date", e.target.value)}
                className={inputClass}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="inv-btw" className="block text-sm font-medium text-foreground">
                BTW
              </label>
              <select
                id="inv-btw"
                value={btwMode}
                onChange={(e) => {
                  const mode = e.target.value as "21" | "0" | "custom";
                  setBtwMode(mode);
                  if (mode === "21") updateField("btw_percentage", "21.00");
                  else if (mode === "0") updateField("btw_percentage", "0.00");
                }}
                className={inputClass}
              >
                <option value="21">21% (standaard)</option>
                <option value="0">0% (vrijgesteld)</option>
                <option value="custom">Aangepast percentage</option>
              </select>
              {btwMode === "custom" && (
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  value={form.btw_percentage}
                  onChange={(e) => updateField("btw_percentage", e.target.value)}
                  placeholder="Bijv. 9.00"
                  className={`${inputClass} mt-2`}
                />
              )}
            </div>
            <div>
              <label htmlFor="inv-reference" className="block text-sm font-medium text-foreground">
                Referentie
              </label>
              <input
                id="inv-reference"
                type="text"
                placeholder="Bijv. kenmerk opdrachtgever"
                value={form.reference}
                onChange={(e) => updateField("reference", e.target.value)}
                className={inputClass}
              />
            </div>
          </div>

          <div>
            <label htmlFor="inv-notes" className="block text-sm font-medium text-foreground">
              Opmerkingen
            </label>
            <textarea
              id="inv-notes"
              rows={2}
              placeholder="Optionele opmerkingen op de factuur"
              value={form.notes}
              onChange={(e) => updateField("notes", e.target.value)}
              className={inputClass}
            />
          </div>
        </div>

        {/* LF-21: Voorschotnota — simplified fields */}
        {invoiceType === "voorschotnota" && (
          <div className="rounded-xl border border-border bg-card p-6 space-y-4">
            <h2 className="text-base font-semibold text-foreground">
              Voorschotbedrag
            </h2>
            {/* DF2-04: Hours-based calculation */}
            {preselectedCase?.hourly_rate && Number(preselectedCase.hourly_rate) > 0 && (
              <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-3">
                <label htmlFor="inv-voorschot-hours" className="block text-sm font-medium text-foreground">
                  Berekenen op basis van uren
                </label>
                <div className="flex items-center gap-3">
                  <input
                    id="inv-voorschot-hours"
                    type="number"
                    step="0.5"
                    min="0"
                    placeholder="Aantal uur"
                    className={`${inputClass} w-32`}
                    onChange={(e) => {
                      const hours = parseFloat(e.target.value);
                      const rate = Number(preselectedCase.hourly_rate);
                      if (hours > 0 && rate > 0) {
                        setVoorschotForm((p) => ({
                          ...p,
                          amount: (hours * rate).toFixed(2),
                        }));
                      }
                    }}
                  />
                  <span className="text-sm text-muted-foreground">
                    × {formatCurrency(Number(preselectedCase.hourly_rate))}/uur
                  </span>
                </div>
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="inv-voorschot-amount" className="block text-sm font-medium text-foreground">
                  Bedrag (excl. BTW) *
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm mt-0.75">€</span>
                  <input
                    id="inv-voorschot-amount"
                    type="number"
                    step="0.01"
                    min="0"
                    value={voorschotForm.amount}
                    onChange={(e) =>
                      setVoorschotForm((p) => ({ ...p, amount: e.target.value }))
                    }
                    placeholder="0.00"
                    className={`${inputClass} pl-8 ${invoiceFieldErrors.voorschot_amount ? "border-destructive ring-1 ring-destructive/30" : ""}`}
                  />
                </div>
                {invoiceFieldErrors.voorschot_amount && (
                  <p className="mt-1 text-xs text-destructive">{invoiceFieldErrors.voorschot_amount}</p>
                )}
              </div>
              <div className="flex items-end">
                {voorschotForm.amount && (
                  <div className="text-sm text-muted-foreground">
                    <span>Incl. BTW: </span>
                    <span className="font-medium text-foreground tabular-nums">
                      {formatCurrency(
                        (parseFloat(voorschotForm.amount) || 0) *
                          (1 + (parseFloat(form.btw_percentage) || 0) / 100)
                      )}
                    </span>
                  </div>
                )}
              </div>
            </div>
            <div>
              <label htmlFor="inv-voorschot-description" className="block text-sm font-medium text-foreground">
                Omschrijving (optioneel)
              </label>
              <input
                id="inv-voorschot-description"
                type="text"
                value={voorschotForm.description}
                onChange={(e) =>
                  setVoorschotForm((p) => ({ ...p, description: e.target.value }))
                }
                placeholder="Bijv. Voorschot juridische werkzaamheden"
                className={inputClass}
              />
            </div>

            {/* DF-13: Verrekening type */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Verrekening
              </label>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setVoorschotForm((p) => ({ ...p, settlement_type: "tussentijds" }))}
                  className={`flex-1 rounded-lg border px-4 py-3 text-left transition-colors ${
                    voorschotForm.settlement_type === "tussentijds"
                      ? "border-primary bg-primary/5 ring-1 ring-primary/30"
                      : "border-border bg-background hover:bg-muted"
                  }`}
                >
                  <div className="text-sm font-medium text-foreground">Tussentijds</div>
                  <div className="mt-0.5 text-xs text-muted-foreground">
                    Voorschot wordt bij elke factuur verrekend
                  </div>
                </button>
                <button
                  type="button"
                  onClick={() => setVoorschotForm((p) => ({ ...p, settlement_type: "bij_sluiting" }))}
                  className={`flex-1 rounded-lg border px-4 py-3 text-left transition-colors ${
                    voorschotForm.settlement_type === "bij_sluiting"
                      ? "border-primary bg-primary/5 ring-1 ring-primary/30"
                      : "border-border bg-background hover:bg-muted"
                  }`}
                >
                  <div className="text-sm font-medium text-foreground">Bij sluiting</div>
                  <div className="mt-0.5 text-xs text-muted-foreground">
                    Voorschot wordt bij afsluiting dossier verrekend
                  </div>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Incasso kosten panel — DF117-05 (Lisanne demo 2026-04-07): toon altijd als
            er een case is gekozen. Het paneel zelf verbergt zichzelf als er geen
            relevante incasso-instellingen zijn (geen vordering, geen provisie). */}
        {invoiceType === "factuur" && form.case_id && (
          <IncassoKostenPanel
            caseId={form.case_id}
            onAddLine={(line) => {
              setLines((prev) => [...prev.filter(l => l.description || l.unit_price), line]);
            }}
          />
        )}

        {/* Invoice lines — only for regular invoices */}
        {invoiceType === "factuur" && (<>
        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-foreground">
                Factuurregels
              </h2>
              {invoiceFieldErrors.lines && (
                <p className="text-xs text-destructive mt-1">{invoiceFieldErrors.lines}</p>
              )}
            </div>
            <div className="flex gap-2">
              {form.case_id && (
                <>
                  <button
                    type="button"
                    onClick={() => {
                      setShowTimeEntries(!showTimeEntries);
                      setShowExpenses(false);
                      setSelectedTimeEntryIds(new Set());
                    }}
                    className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                      showTimeEntries
                        ? "border-primary bg-primary/5 text-primary"
                        : "border-border text-muted-foreground hover:bg-muted"
                    }`}
                  >
                    <Clock className="h-3.5 w-3.5" />
                    Importeer uren
                    {availableEntries.length > 0 && (
                      <span className="ml-1 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-primary/10 px-1 text-[10px] font-semibold text-primary">
                        {availableEntries.length}
                      </span>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowExpenses(!showExpenses);
                      setShowTimeEntries(false);
                    }}
                    className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                      showExpenses
                        ? "border-primary bg-primary/5 text-primary"
                        : "border-border text-muted-foreground hover:bg-muted"
                    }`}
                  >
                    <Plus className="h-3.5 w-3.5" />
                    Importeer verschotten
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Time entries import panel — batch with checkboxes */}
          {showTimeEntries && (
            <div className="rounded-lg border border-primary/20 bg-primary/[0.02] p-4 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  Onbefactureerde uren
                </p>
                {availableEntries.length > 0 && (
                  <button
                    type="button"
                    onClick={toggleAllTimeEntries}
                    className="text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                  >
                    {selectedTimeEntryIds.size === availableEntries.length
                      ? "Deselecteer alles"
                      : "Alles selecteren"}
                  </button>
                )}
              </div>

              {availableEntries.length === 0 ? (
                <div className="rounded-md border border-dashed border-border py-6 text-center">
                  <Clock className="mx-auto h-6 w-6 text-muted-foreground/30" />
                  <p className="mt-1.5 text-sm text-muted-foreground">
                    Geen onbefactureerde uren voor dit dossier
                  </p>
                </div>
              ) : (
                <>
                  <div className="space-y-1">
                    {availableEntries.map((entry) => {
                      const hours = entry.duration_minutes / 60;
                      const amount = hours * Number(entry.hourly_rate ?? 0);
                      const isSelected = selectedTimeEntryIds.has(entry.id);

                      return (
                        <label
                          key={entry.id}
                          className={`flex w-full cursor-pointer items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors ${
                            isSelected
                              ? "bg-primary/5 ring-1 ring-primary/20"
                              : "hover:bg-muted"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => toggleTimeEntry(entry.id)}
                            className="h-4 w-4 rounded border-input text-primary focus:ring-primary/20"
                          />
                          <div className="flex flex-1 items-center justify-between min-w-0">
                            <div className="min-w-0 flex-1">
                              <span className="truncate block">
                                {entry.description || "Werkzaamheden"}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {formatDateShort(entry.date)} · {hours.toFixed(1)}u
                                {entry.user?.full_name && ` · ${entry.user.full_name}`}
                              </span>
                            </div>
                            <span className="ml-3 font-medium tabular-nums text-foreground">
                              {entry.hourly_rate ? formatCurrency(amount) : "-"}
                            </span>
                          </div>
                        </label>
                      );
                    })}
                  </div>

                  {/* Batch import footer */}
                  <div className="flex items-center justify-between border-t border-border pt-3">
                    <div className="text-sm text-muted-foreground">
                      {selectedTimeEntryIds.size > 0 ? (
                        <>
                          <span className="font-medium text-foreground">
                            {selectedTimeEntryIds.size}
                          </span>{" "}
                          geselecteerd · subtotaal{" "}
                          <span className="font-medium text-foreground tabular-nums">
                            {formatCurrency(selectedTotal)}
                          </span>
                        </>
                      ) : (
                        "Selecteer uren om te importeren"
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={importSelectedTimeEntries}
                      disabled={selectedTimeEntryIds.size === 0}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      <Check className="h-3.5 w-3.5" />
                      Importeer ({selectedTimeEntryIds.size})
                    </button>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Expenses import panel */}
          {showExpenses && expenses && expenses.length > 0 && (
            <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Onbefactureerde verschotten
              </p>
              {expenses.map((expense: Expense) => (
                <button
                  key={expense.id}
                  type="button"
                  onClick={() => importExpense(expense)}
                  className="flex w-full items-center justify-between rounded-md px-3 py-2 text-sm hover:bg-muted transition-colors"
                >
                  <span className="truncate">{expense.description}</span>
                  <span className="text-muted-foreground tabular-nums">
                    {formatCurrency(expense.amount)}
                  </span>
                </button>
              ))}
            </div>
          )}

          {showExpenses && (!expenses || expenses.length === 0) && (
            <div className="rounded-lg border border-dashed border-border py-6 text-center">
              <p className="text-sm text-muted-foreground">
                Geen onbefactureerde verschotten voor dit dossier
              </p>
            </div>
          )}

          {/* Line items table */}
          <div className="space-y-3">
            {/* Header */}
            <div className="grid grid-cols-12 gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground px-1">
              <div className="col-span-4">Omschrijving</div>
              <div className="col-span-2">Aantal</div>
              <div className="col-span-2">Prijs</div>
              <div className="col-span-1">BTW</div>
              <div className="col-span-1 text-right">Totaal</div>
              <div className="col-span-1" />
            </div>

            {lines.map((line, index) => {
              const qty = parseFloat(line.quantity) || 0;
              const price = parseFloat(line.unit_price) || 0;
              const lineTotal = qty * price;

              return (
                <div key={index} className="grid grid-cols-12 gap-2 items-start">
                  <div className="col-span-4">
                    <input
                      type="text"
                      placeholder="Omschrijving"
                      value={line.description}
                      onChange={(e) =>
                        updateLine(index, "description", e.target.value)
                      }
                      className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                    />
                  </div>
                  <div className="col-span-2">
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="1"
                      value={line.quantity}
                      onChange={(e) =>
                        updateLine(index, "quantity", e.target.value)
                      }
                      className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm tabular-nums focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                    />
                  </div>
                  <div className="col-span-2">
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      value={line.unit_price}
                      onChange={(e) =>
                        updateLine(index, "unit_price", e.target.value)
                      }
                      className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm tabular-nums focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                    />
                  </div>
                  <div className="col-span-1">
                    <select
                      value={line.btw_percentage}
                      onChange={(e) =>
                        updateLine(index, "btw_percentage", e.target.value)
                      }
                      className="w-full rounded-lg border border-input bg-background px-1.5 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                    >
                      <option value="21.00">21%</option>
                      <option value="9.00">9%</option>
                      <option value="0.00">0%</option>
                    </select>
                  </div>
                  <div className="col-span-1 flex items-center justify-end h-[38px]">
                    <span className="text-sm font-medium tabular-nums">
                      {formatCurrency(lineTotal)}
                    </span>
                  </div>
                  <div className="col-span-1 flex items-center justify-center h-[38px]">
                    {lines.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeLine(index)}
                        className="rounded-md p-1 text-muted-foreground hover:text-red-600 hover:bg-red-50 transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}

            <button
              type="button"
              onClick={addLine}
              className="inline-flex items-center gap-1.5 rounded-lg border border-dashed border-border px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-muted hover:border-primary/30 transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
              Regel toevoegen
            </button>
          </div>

          {/* Totals */}
          <div className="border-t border-border pt-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Subtotaal</span>
              <span className="font-medium tabular-nums">
                {formatCurrency(subtotal)}
              </span>
            </div>
            {verrekenEnabled && verrekenAmount && parseFloat(verrekenAmount) > 0 && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Verrekening voorschot</span>
                <span className="font-medium tabular-nums text-emerald-600">
                  -{formatCurrency(parseFloat(verrekenAmount))}
                </span>
              </div>
            )}
            {/* DF2-03: BTW breakdown per rate group */}
            {btwGroups.size > 1 ? (
              Array.from(btwGroups.entries()).map(([pct, group]) => (
                <div key={pct} className="flex justify-between text-sm">
                  <span className="text-muted-foreground">
                    BTW {parseFloat(pct)}% over {formatCurrency(group.subtotal)}
                  </span>
                  <span className="font-medium tabular-nums">
                    {formatCurrency(group.btw)}
                  </span>
                </div>
              ))
            ) : (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">
                  BTW ({lines[0]?.btw_percentage || "21.00"}%)
                </span>
                <span className="font-medium tabular-nums">
                  {formatCurrency(btwAmount)}
                </span>
              </div>
            )}
            <div className="flex justify-between text-base font-semibold border-t border-border pt-2">
              <span>Totaal</span>
              <span className="tabular-nums">
                {formatCurrency(
                  total -
                    (verrekenEnabled ? (parseFloat(verrekenAmount) || 0) * (1 + (parseFloat(form.btw_percentage) || 0) / 100) : 0)
                )}
              </span>
            </div>
          </div>
        </div>

        {/* LF-21: Voorschot verrekening — only for regular invoices with advance balance */}
        {advanceBalance && advanceBalance.available_balance > 0 && (
          <div className="rounded-xl border border-border bg-card p-6 space-y-4">
            <h2 className="text-base font-semibold text-foreground">
              Voorschot verrekenen
            </h2>
            <p className="text-sm text-muted-foreground">
              Dit dossier heeft een beschikbaar voorschotsaldo van{" "}
              <span className="font-medium text-foreground tabular-nums">
                {formatCurrency(advanceBalance.available_balance)}
              </span>
            </p>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={verrekenEnabled}
                onChange={(e) => {
                  setVerrekenEnabled(e.target.checked);
                  if (!e.target.checked) setVerrekenAmount("");
                }}
                className="h-4 w-4 rounded border-input text-primary focus:ring-primary/20"
              />
              <span className="text-sm font-medium text-foreground">
                Voorschot verrekenen met deze factuur
              </span>
            </label>
            {verrekenEnabled && (
              <div className="pl-7">
                <label htmlFor="inv-verrekening-amount" className="block text-sm font-medium text-foreground mb-1">
                  Verrekeningsbedrag (excl. BTW)
                </label>
                <div className="relative w-48">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">€</span>
                  <input
                    id="inv-verrekening-amount"
                    type="number"
                    step="0.01"
                    min="0"
                    max={advanceBalance.available_balance}
                    value={verrekenAmount}
                    onChange={(e) => setVerrekenAmount(e.target.value)}
                    placeholder="0.00"
                    className={`${inputClass} pl-8 w-48`}
                  />
                </div>
                {parseFloat(verrekenAmount) > advanceBalance.available_balance && (
                  <p className="mt-1 text-xs text-red-600">
                    Bedrag mag niet hoger zijn dan het beschikbare saldo
                  </p>
                )}
              </div>
            )}
          </div>
        )}
        </>)}

        {/* Error */}
        {error && (
          <div className="rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-end gap-3">
          <Link
            href="/facturen"
            className="rounded-lg border border-border px-4 py-2.5 text-sm font-medium text-muted-foreground hover:bg-muted transition-colors"
          >
            Annuleren
          </Link>
          <button
            type="submit"
            disabled={createInvoice.isPending || createVoorschotnota.isPending}
            className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {(createInvoice.isPending || createVoorschotnota.isPending)
              ? "Aanmaken..."
              : invoiceType === "voorschotnota"
                ? "Voorschotnota aanmaken"
                : "Factuur aanmaken"}
          </button>
        </div>
      </form>
    </div>
  );
}
