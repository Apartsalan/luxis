"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Briefcase,
  Clock,
  Euro,
  FileText,
  Users,
  Trash2,
} from "lucide-react";
import { useCase, useUpdateCaseStatus, useDeleteCase } from "@/hooks/use-cases";
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
  betaald: "bg-green-100 text-green-700",
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
    } catch (err: any) {
      alert(err.message || "Statuswijziging mislukt");
    }
  };

  const handleDelete = async () => {
    if (!confirm("Weet je zeker dat je deze zaak wilt verwijderen?")) return;
    try {
      await deleteCase.mutateAsync(id);
      router.push("/zaken");
    } catch {
      alert("Kon de zaak niet verwijderen");
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-navy-200 border-t-navy-500" />
      </div>
    );
  }

  if (!zaak) {
    return (
      <div className="py-20 text-center">
        <p className="text-muted-foreground">Zaak niet gevonden</p>
      </div>
    );
  }

  const tabs = [
    { id: "overzicht", label: "Overzicht", icon: Briefcase },
    { id: "activiteiten", label: "Activiteiten", icon: Clock },
    { id: "partijen", label: "Partijen", icon: Users },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/zaken"
            className="rounded-md p-2 hover:bg-muted transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-navy-500" />
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-navy-800">
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
              {TYPE_LABELS[zaak.case_type]} &middot; Geopend {formatDate(zaak.date_opened)}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {/* Status change buttons */}
          {NEXT_STATUSES[zaak.status]?.map((nextStatus) => (
            <button
              key={nextStatus}
              onClick={() => handleStatusChange(nextStatus)}
              disabled={updateStatus.isPending}
              className="rounded-md border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted transition-colors"
            >
              &rarr; {STATUS_LABELS[nextStatus]}
            </button>
          ))}
          <button
            onClick={handleDelete}
            className="rounded-md border border-red-200 p-2 text-red-600 hover:bg-red-50 transition-colors"
            title="Verwijderen"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-border bg-white p-4">
          <p className="text-xs text-muted-foreground">Hoofdsom</p>
          <p className="text-lg font-bold text-navy-800">
            {formatCurrency(zaak.total_principal)}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-white p-4">
          <p className="text-xs text-muted-foreground">Betaald</p>
          <p className="text-lg font-bold text-green-600">
            {formatCurrency(zaak.total_paid)}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-white p-4">
          <p className="text-xs text-muted-foreground">Rente</p>
          <p className="text-xs text-muted-foreground mt-1">
            {INTEREST_LABELS[zaak.interest_type] ?? zaak.interest_type}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-white p-4">
          <p className="text-xs text-muted-foreground">Client</p>
          <p className="text-sm font-medium text-navy-700">
            {zaak.client?.name ?? "-"}
          </p>
          {zaak.opposing_party && (
            <>
              <p className="text-xs text-muted-foreground mt-2">Wederpartij</p>
              <p className="text-sm font-medium text-navy-700">
                {zaak.opposing_party.name}
              </p>
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border">
        <nav className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "border-navy-500 text-navy-800"
                  : "border-transparent text-muted-foreground hover:text-navy-600"
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
          <div className="rounded-lg border border-border bg-white p-6">
            <h2 className="mb-4 text-lg font-semibold text-navy-800">
              Zaakgegevens
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-xs text-muted-foreground">Beschrijving</dt>
                <dd className="text-sm text-navy-700">
                  {zaak.description || "-"}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Referentie</dt>
                <dd className="text-sm text-navy-700">{zaak.reference || "-"}</dd>
              </div>
              {zaak.contractual_rate && (
                <div>
                  <dt className="text-xs text-muted-foreground">
                    Contractueel rentepercentage
                  </dt>
                  <dd className="text-sm text-navy-700">
                    {zaak.contractual_rate}%
                    {zaak.contractual_compound ? " (samengesteld)" : " (enkelvoudig)"}
                  </dd>
                </div>
              )}
              {zaak.assigned_to && (
                <div>
                  <dt className="text-xs text-muted-foreground">Toegewezen aan</dt>
                  <dd className="text-sm text-navy-700">
                    {zaak.assigned_to.full_name}
                  </dd>
                </div>
              )}
              {zaak.date_closed && (
                <div>
                  <dt className="text-xs text-muted-foreground">Datum gesloten</dt>
                  <dd className="text-sm text-navy-700">
                    {formatDate(zaak.date_closed)}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* Quick activity */}
          <div className="rounded-lg border border-border bg-white p-6">
            <h2 className="mb-4 text-lg font-semibold text-navy-800">
              Recente activiteit
            </h2>
            {zaak.recent_activities && zaak.recent_activities.length > 0 ? (
              <div className="space-y-3">
                {zaak.recent_activities.slice(0, 5).map((activity) => (
                  <div
                    key={activity.id}
                    className="flex items-start gap-3 rounded-md border border-border p-3"
                  >
                    <span className="text-lg">
                      {ACTIVITY_ICONS[activity.activity_type] ?? "📌"}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-navy-800">
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
      )}

      {activeTab === "activiteiten" && (
        <div className="rounded-lg border border-border bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold text-navy-800">
            Alle activiteiten
          </h2>
          {zaak.recent_activities && zaak.recent_activities.length > 0 ? (
            <div className="space-y-3">
              {zaak.recent_activities.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-start gap-3 border-b border-border pb-3 last:border-0"
                >
                  <span className="text-lg">
                    {ACTIVITY_ICONS[activity.activity_type] ?? "📌"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-navy-800">
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
      )}

      {activeTab === "partijen" && (
        <div className="rounded-lg border border-border bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold text-navy-800">Partijen</h2>
          <div className="space-y-3">
            {zaak.client && (
              <div className="flex items-center justify-between rounded-md border border-border p-3">
                <div>
                  <Link
                    href={`/relaties/${zaak.client.id}`}
                    className="text-sm font-medium text-navy-700 hover:underline"
                  >
                    {zaak.client.name}
                  </Link>
                </div>
                <span className="rounded-full bg-navy-100 px-2.5 py-0.5 text-xs font-medium text-navy-700">
                  Client
                </span>
              </div>
            )}
            {zaak.opposing_party && (
              <div className="flex items-center justify-between rounded-md border border-border p-3">
                <div>
                  <Link
                    href={`/relaties/${zaak.opposing_party.id}`}
                    className="text-sm font-medium text-navy-700 hover:underline"
                  >
                    {zaak.opposing_party.name}
                  </Link>
                </div>
                <span className="rounded-full bg-orange-100 px-2.5 py-0.5 text-xs font-medium text-orange-700">
                  Wederpartij
                </span>
              </div>
            )}
            {zaak.parties &&
              zaak.parties.map((party) => (
                <div
                  key={party.id}
                  className="flex items-center justify-between rounded-md border border-border p-3"
                >
                  <div>
                    <Link
                      href={`/relaties/${party.contact.id}`}
                      className="text-sm font-medium text-navy-700 hover:underline"
                    >
                      {party.contact.name}
                    </Link>
                  </div>
                  <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">
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
