"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Plus, Trash2, Search } from "lucide-react";
import { toast } from "sonner";
import { useCreateInvoice } from "@/hooks/use-invoices";
import { useRelations } from "@/hooks/use-relations";
import { useCases } from "@/hooks/use-cases";
import { useTimeEntries } from "@/hooks/use-time-entries";
import { useExpenses } from "@/hooks/use-expenses";
import { formatCurrency } from "@/lib/utils";

interface LineItem {
  description: string;
  quantity: string;
  unit_price: string;
  time_entry_id?: string;
  expense_id?: string;
}

export default function NieuweFactuurPage() {
  const router = useRouter();
  const createInvoice = useCreateInvoice();

  const [form, setForm] = useState({
    contact_id: "",
    case_id: "",
    invoice_date: new Date().toISOString().split("T")[0],
    due_date: new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0],
    btw_percentage: "21.00",
    reference: "",
    notes: "",
  });

  const [lines, setLines] = useState<LineItem[]>([
    { description: "", quantity: "1", unit_price: "" },
  ]);

  const [contactSearch, setContactSearch] = useState("");
  const [caseSearch, setCaseSearch] = useState("");
  const [showContactResults, setShowContactResults] = useState(false);
  const [showCaseResults, setShowCaseResults] = useState(false);
  const [selectedContactName, setSelectedContactName] = useState("");
  const [selectedCaseNumber, setSelectedCaseNumber] = useState("");
  const [showTimeEntries, setShowTimeEntries] = useState(false);
  const [showExpenses, setShowExpenses] = useState(false);
  const [error, setError] = useState("");

  const { data: contactResults } = useRelations({
    search: contactSearch || undefined,
    per_page: 5,
  });
  const { data: caseResults } = useCases({
    search: caseSearch || undefined,
    per_page: 5,
  });

  // Time entries for import (only billable, for selected case)
  const { data: timeEntries } = useTimeEntries({
    case_id: form.case_id || undefined,
    billable: true,
  });

  // Uninvoiced expenses for import
  const { data: expenses } = useExpenses({
    case_id: form.case_id || undefined,
    uninvoiced_only: true,
    billable_only: true,
  });

  const updateField = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
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
      { description: "", quantity: "1", unit_price: "" },
    ]);
  };

  const removeLine = (index: number) => {
    setLines((prev) => prev.filter((_, i) => i !== index));
  };

  const importTimeEntry = (entry: {
    id: string;
    description: string | null;
    duration_minutes: number;
    hourly_rate: number | null;
  }) => {
    const hours = entry.duration_minutes / 60;
    const rate = entry.hourly_rate ?? 0;
    setLines((prev) => [
      ...prev,
      {
        description: entry.description || "Juridische werkzaamheden",
        quantity: hours.toFixed(2),
        unit_price: rate.toFixed(2),
        time_entry_id: entry.id,
      },
    ]);
    setShowTimeEntries(false);
  };

  const importExpense = (expense: {
    id: string;
    description: string;
    amount: number;
  }) => {
    setLines((prev) => [
      ...prev,
      {
        description: expense.description,
        quantity: "1",
        unit_price: expense.amount.toFixed(2),
        expense_id: expense.id,
      },
    ]);
    setShowExpenses(false);
  };

  // Calculate totals
  const subtotal = lines.reduce((sum, line) => {
    const qty = parseFloat(line.quantity) || 0;
    const price = parseFloat(line.unit_price) || 0;
    return sum + qty * price;
  }, 0);
  const btwPercentage = parseFloat(form.btw_percentage) || 0;
  const btwAmount = subtotal * (btwPercentage / 100);
  const total = subtotal + btwAmount;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!form.contact_id) {
      setError("Selecteer een relatie");
      return;
    }

    const validLines = lines.filter(
      (l) => l.description && parseFloat(l.unit_price) > 0
    );
    if (validLines.length === 0) {
      setError("Voeg minimaal een factuurregel toe");
      return;
    }

    try {
      const result = await createInvoice.mutateAsync({
        contact_id: form.contact_id,
        case_id: form.case_id || undefined,
        invoice_date: form.invoice_date,
        due_date: form.due_date,
        btw_percentage: parseFloat(form.btw_percentage),
        reference: form.reference || undefined,
        notes: form.notes || undefined,
        lines: validLines.map((l) => ({
          description: l.description,
          quantity: parseFloat(l.quantity) || 1,
          unit_price: parseFloat(l.unit_price),
          time_entry_id: l.time_entry_id || undefined,
          expense_id: l.expense_id || undefined,
        })),
      });
      toast.success("Factuur aangemaakt");
      router.push(`/facturen/${result.id}`);
    } catch (err: any) {
      setError(err.message || "Er ging iets mis");
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
            Nieuwe factuur
          </h1>
          <p className="text-sm text-muted-foreground">
            Maak een nieuwe factuur aan
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Invoice details */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          <h2 className="text-base font-semibold text-foreground">
            Factuurgegevens
          </h2>

          {/* Contact search */}
          <div className="relative">
            <label className="block text-sm font-medium text-foreground">
              Relatie *
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground mt-0.75" />
              <input
                type="text"
                placeholder="Zoek relatie..."
                value={selectedContactName || contactSearch}
                onChange={(e) => {
                  setContactSearch(e.target.value);
                  setSelectedContactName("");
                  updateField("contact_id", "");
                  setShowContactResults(true);
                }}
                onFocus={() => setShowContactResults(true)}
                className={`${inputClass} pl-10`}
              />
            </div>
            {showContactResults &&
              contactSearch &&
              contactResults?.items &&
              contactResults.items.length > 0 && (
                <div className="absolute z-10 mt-1 w-full rounded-lg border border-border bg-card shadow-lg">
                  {contactResults.items.map((c: any) => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => {
                        updateField("contact_id", c.id);
                        setSelectedContactName(c.name);
                        setContactSearch("");
                        setShowContactResults(false);
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

          {/* Case search (optional) */}
          <div className="relative">
            <label className="block text-sm font-medium text-foreground">
              Dossier (optioneel)
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground mt-0.75" />
              <input
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
                className={`${inputClass} pl-10`}
              />
            </div>
            {showCaseResults &&
              caseSearch &&
              caseResults?.items &&
              caseResults.items.length > 0 && (
                <div className="absolute z-10 mt-1 w-full rounded-lg border border-border bg-card shadow-lg">
                  {caseResults.items.map((c: any) => (
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

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground">
                Factuurdatum
              </label>
              <input
                type="date"
                value={form.invoice_date}
                onChange={(e) => updateField("invoice_date", e.target.value)}
                className={inputClass}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground">
                Vervaldatum
              </label>
              <input
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
              <label className="block text-sm font-medium text-foreground">
                BTW-percentage
              </label>
              <input
                type="number"
                step="0.01"
                value={form.btw_percentage}
                onChange={(e) => updateField("btw_percentage", e.target.value)}
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground">
                Referentie
              </label>
              <input
                type="text"
                placeholder="Bijv. kenmerk opdrachtgever"
                value={form.reference}
                onChange={(e) => updateField("reference", e.target.value)}
                className={inputClass}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground">
              Opmerkingen
            </label>
            <textarea
              rows={2}
              placeholder="Optionele opmerkingen op de factuur"
              value={form.notes}
              onChange={(e) => updateField("notes", e.target.value)}
              className={inputClass}
            />
          </div>
        </div>

        {/* Invoice lines */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-foreground">
              Factuurregels
            </h2>
            <div className="flex gap-2">
              {form.case_id && (
                <>
                  <button
                    type="button"
                    onClick={() => setShowTimeEntries(!showTimeEntries)}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    Importeer uren
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowExpenses(!showExpenses)}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    Importeer verschotten
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Time entries import panel */}
          {showTimeEntries && timeEntries && timeEntries.length > 0 && (
            <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Declarabele uren
              </p>
              {timeEntries.map((entry: any) => (
                <button
                  key={entry.id}
                  type="button"
                  onClick={() => importTimeEntry(entry)}
                  className="flex w-full items-center justify-between rounded-md px-3 py-2 text-sm hover:bg-muted transition-colors"
                >
                  <span className="truncate">
                    {entry.description || "Werkzaamheden"} &middot;{" "}
                    {(entry.duration_minutes / 60).toFixed(1)}u
                  </span>
                  <span className="text-muted-foreground tabular-nums">
                    {entry.hourly_rate
                      ? formatCurrency(
                          (entry.duration_minutes / 60) * entry.hourly_rate
                        )
                      : "-"}
                  </span>
                </button>
              ))}
            </div>
          )}

          {/* Expenses import panel */}
          {showExpenses && expenses && expenses.length > 0 && (
            <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-2">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Ongedefactureerde verschotten
              </p>
              {expenses.map((expense: any) => (
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

          {/* Line items table */}
          <div className="space-y-3">
            {/* Header */}
            <div className="grid grid-cols-12 gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground px-1">
              <div className="col-span-5">Omschrijving</div>
              <div className="col-span-2">Aantal</div>
              <div className="col-span-2">Prijs</div>
              <div className="col-span-2 text-right">Totaal</div>
              <div className="col-span-1" />
            </div>

            {lines.map((line, index) => {
              const qty = parseFloat(line.quantity) || 0;
              const price = parseFloat(line.unit_price) || 0;
              const lineTotal = qty * price;

              return (
                <div key={index} className="grid grid-cols-12 gap-2 items-start">
                  <div className="col-span-5">
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
                  <div className="col-span-2 flex items-center justify-end h-[38px]">
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
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">
                BTW ({form.btw_percentage}%)
              </span>
              <span className="font-medium tabular-nums">
                {formatCurrency(btwAmount)}
              </span>
            </div>
            <div className="flex justify-between text-base font-semibold border-t border-border pt-2">
              <span>Totaal</span>
              <span className="tabular-nums">{formatCurrency(total)}</span>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
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
            disabled={createInvoice.isPending}
            className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {createInvoice.isPending ? "Aanmaken..." : "Factuur aanmaken"}
          </button>
        </div>
      </form>
    </div>
  );
}
