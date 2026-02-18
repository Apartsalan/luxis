"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Briefcase,
  Clock,
  Download,
  File,
  Users,
  Trash2,
  ChevronRight,
  Euro,
  FileText,
  Loader2,
  Plus,
  Receipt,
  Wallet,
} from "lucide-react";
import { toast } from "sonner";
import {
  useCase,
  useUpdateCaseStatus,
  useDeleteCase,
} from "@/hooks/use-cases";
import {
  useClaims,
  useCreateClaim,
  useDeleteClaim,
  usePayments,
  useCreatePayment,
  useCaseInterest,
  useFinancialSummary,
  useDerdengelden,
  useDerdengeldenBalance,
  useCreateDerdengelden,
} from "@/hooks/use-collections";
import {
  useDocxTemplates,
  useGenerateDocx,
  useCaseDocuments,
  useDeleteDocument,
  getTemplateLabel,
  getTemplateDescription,
  triggerDownload,
} from "@/hooks/use-documents";
import { formatCurrency, formatDate, formatDateShort } from "@/lib/utils";

const STATUS_LABELS: Record<string, string> = {
  nieuw: "Nieuw",
  "14_dagenbrief": "14-dagenbrief",
  sommatie: "Sommatie",
  dagvaarding: "Dagvaarding",
  vonnis: "Vonnis",
  executie: "Executie",
  betaald: "Betaald",
  afgesloten: "Afgesloten",
};

const STATUS_COLORS: Record<string, string> = {
  nieuw: "bg-blue-100 text-blue-700",
  "14_dagenbrief": "bg-yellow-100 text-yellow-700",
  sommatie: "bg-orange-100 text-orange-700",
  dagvaarding: "bg-red-100 text-red-700",
  vonnis: "bg-purple-100 text-purple-700",
  executie: "bg-red-200 text-red-800",
  betaald: "bg-emerald-100 text-emerald-700",
  afgesloten: "bg-gray-100 text-gray-600",
};

const NEXT_STATUSES: Record<string, string[]> = {
  nieuw: ["14_dagenbrief", "afgesloten"],
  "14_dagenbrief": ["sommatie", "betaald", "afgesloten"],
  sommatie: ["dagvaarding", "betaald", "afgesloten"],
  dagvaarding: ["vonnis", "betaald", "afgesloten"],
  vonnis: ["executie", "betaald", "afgesloten"],
  executie: ["betaald", "afgesloten"],
  betaald: [],
  afgesloten: [],
};

const TYPE_LABELS: Record<string, string> = {
  incasso: "Incasso",
  insolventie: "Insolventie",
  advies: "Advies",
  overig: "Overig",
};

const INTEREST_LABELS: Record<string, string> = {
  statutory: "Wettelijke rente (art. 6:119 BW)",
  commercial: "Handelsrente (art. 6:119a BW)",
  government: "Overheidsrente (art. 6:119b BW)",
  contractual: "Contractuele rente",
};

const ACTIVITY_ICONS: Record<string, string> = {
  status_change: "📋",
  note: "📝",
  phone_call: "📞",
  email: "📧",
  document: "📄",
  payment: "💰",
};

