"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Briefcase,
  Clock,
  Users,
  Trash2,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";
import {
  useCase,
  useUpdateCaseStatus,
  useDeleteCase,
} from "@/hooks/use-cases";
import { formatCurrency, formatDate } from "@/lib/utils";

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
      <div className="border-b border-border">
        <nav className="flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
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
      {activeTab === "overzicht" && (
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
                  <dt className="text-xs text-muted-foreground">
                    Toegewezen aan
                  </dt>
                  <dd className="text-sm text-foreground">
                    {zaak.assigned_to.full_name}
                  </dd>
                </div>
              )}
              {zaak.date_closed && (
                <div>
                  <dt className="text-xs text-muted-foreground">
                    Datum gesloten
                  </dt>
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
                {zaak.recent_activities.slice(0, 5).map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-start gap-3 rounded-lg p-2.5 -mx-1 hover:bg-muted/50 transition-colors"
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
              <p className="text-sm text-muted-foreground">
                Geen activiteiten
              </p>
            )}
          </div>
        </div>
      )}

      {activeTab === "activiteiten" && (
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-4 text-base font-semibold text-foreground">
            Alle activiteiten
          </h2>
          {zaak.recent_activities && zaak.recent_activities.length > 0 ? (
            <div className="space-y-1">
              {zaak.recent_activities.map((activity) => (
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
            <p className="text-sm text-muted-foreground">
              Geen activiteiten
            </p>
          )}
        </div>
      )}

      {activeTab === "partijen" && (
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
              zaak.parties.map((party) => (
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
      )}
    </div>
  );
}
