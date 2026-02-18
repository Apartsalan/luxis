"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Building2,
  User,
  Mail,
  Phone,
  MapPin,
  Trash2,
  Pencil,
  Briefcase,
  X,
  Check,
} from "lucide-react";
import { toast } from "sonner";
import {
  useRelation,
  useUpdateRelation,
  useDeleteRelation,
} from "@/hooks/use-relations";
import { useCases } from "@/hooks/use-cases";
import { formatDate, formatCurrency } from "@/lib/utils";

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

export default function RelatieDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { data: contact, isLoading } = useRelation(id);
  const updateRelation = useUpdateRelation();
  const deleteRelation = useDeleteRelation();
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<Record<string, string>>({});

  // Fetch cases where this contact is client or opposing party
  const { data: linkedCases } = useCases({ search: contact?.name, per_page: 50 });

  const startEditing = () => {
    if (!contact) return;
    setEditForm({
      name: contact.name || "",
      first_name: contact.first_name || "",
      last_name: contact.last_name || "",
      email: contact.email || "",
      phone: contact.phone || "",
      kvk_number: contact.kvk_number || "",
      btw_number: contact.btw_number || "",
      visit_address: contact.visit_address || "",
      visit_postcode: contact.visit_postcode || "",
      visit_city: contact.visit_city || "",
      notes: contact.notes || "",
    });
    setEditing(true);
  };

  const handleSave = async () => {
    if (!contact) return;
    try {
      const data: Record<string, string | undefined> = {};
      if (contact.contact_type === "company") {
        data.name = editForm.name;
      } else {
        data.first_name = editForm.first_name;
        data.last_name = editForm.last_name;
        data.name = `${editForm.first_name} ${editForm.last_name}`.trim();
      }
      data.email = editForm.email || undefined;
      data.phone = editForm.phone || undefined;
      data.kvk_number = editForm.kvk_number || undefined;
      data.btw_number = editForm.btw_number || undefined;
      data.visit_address = editForm.visit_address || undefined;
      data.visit_postcode = editForm.visit_postcode || undefined;
      data.visit_city = editForm.visit_city || undefined;
      data.notes = editForm.notes || undefined;

      await updateRelation.mutateAsync({ id, data });
      toast.success("Relatie bijgewerkt");
      setEditing(false);
    } catch (err: any) {
      toast.error(err.message || "Kon niet opslaan");
    }
  };

  const handleDelete = async () => {
    if (!confirm("Weet je zeker dat je deze relatie wilt verwijderen?")) return;
    try {
      await deleteRelation.mutateAsync(id);
      toast.success("Relatie verwijderd");
      router.push("/relaties");
    } catch {
      toast.error("Kon de relatie niet verwijderen");
    }
  };

  const updateEdit = (field: string, value: string) => {
    setEditForm((prev) => ({ ...prev, [field]: value }));
  };

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl space-y-6 animate-fade-in">
        <div className="h-8 w-48 rounded-md skeleton" />
        <div className="grid gap-6 md:grid-cols-2">
          <div className="h-48 rounded-lg skeleton" />
          <div className="h-48 rounded-lg skeleton" />
        </div>
        <div className="h-32 rounded-lg skeleton" />
      </div>
    );
  }

  if (!contact) {
    return (
      <div className="py-20 text-center">
        <p className="text-muted-foreground">Relatie niet gevonden</p>
        <Link
          href="/relaties"
          className="mt-2 inline-block text-sm text-primary hover:underline"
        >
          Terug naar relaties
        </Link>
      </div>
    );
  }

  // Filter linked cases to only those that actually reference this contact
  const contactCases = linkedCases?.items.filter(
    (c) => c.client?.id === id || c.opposing_party?.id === id
  );

  const inputClass =
    "w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="mx-auto max-w-4xl space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/relaties"
            className="rounded-lg p-2 hover:bg-muted transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-muted-foreground" />
          </Link>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
              {contact.contact_type === "company" ? (
                <Building2 className="h-5 w-5 text-primary" />
              ) : (
                <User className="h-5 w-5 text-primary" />
              )}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">
                {contact.name}
              </h1>
              <p className="text-sm text-muted-foreground">
                {contact.contact_type === "company" ? "Bedrijf" : "Persoon"}{" "}
                &middot; Aangemaakt op {formatDate(contact.created_at)}
              </p>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          {editing ? (
            <>
              <button
                onClick={handleSave}
                disabled={updateRelation.isPending}
                className="inline-flex items-center gap-1 rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                <Check className="h-4 w-4" />
                {updateRelation.isPending ? "Opslaan..." : "Opslaan"}
              </button>
              <button
                onClick={() => setEditing(false)}
                className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-2 text-sm hover:bg-muted transition-colors"
              >
                <X className="h-4 w-4" />
                Annuleren
              </button>
            </>
          ) : (
            <>
              <button
                onClick={startEditing}
                className="inline-flex items-center gap-1 rounded-lg border border-border px-3 py-2 text-sm hover:bg-muted transition-colors"
              >
                <Pencil className="h-4 w-4" />
                Bewerken
              </button>
              <button
                onClick={handleDelete}
                className="inline-flex items-center gap-1 rounded-lg border border-destructive/20 px-3 py-2 text-sm text-destructive hover:bg-destructive/10 transition-colors"
              >
                <Trash2 className="h-4 w-4" />
                Verwijderen
              </button>
            </>
          )}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Contact info */}
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-4 text-base font-semibold text-foreground">
            Contactgegevens
          </h2>
          {editing ? (
            <div className="space-y-3">
              {contact.contact_type === "company" ? (
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">
                    Bedrijfsnaam
                  </label>
                  <input
                    type="text"
                    value={editForm.name}
                    onChange={(e) => updateEdit("name", e.target.value)}
                    className={inputClass}
                  />
                </div>
              ) : (
                <div className="grid gap-3 grid-cols-2">
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">
                      Voornaam
                    </label>
                    <input
                      type="text"
                      value={editForm.first_name}
                      onChange={(e) => updateEdit("first_name", e.target.value)}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">
                      Achternaam
                    </label>
                    <input
                      type="text"
                      value={editForm.last_name}
                      onChange={(e) => updateEdit("last_name", e.target.value)}
                      className={inputClass}
                    />
                  </div>
                </div>
              )}
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  E-mail
                </label>
                <input
                  type="email"
                  value={editForm.email}
                  onChange={(e) => updateEdit("email", e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Telefoon
                </label>
                <input
                  type="tel"
                  value={editForm.phone}
                  onChange={(e) => updateEdit("phone", e.target.value)}
                  className={inputClass}
                />
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {contact.email && (
                <div className="flex items-center gap-3">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <a
                    href={`mailto:${contact.email}`}
                    className="text-sm text-primary hover:underline"
                  >
                    {contact.email}
                  </a>
                </div>
              )}
              {contact.phone && (
                <div className="flex items-center gap-3">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <a
                    href={`tel:${contact.phone}`}
                    className="text-sm text-foreground hover:underline"
                  >
                    {contact.phone}
                  </a>
                </div>
              )}
              {contact.visit_address && (
                <div className="flex items-start gap-3">
                  <MapPin className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <div className="text-sm text-foreground">
                    {contact.visit_address}
                    <br />
                    {contact.visit_postcode} {contact.visit_city}
                  </div>
                </div>
              )}
              {!contact.email && !contact.phone && !contact.visit_address && (
                <p className="text-sm text-muted-foreground">
                  Geen contactgegevens
                </p>
              )}
            </div>
          )}
        </div>

        {/* Business info / Address */}
        <div className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-4 text-base font-semibold text-foreground">
            {contact.contact_type === "company"
              ? "Bedrijfsgegevens"
              : "Details"}
          </h2>
          {editing ? (
            <div className="space-y-3">
              {contact.contact_type === "company" && (
                <>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">
                      KvK-nummer
                    </label>
                    <input
                      type="text"
                      value={editForm.kvk_number}
                      onChange={(e) => updateEdit("kvk_number", e.target.value)}
                      className={inputClass}
                      maxLength={8}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1">
                      BTW-nummer
                    </label>
                    <input
                      type="text"
                      value={editForm.btw_number}
                      onChange={(e) => updateEdit("btw_number", e.target.value)}
                      className={inputClass}
                    />
                  </div>
                </>
              )}
              <h3 className="pt-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Adres
              </h3>
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Straat + huisnummer
                </label>
                <input
                  type="text"
                  value={editForm.visit_address}
                  onChange={(e) => updateEdit("visit_address", e.target.value)}
                  className={inputClass}
                />
              </div>
              <div className="grid gap-3 grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">
                    Postcode
                  </label>
                  <input
                    type="text"
                    value={editForm.visit_postcode}
                    onChange={(e) =>
                      updateEdit("visit_postcode", e.target.value)
                    }
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">
                    Plaats
                  </label>
                  <input
                    type="text"
                    value={editForm.visit_city}
                    onChange={(e) => updateEdit("visit_city", e.target.value)}
                    className={inputClass}
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {contact.kvk_number && (
                <div>
                  <p className="text-xs text-muted-foreground">KvK-nummer</p>
                  <p className="text-sm font-medium text-foreground">
                    {contact.kvk_number}
                  </p>
                </div>
              )}
              {contact.btw_number && (
                <div>
                  <p className="text-xs text-muted-foreground">BTW-nummer</p>
                  <p className="text-sm font-medium text-foreground">
                    {contact.btw_number}
                  </p>
                </div>
              )}
              {contact.first_name && (
                <div>
                  <p className="text-xs text-muted-foreground">Naam</p>
                  <p className="text-sm font-medium text-foreground">
                    {contact.first_name} {contact.last_name}
                  </p>
                </div>
              )}
              {contact.visit_address && (
                <div>
                  <p className="text-xs text-muted-foreground">Adres</p>
                  <p className="text-sm text-foreground">
                    {contact.visit_address}
                    <br />
                    {contact.visit_postcode} {contact.visit_city}
                  </p>
                </div>
              )}
              {!contact.kvk_number &&
                !contact.btw_number &&
                !contact.first_name &&
                !contact.visit_address && (
                  <p className="text-sm text-muted-foreground">
                    Geen extra gegevens
                  </p>
                )}
            </div>
          )}
        </div>
      </div>

      {/* Notes */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="mb-3 text-base font-semibold text-foreground">
          Notities
        </h2>
        {editing ? (
          <textarea
            value={editForm.notes}
            onChange={(e) => updateEdit("notes", e.target.value)}
            rows={4}
            className={`${inputClass} resize-none`}
            placeholder="Voeg notities toe..."
          />
        ) : contact.notes ? (
          <p className="text-sm text-foreground whitespace-pre-wrap">
            {contact.notes}
          </p>
        ) : (
          <p className="text-sm text-muted-foreground">Geen notities</p>
        )}
      </div>

      {/* Linked Cases */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-foreground">
            Gekoppelde zaken
          </h2>
          <Link
            href={`/zaken/nieuw`}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Briefcase className="h-3.5 w-3.5" />
            Nieuwe zaak
          </Link>
        </div>
        {contactCases && contactCases.length > 0 ? (
          <div className="space-y-2">
            {contactCases.map((zaak) => (
              <Link
                key={zaak.id}
                href={`/zaken/${zaak.id}`}
                className="flex items-center justify-between rounded-lg border border-border p-3 hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Briefcase className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {zaak.case_number}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {zaak.description || zaak.case_type}
                      {zaak.client?.id === id && zaak.opposing_party && (
                        <span> &middot; vs. {zaak.opposing_party.name}</span>
                      )}
                      {zaak.opposing_party?.id === id && zaak.client && (
                        <span> &middot; client: {zaak.client.name}</span>
                      )}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-foreground">
                    {formatCurrency(zaak.total_principal)}
                  </span>
                  <span
                    className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                      STATUS_COLORS[zaak.status] ?? "bg-gray-100 text-gray-600"
                    }`}
                  >
                    {STATUS_LABELS[zaak.status] ?? zaak.status}
                  </span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      zaak.client?.id === id
                        ? "bg-primary/10 text-primary"
                        : "bg-warning/10 text-warning"
                    }`}
                  >
                    {zaak.client?.id === id ? "Client" : "Wederpartij"}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="rounded-lg border border-dashed border-border py-8 text-center">
            <Briefcase className="mx-auto h-8 w-8 text-muted-foreground/30" />
            <p className="mt-2 text-sm text-muted-foreground">
              Nog geen gekoppelde zaken
            </p>
            <Link
              href="/zaken/nieuw"
              className="mt-1 inline-block text-sm text-primary hover:underline"
            >
              Maak een nieuwe zaak aan
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