export default function ZaakDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { data: zaak, isLoading } = useCase(id);
  const updateStatus = useUpdateCaseStatus();
  const deleteCase = useDeleteCase();
  const [activeTab, setActiveTab] = useState("overzicht");

  const handleStatusChange = async (newStatus: string) => {
    const note = prompt("Notitie bij statuswijziging (optioneel):");
    try {
      await updateStatus.mutateAsync({
        id,
        new_status: newStatus,
        note: note || undefined,
      });
      toast.success(`Status gewijzigd naar ${STATUS_LABELS[newStatus]}`);
    } catch (err: any) {
      toast.error(err.message || "Statuswijziging mislukt");
    }
  };

  const handleDelete = async () => {
    if (!confirm("Weet je zeker dat je deze zaak wilt verwijderen?")) return;
    try {
      await deleteCase.mutateAsync(id);
      toast.success("Zaak verwijderd");
      router.push("/zaken");
    } catch {
      toast.error("Kon de zaak niet verwijderen");
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="h-8 w-48 rounded-md skeleton" />
        <div className="grid gap-4 md:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-20 rounded-lg skeleton" />
          ))}
        </div>
        <div className="h-64 rounded-lg skeleton" />
      </div>
    );
  }

  if (!zaak) {
    return (
      <div className="py-20 text-center">
        <p className="text-muted-foreground">Zaak niet gevonden</p>
        <Link
          href="/zaken"
          className="mt-2 inline-block text-sm text-primary hover:underline"
        >
          Terug naar zaken
        </Link>
      </div>
    );
  }

  const tabs = [
    { id: "overzicht", label: "Overzicht", icon: Briefcase },
    { id: "vorderingen", label: "Vorderingen", icon: Euro },
    { id: "betalingen", label: "Betalingen", icon: Receipt },
    { id: "financieel", label: "Financieel", icon: Wallet },
    { id: "derdengelden", label: "Derdengelden", icon: FileText },
    { id: "documenten", label: "Documenten", icon: File },
    { id: "activiteiten", label: "Activiteiten", icon: Clock },
    { id: "partijen", label: "Partijen", icon: Users },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/zaken"
            className="rounded-lg p-2 hover:bg-muted transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-muted-foreground" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-foreground">
                {zaak.case_number}
              </h1>
              <span
                className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  STATUS_COLORS[zaak.status] ?? "bg-gray-100 text-gray-600"
                }`}
              >
                {STATUS_LABELS[zaak.status] ?? zaak.status}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              {TYPE_LABELS[zaak.case_type]} &middot; Geopend{" "}
              {formatDate(zaak.date_opened)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {NEXT_STATUSES[zaak.status]?.map((nextStatus) => (
            <button
              key={nextStatus}
              onClick={() => handleStatusChange(nextStatus)}
              disabled={updateStatus.isPending}
              className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted transition-colors"
            >
              <ChevronRight className="h-3 w-3" />
              {STATUS_LABELS[nextStatus]}
            </button>
          ))}
          <button
            onClick={handleDelete}
            className="rounded-lg border border-destructive/20 p-2 text-destructive hover:bg-destructive/10 transition-colors"
            title="Verwijderen"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Hoofdsom</p>
          <p className="text-lg font-bold text-foreground">
            {formatCurrency(zaak.total_principal)}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Betaald</p>
          <p className="text-lg font-bold text-success">
            {formatCurrency(zaak.total_paid)}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Rente</p>
          <p className="text-xs text-muted-foreground mt-1">
            {INTEREST_LABELS[zaak.interest_type] ?? zaak.interest_type}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-card p-4">
          <p className="text-xs text-muted-foreground">Client</p>
          <p className="text-sm font-medium text-foreground">
            {zaak.client?.name ?? "-"}
          </p>
          {zaak.opposing_party && (
            <>
              <p className="text-xs text-muted-foreground mt-2">Wederpartij</p>
              <p className="text-sm font-medium text-foreground">
                {zaak.opposing_party.name}
              </p>
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border overflow-x-auto">
        <nav className="flex gap-1 min-w-max">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      {activeTab === "overzicht" && <OverzichtTab zaak={zaak} />}
      {activeTab === "vorderingen" && <VorderingenTab caseId={id} />}
      {activeTab === "betalingen" && <BetalingenTab caseId={id} />}
      {activeTab === "financieel" && <FinancieelTab caseId={id} />}
      {activeTab === "derdengelden" && <DerdengeldenTab caseId={id} />}
      {activeTab === "documenten" && <DocumentenTab caseId={id} />}
      {activeTab === "activiteiten" && <ActiviteitenTab zaak={zaak} />}
      {activeTab === "partijen" && <PartijenTab zaak={zaak} />}
    </div>
  );
}

// ── Overzicht Tab ─────────────────────────────────────────────────────────────

function OverzichtTab({ zaak }: { zaak: any }) {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="mb-4 text-base font-semibold text-foreground">
          Zaakgegevens
        </h2>
        <dl className="space-y-3">
          <div>
            <dt className="text-xs text-muted-foreground">Beschrijving</dt>
            <dd className="text-sm text-foreground">
              {zaak.description || "-"}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Referentie</dt>
            <dd className="text-sm text-foreground">
              {zaak.reference || "-"}
            </dd>
          </div>
          {zaak.contractual_rate && (
            <div>
              <dt className="text-xs text-muted-foreground">
                Contractueel rentepercentage
              </dt>
              <dd className="text-sm text-foreground">
                {zaak.contractual_rate}%
                {zaak.contractual_compound
                  ? " (samengesteld)"
                  : " (enkelvoudig)"}
              </dd>
            </div>
          )}
          {zaak.assigned_to && (
            <div>
              <dt className="text-xs text-muted-foreground">Toegewezen aan</dt>
              <dd className="text-sm text-foreground">
                {zaak.assigned_to.full_name}
              </dd>
            </div>
          )}
          {zaak.date_closed && (
            <div>
              <dt className="text-xs text-muted-foreground">Datum gesloten</dt>
              <dd className="text-sm text-foreground">
                {formatDate(zaak.date_closed)}
              </dd>
            </div>
          )}
        </dl>
      </div>

      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="mb-4 text-base font-semibold text-foreground">
          Recente activiteit
        </h2>
        {zaak.recent_activities && zaak.recent_activities.length > 0 ? (
          <div className="space-y-2">
            {zaak.recent_activities.slice(0, 5).map((activity: any) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 rounded-lg p-2.5 -mx-1"
              >
                <span className="mt-0.5 text-base">
                  {ACTIVITY_ICONS[activity.activity_type] ?? "📌"}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-foreground">
                    {activity.title}
                  </p>
                  {activity.description && (
                    <p className="text-xs text-muted-foreground truncate">
                      {activity.description}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground">
                    {formatDate(activity.created_at)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Geen activiteiten</p>
        )}
      </div>
    </div>
  );
}

// ── Vorderingen Tab ───────────────────────────────────────────────────────────

function VorderingenTab({ caseId }: { caseId: string }) {
  const { data: claims, isLoading } = useClaims(caseId);
  const { data: interest } = useCaseInterest(caseId);
  const createClaim = useCreateClaim();
  const deleteClaim = useDeleteClaim();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    description: "",
    principal_amount: "",
    default_date: "",
    invoice_number: "",
    invoice_date: "",
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createClaim.mutateAsync({
        caseId,
        data: {
          description: form.description,
          principal_amount: parseFloat(form.principal_amount),
          default_date: form.default_date,
          ...(form.invoice_number && { invoice_number: form.invoice_number }),
          ...(form.invoice_date && { invoice_date: form.invoice_date }),
        },
      });
      toast.success("Vordering toegevoegd");
      setShowForm(false);
      setForm({
        description: "",
        principal_amount: "",
        default_date: "",
        invoice_number: "",
        invoice_date: "",
      });
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleDelete = async (claimId: string) => {
    if (!confirm("Vordering verwijderen?")) return;
    try {
      await deleteClaim.mutateAsync({ caseId, claimId });
      toast.success("Vordering verwijderd");
    } catch {
      toast.error("Kon niet verwijderen");
    }
  };

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">
          Vorderingen
        </h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          Vordering toevoegen
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-3"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-foreground">
                Beschrijving *
              </label>
              <input
                type="text"
                required
                value={form.description}
                onChange={(e) =>
                  setForm((f) => ({ ...f, description: e.target.value }))
                }
                className={inputClass}
                placeholder="Factuur nr. 2025-001"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Hoofdsom *
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={form.principal_amount}
                onChange={(e) =>
                  setForm((f) => ({ ...f, principal_amount: e.target.value }))
                }
                className={inputClass}
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Verzuimdatum *
              </label>
              <input
                type="date"
                required
                value={form.default_date}
                onChange={(e) =>
                  setForm((f) => ({ ...f, default_date: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Factuurnummer
              </label>
              <input
                type="text"
                value={form.invoice_number}
                onChange={(e) =>
                  setForm((f) => ({ ...f, invoice_number: e.target.value }))
                }
                className={inputClass}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createClaim.isPending}
              className="rounded-lg bg-primary px-4 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {createClaim.isPending ? "Opslaan..." : "Opslaan"}
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

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg skeleton" />
          ))}
        </div>
      ) : claims && claims.length > 0 ? (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="px-4 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Beschrijving
                </th>
                <th className="px-4 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Hoofdsom
                </th>
                <th className="hidden sm:table-cell px-4 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Verzuimdatum
                </th>
                <th className="hidden md:table-cell px-4 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Rente
                </th>
                <th className="px-4 py-2.5 w-10" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {claims.map((claim) => {
                const claimInterest = interest?.claims.find(
                  (c) => c.claim_id === claim.id
                );
                return (
                  <tr
                    key={claim.id}
                    className="hover:bg-muted/30 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <p className="text-sm font-medium text-foreground">
                        {claim.description}
                      </p>
                      {claim.invoice_number && (
                        <p className="text-xs text-muted-foreground">
                          Factuur: {claim.invoice_number}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-sm font-medium text-foreground">
                      {formatCurrency(claim.principal_amount)}
                    </td>
                    <td className="hidden sm:table-cell px-4 py-3 text-sm text-muted-foreground">
                      {formatDateShort(claim.default_date)}
                    </td>
                    <td className="hidden md:table-cell px-4 py-3 text-right text-sm text-accent font-medium">
                      {claimInterest
                        ? formatCurrency(claimInterest.total_interest)
                        : "-"}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleDelete(claim.id)}
                        className="rounded p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
            {interest && (
              <tfoot>
                <tr className="border-t-2 border-border bg-muted/20">
                  <td className="px-4 py-3 text-sm font-semibold text-foreground">
                    Totaal
                  </td>
                  <td className="px-4 py-3 text-right text-sm font-bold text-foreground">
                    {formatCurrency(interest.total_principal)}
                  </td>
                  <td className="hidden sm:table-cell px-4 py-3" />
                  <td className="hidden md:table-cell px-4 py-3 text-right text-sm font-bold text-accent">
                    {formatCurrency(interest.total_interest)}
                  </td>
                  <td className="px-4 py-3" />
                </tr>
              </tfoot>
            )}
          </table>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <Euro className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">
            Nog geen vorderingen
          </p>
          <button
            onClick={() => setShowForm(true)}
            className="mt-2 text-sm text-primary hover:underline"
          >
            Voeg de eerste vordering toe
          </button>
        </div>
      )}
    </div>
  );
}

// ── Betalingen Tab ────────────────────────────────────────────────────────────

function BetalingenTab({ caseId }: { caseId: string }) {
  const { data: payments, isLoading } = usePayments(caseId);
  const createPayment = useCreatePayment();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    amount: "",
    payment_date: new Date().toISOString().split("T")[0],
    description: "",
    payment_method: "",
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createPayment.mutateAsync({
        caseId,
        data: {
          amount: parseFloat(form.amount),
          payment_date: form.payment_date,
          ...(form.description && { description: form.description }),
          ...(form.payment_method && { payment_method: form.payment_method }),
        },
      });
      toast.success("Betaling geregistreerd");
      setShowForm(false);
      setForm({
        amount: "",
        payment_date: new Date().toISOString().split("T")[0],
        description: "",
        payment_method: "",
      });
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">Betalingen</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          Betaling registreren
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-3"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-foreground">
                Bedrag *
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={form.amount}
                onChange={(e) =>
                  setForm((f) => ({ ...f, amount: e.target.value }))
                }
                className={inputClass}
                placeholder="0.00"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Datum *
              </label>
              <input
                type="date"
                required
                value={form.payment_date}
                onChange={(e) =>
                  setForm((f) => ({ ...f, payment_date: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
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
            <div>
              <label className="block text-xs font-medium text-foreground">
                Betaalwijze
              </label>
              <select
                value={form.payment_method}
                onChange={(e) =>
                  setForm((f) => ({ ...f, payment_method: e.target.value }))
                }
                className={inputClass}
              >
                <option value="">-</option>
                <option value="bank">Bankoverschrijving</option>
                <option value="cash">Contant</option>
                <option value="derdengelden">Via derdengelden</option>
              </select>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createPayment.isPending}
              className="rounded-lg bg-primary px-4 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {createPayment.isPending ? "Opslaan..." : "Registreren"}
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

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 rounded-lg skeleton" />
          ))}
        </div>
      ) : payments && payments.length > 0 ? (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="px-4 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Datum
                </th>
                <th className="px-4 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Bedrag
                </th>
                <th className="hidden sm:table-cell px-4 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Omschrijving
                </th>
                <th className="hidden md:table-cell px-4 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Kosten
                </th>
                <th className="hidden md:table-cell px-4 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Rente
                </th>
                <th className="hidden md:table-cell px-4 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Hoofdsom
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {payments.map((payment) => (
                <tr
                  key={payment.id}
                  className="hover:bg-muted/30 transition-colors"
                >
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {formatDateShort(payment.payment_date)}
                  </td>
                  <td className="px-4 py-3 text-right text-sm font-medium text-success">
                    {formatCurrency(payment.amount)}
                  </td>
                  <td className="hidden sm:table-cell px-4 py-3 text-sm text-muted-foreground">
                    {payment.description || "-"}
                  </td>
                  <td className="hidden md:table-cell px-4 py-3 text-right text-xs text-muted-foreground">
                    {formatCurrency(payment.allocated_to_costs)}
                  </td>
                  <td className="hidden md:table-cell px-4 py-3 text-right text-xs text-muted-foreground">
                    {formatCurrency(payment.allocated_to_interest)}
                  </td>
                  <td className="hidden md:table-cell px-4 py-3 text-right text-xs text-muted-foreground">
                    {formatCurrency(payment.allocated_to_principal)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="border-t border-border bg-muted/20 px-4 py-2.5 text-xs text-muted-foreground">
            Art. 6:44 BW — Betalingen worden automatisch verdeeld: eerst kosten, dan rente, dan hoofdsom
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <Receipt className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">
            Nog geen betalingen
          </p>
        </div>
      )}
    </div>
  );
}

// ── Financieel Tab ────────────────────────────────────────────────────────────

function FinancieelTab({ caseId }: { caseId: string }) {
  const { data: summary, isLoading } = useFinancialSummary(caseId);

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-16 rounded-lg skeleton" />
        ))}
      </div>
    );
  }

  if (!summary) return null;

  return (
    <div className="space-y-6">
      <h2 className="text-base font-semibold text-foreground">
        Financieel overzicht
      </h2>

      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-muted/30">
              <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Post
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Totaal
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Betaald
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Openstaand
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            <tr>
              <td className="px-5 py-3 text-sm text-foreground">Hoofdsom</td>
              <td className="px-5 py-3 text-right text-sm font-medium">
                {formatCurrency(summary.total_principal)}
              </td>
              <td className="px-5 py-3 text-right text-sm text-success">
                {formatCurrency(summary.total_paid_principal)}
              </td>
              <td className="px-5 py-3 text-right text-sm font-medium">
                {formatCurrency(summary.remaining_principal)}
              </td>
            </tr>
            <tr>
              <td className="px-5 py-3 text-sm text-foreground">Rente</td>
              <td className="px-5 py-3 text-right text-sm font-medium">
                {formatCurrency(summary.total_interest)}
              </td>
              <td className="px-5 py-3 text-right text-sm text-success">
                {formatCurrency(summary.total_paid_interest)}
              </td>
              <td className="px-5 py-3 text-right text-sm font-medium">
                {formatCurrency(summary.remaining_interest)}
              </td>
            </tr>
            <tr>
              <td className="px-5 py-3 text-sm text-foreground">
                BIK (art. 6:96 BW)
                {summary.bik_btw > 0 && (
                  <span className="ml-1 text-xs text-muted-foreground">
                    incl. BTW
                  </span>
                )}
              </td>
              <td className="px-5 py-3 text-right text-sm font-medium">
                {formatCurrency(summary.total_bik)}
              </td>
              <td className="px-5 py-3 text-right text-sm text-success">
                {formatCurrency(summary.total_paid_costs)}
              </td>
              <td className="px-5 py-3 text-right text-sm font-medium">
                {formatCurrency(summary.remaining_costs)}
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-border bg-muted/30">
              <td className="px-5 py-3 text-sm font-bold text-foreground">
                Totaal
              </td>
              <td className="px-5 py-3 text-right text-sm font-bold text-foreground">
                {formatCurrency(summary.grand_total)}
              </td>
              <td className="px-5 py-3 text-right text-sm font-bold text-success">
                {formatCurrency(summary.total_paid)}
              </td>
              <td className="px-5 py-3 text-right text-sm font-bold text-primary">
                {formatCurrency(summary.total_outstanding)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {summary.derdengelden_balance > 0 && (
        <div className="rounded-xl border border-border bg-card p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-foreground">Derdengelden saldo</p>
            <p className="text-lg font-bold text-primary">
              {formatCurrency(summary.derdengelden_balance)}
            </p>
          </div>
        </div>
      )}

      <p className="text-xs text-muted-foreground">
        Berekening op {formatDate(summary.calculation_date)}. Rente wordt
        dagelijks bijgewerkt.
      </p>
    </div>
  );
}

// ── Derdengelden Tab ──────────────────────────────────────────────────────────

function DerdengeldenTab({ caseId }: { caseId: string }) {
  const { data: transactions, isLoading } = useDerdengelden(caseId);
  const { data: balance } = useDerdengeldenBalance(caseId);
  const createTx = useCreateDerdengelden();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    transaction_type: "deposit" as "deposit" | "withdrawal",
    amount: "",
    transaction_date: new Date().toISOString().split("T")[0],
    description: "",
    counterparty: "",
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createTx.mutateAsync({
        caseId,
        data: {
          transaction_type: form.transaction_type,
          amount: parseFloat(form.amount),
          transaction_date: form.transaction_date,
          ...(form.description && { description: form.description }),
          ...(form.counterparty && { counterparty: form.counterparty }),
        },
      });
      toast.success("Transactie opgeslagen");
      setShowForm(false);
      setForm({
        transaction_type: "deposit",
        amount: "",
        transaction_date: new Date().toISOString().split("T")[0],
        description: "",
        counterparty: "",
      });
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-foreground">
            Derdengelden
          </h2>
          {balance && (
            <p className="text-sm text-muted-foreground">
              Saldo:{" "}
              <span className="font-semibold text-primary">
                {formatCurrency(balance.balance)}
              </span>
            </p>
          )}
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          Transactie
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="rounded-xl border border-primary/20 bg-primary/5 p-5 space-y-3"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-foreground">
                Type *
              </label>
              <select
                value={form.transaction_type}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    transaction_type: e.target.value as "deposit" | "withdrawal",
                  }))
                }
                className={inputClass}
              >
                <option value="deposit">Storting</option>
                <option value="withdrawal">Uitbetaling</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Bedrag *
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={form.amount}
                onChange={(e) =>
                  setForm((f) => ({ ...f, amount: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Datum *
              </label>
              <input
                type="date"
                required
                value={form.transaction_date}
                onChange={(e) =>
                  setForm((f) => ({ ...f, transaction_date: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-foreground">
                Wederpartij
              </label>
              <input
                type="text"
                value={form.counterparty}
                onChange={(e) =>
                  setForm((f) => ({ ...f, counterparty: e.target.value }))
                }
                className={inputClass}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={createTx.isPending}
              className="rounded-lg bg-primary px-4 py-2 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              Opslaan
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

      {isLoading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-14 rounded-lg skeleton" />
          ))}
        </div>
      ) : transactions && transactions.length > 0 ? (
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="px-4 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Datum
                </th>
                <th className="px-4 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Type
                </th>
                <th className="px-4 py-2.5 text-right text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Bedrag
                </th>
                <th className="hidden sm:table-cell px-4 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Wederpartij
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {transactions.map((tx) => (
                <tr
                  key={tx.id}
                  className="hover:bg-muted/30 transition-colors"
                >
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {formatDateShort(tx.transaction_date)}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        tx.transaction_type === "deposit"
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-orange-100 text-orange-700"
                      }`}
                    >
                      {tx.transaction_type === "deposit"
                        ? "Storting"
                        : "Uitbetaling"}
                    </span>
                  </td>
                  <td
                    className={`px-4 py-3 text-right text-sm font-medium ${
                      tx.transaction_type === "deposit"
                        ? "text-success"
                        : "text-warning"
                    }`}
                  >
                    {tx.transaction_type === "deposit" ? "+" : "-"}
                    {formatCurrency(tx.amount)}
                  </td>
                  <td className="hidden sm:table-cell px-4 py-3 text-sm text-muted-foreground">
                    {tx.counterparty || "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-border py-12 text-center">
          <FileText className="mx-auto h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">
            Geen derdengelden transacties
          </p>
        </div>
      )}
    </div>
  );
}

// ── Activiteiten Tab ──────────────────────────────────────────────────────────

function ActiviteitenTab({ zaak }: { zaak: any }) {
  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <h2 className="mb-4 text-base font-semibold text-foreground">
        Alle activiteiten
      </h2>
      {zaak.recent_activities && zaak.recent_activities.length > 0 ? (
        <div className="space-y-1">
          {zaak.recent_activities.map((activity: any) => (
            <div
              key={activity.id}
              className="flex items-start gap-3 border-b border-border pb-3 last:border-0 py-2.5"
            >
              <span className="mt-0.5 text-base">
                {ACTIVITY_ICONS[activity.activity_type] ?? "📌"}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-foreground">
                  {activity.title}
                </p>
                {activity.description && (
                  <p className="text-sm text-muted-foreground">
                    {activity.description}
                  </p>
                )}
                <p className="text-xs text-muted-foreground mt-1">
                  {formatDate(activity.created_at)}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">Geen activiteiten</p>
      )}
    </div>
  );
}

// ── Partijen Tab ──────────────────────────────────────────────────────────────

function PartijenTab({ zaak }: { zaak: any }) {
  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <h2 className="mb-4 text-base font-semibold text-foreground">
        Partijen
      </h2>
      <div className="space-y-2">
        {zaak.client && (
          <div className="flex items-center justify-between rounded-lg border border-border p-3">
            <Link
              href={`/relaties/${zaak.client.id}`}
              className="text-sm font-medium text-foreground hover:text-primary hover:underline"
            >
              {zaak.client.name}
            </Link>
            <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
              Client
            </span>
          </div>
        )}
        {zaak.opposing_party && (
          <div className="flex items-center justify-between rounded-lg border border-border p-3">
            <Link
              href={`/relaties/${zaak.opposing_party.id}`}
              className="text-sm font-medium text-foreground hover:text-primary hover:underline"
            >
              {zaak.opposing_party.name}
            </Link>
            <span className="rounded-full bg-warning/10 px-2.5 py-0.5 text-xs font-medium text-warning">
              Wederpartij
            </span>
          </div>
        )}
        {zaak.parties &&
          zaak.parties.map((party: any) => (
            <div
              key={party.id}
              className="flex items-center justify-between rounded-lg border border-border p-3"
            >
              <Link
                href={`/relaties/${party.contact.id}`}
                className="text-sm font-medium text-foreground hover:text-primary hover:underline"
              >
                {party.contact.name}
              </Link>
              <span className="rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-muted-foreground">
                {party.role}
              </span>
            </div>
          ))}
      </div>
    </div>
  );
}

// ── Documenten Tab ──────────────────────────────────────────────────────────

function DocumentenTab({ caseId }: { caseId: string }) {
  const { data: templates, isLoading: templatesLoading } = useDocxTemplates();
  const { data: documents, isLoading: docsLoading } = useCaseDocuments(caseId);
  const generateDocx = useGenerateDocx(caseId);
  const deleteDocument = useDeleteDocument(caseId);

  const handleGenerate = async (templateType: string) => {
    try {
      const result = await generateDocx.mutateAsync(templateType);
      triggerDownload(result.blob, result.filename);
      toast.success(`${getTemplateLabel(templateType)} gegenereerd`);
    } catch (err: any) {
      toast.error(err.message || "Fout bij genereren document");
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      await deleteDocument.mutateAsync(docId);
      toast.success("Document verwijderd");
    } catch {
      toast.error("Fout bij verwijderen document");
    }
  };

  return (
    <div className="space-y-6">
      {/* Generate from templates */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="mb-1 text-base font-semibold text-foreground">
          Document genereren
        </h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Genereer een Word-document vanuit een template
        </p>

        {templatesLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Templates laden...
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {templates
              ?.filter((t) => t.available)
              .map((template) => (
                <button
                  key={template.template_type}
                  onClick={() => handleGenerate(template.template_type)}
                  disabled={generateDocx.isPending}
                  className="flex flex-col items-start gap-2 rounded-lg border border-border p-4 text-left hover:border-primary/30 hover:bg-muted/50 transition-all disabled:opacity-50"
                >
                  <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                      <FileText className="h-4 w-4 text-primary" />
                    </div>
                    <span className="text-sm font-medium text-foreground">
                      {getTemplateLabel(template.template_type)}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {getTemplateDescription(template.template_type)}
                  </p>
                  <div className="mt-auto flex items-center gap-1 text-xs text-primary">
                    <Download className="h-3 w-3" />
                    {generateDocx.isPending ? "Genereren..." : "Download .docx"}
                  </div>
                </button>
              ))}
          </div>
        )}
      </div>

      {/* Generated documents list */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="mb-1 text-base font-semibold text-foreground">
          Gegenereerde documenten
        </h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Eerder gegenereerde documenten voor deze zaak
        </p>

        {docsLoading ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Documenten laden...
          </div>
        ) : !documents?.length ? (
          <div className="rounded-lg border border-dashed border-border py-8 text-center">
            <File className="mx-auto h-8 w-8 text-muted-foreground/30" />
            <p className="mt-2 text-sm text-muted-foreground">
              Nog geen documenten gegenereerd voor deze zaak
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between rounded-lg border border-border p-3"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {doc.title}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDateShort(doc.created_at)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="rounded-lg p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                  title="Verwijderen"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
