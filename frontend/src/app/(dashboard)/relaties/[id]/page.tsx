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
  Euro,
  FileText,
} from "lucide-react";
import { toast } from "sonner";
import {
  useRelation,
  useUpdateRelation,
  useDeleteRelation,
} from "@/hooks/use-relations";
import { useCases } from "@/hooks/use-cases";
import { formatDate, formatCurrency, formatDateShort } from "@/lib/utils";

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

const STATUS_BADGE: Record<string, string> = {
  nieuw: "bg-blue-50 text-blue-700 ring-blue-600/20",
  "14_dagenbrief": "bg-sky-50 text-sky-700 ring-sky-600/20",
  sommatie: "bg-amber-50 text-amber-700 ring-amber-600/20",
  dagvaarding: "bg-red-50 text-red-700 ring-red-600/20",
  vonnis: "bg-purple-50 text-purple-700 ring-purple-600/20",
  executie: "bg-red-50 text-red-800 ring-red-700/20",
  betaald: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  afgesloten: "bg-slate-50 text-slate-600 ring-slate-500/20",
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
  const { data: linkedCases } = useCases({
    search: contact?.name,
    per_page: 50,
  });

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
      <div className="space-y-6 animate-fade-in">
        <div className="h-8 w-48 rounded-md skeleton" />
        <div className="grid gap-6 lg:grid-cols-5">
          <div className="lg:col-span-3 h-48 rounded-xl skeleton" />
          <div className="lg:col-span-2 h-48 rounded-xl skeleton" />
        </div>
        <div className="h-32 rounded-xl skeleton" />
      </div>
    );
  }

  if (!contact) {
    return (
      <div className="py-20 text-center">
        <User className="mx-auto h-12 w-12 text-muted-foreground/30" />
        <p className="mt-4 text-base font-medium text-foreground">
          Relatie niet gevonden
        </p>
        <Link
          href="/relaties"
          className="mt-2 inline-block text-sm text-primary hover:underline"
        >
          ← Terug naar relaties
        </Link>
      </div>
    );
  }

  // Filter linked cases to only those that actually reference this contact
  const contactCases = linkedCases?.items.filter(
    (c) => c.client?.id === id || c.opposing_party?.id === id
  );

  const inputClass =
    "w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <Link
            href="/relaties"
            className="mt-1 rounded-lg p-2 hover:bg-muted transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-muted-foreground" />
          </Link>
          <div className="flex items-center gap-3">
            <div
              className={`flex h-11 w-11 items-center justify-center rounded-full ${
                contact.contact_type === "company"
                  ? "bg-blue-50 text-blue-600"
                  : "bg-violet-50 text-violet-600"
              }`}
            >
              {contact.contact_type === "company" ? (
                <Building2 className="h-5 w-5" />
              ) : (
                <User className="h-5 w-5" />
              )}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">
                {contact.name}
              </h1>
              <p className="text-sm text-muted-foreground">
                {contact.contact_type === "company" ? "Bedrijf" : "Persoon"}{" "}
                · Aangemaakt {formatDateShort(contact.created_at)}
                {contact.kvk_number && ` · KvK ${contact.kvk_number}`}
              </p>
            </div>
          </div>
        </div>
        <div className="flex gap-2 shrink-0">
          {editing ? (
            <>
              <button
                onClick={handleSave}
                disabled={updateRelation.isPending}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                <Check className="h-4 w-4" />
                {updateRelation.isPending ? "Opslaan..." : "Opslaan"}
              </button>
              <button
                onClick={() => setEditing(false)}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-sm hover:bg-muted transition-colors"
              >
                <X className="h-4 w-4" />
                Annuleren
              </button>
            </>
          ) : (
            <>
              <button
                onClick={startEditing}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-2 text-sm hover:bg-muted transition-colors"
              >
                <Pencil className="h-4 w-4" />
                Bewerken
              </button>
              <button
                onClick={handleDelete}
                className="rounded-lg border border-destructive/20 p-2 text-destructive hover:bg-destructive/10 transition-colors"
                title="Verwijderen"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Two column layout */}
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Left column: Contact info */}
        <div className="lg:col-span-3 space-y-6">
          <div className="rounded-xl border border-border bg-card p-6">
            <h2 className="mb-4 text-sm font-semibold text-card-foreground uppercase tracking-wider">
              Contactgegevens
            </h2>
            {editing ? (
              <div className="space-y-4">
                {contact.contact_type === "company" ? (
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
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
                  <div className="grid gap-4 grid-cols-2">
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        Voornaam
                      </label>
                      <input
                        type="text"
                        value={editForm.first_name}
                        onChange={(e) =>
                          updateEdit("first_name", e.target.value)
                        }
                        className={inputClass}
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        Achternaam
                      </label>
                      <input
                        type="text"
                        value={editForm.last_name}
                        onChange={(e) =>
                          updateEdit("last_name", e.target.value)
                        }
                        className={inputClass}
                      />
                    </div>
                  </div>
                )}
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
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
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
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
                {contact.contact_type === "company" && (
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        KvK-nummer
                      </label>
                      <input
                        type="text"
                        value={editForm.kvk_number}
                        onChange={(e) =>
                          updateEdit("kvk_number", e.target.value)
                        }
                        className={inputClass}
                        maxLength={8}
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        BTW-nummer
                      </label>
                      <input
                        type="text"
                        value={editForm.btw_number}
                        onChange={(e) =>
                          updateEdit("btw_number", e.target.value)
                        }
                        className={inputClass}
                      />
                    </div>
                  </div>
                )}
                <div className="pt-2">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                    Adres
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        Straat + huisnummer
                      </label>
                      <input
                        type="text"
                        value={editForm.visit_address}
                        onChange={(e) =>
                          updateEdit("visit_address", e.target.value)
                        }
                        className={inputClass}
                      />
                    </div>
                    <div className="grid gap-4 grid-cols-2">
                      <div>
                        <label className="block text-xs font-medium text-muted-foreground mb-1.5">
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
                        <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                          Plaats
                        </label>
                        <input
                          type="text"
                          value={editForm.visit_city}
                          onChange={(e) =>
                            updateEdit("visit_city", e.target.value)
                          }
                          className={inputClass}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {contact.email && (
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                      <Mail className="h-4 w-4 text-muted-foreground" />
                    </div>
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
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                      <Phone className="h-4 w-4 text-muted-foreground" />
                    </div>
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
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted mt-0.5">
                      <MapPin className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="text-sm text-foreground">
                      {contact.visit_address}
                      <br />
                      {contact.visit_postcode} {contact.visit_city}
                    </div>
                  </div>
                )}
                {contact.kvk_number && (
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">KvK</p>
                      <p className="text-sm font-mono text-foreground">
                        {contact.kvk_number}
                      </p>
                    </div>
                  </div>
                )}
                {contact.btw_number && (
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                      <Euro className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">BTW</p>
                      <p className="text-sm font-mono text-foreground">
                        {contact.btw_number}
                      </p>
                    </div>
                  </div>
                )}
                {!contact.email &&
                  !contact.phone &&
                  !contact.visit_address &&
                  !contact.kvk_number && (
                    <p className="text-sm text-muted-foreground">
                      Geen contactgegevens ingevuld
                    </p>
                  )}
              </div>
            )}
          </div>

          {/* Notes */}
          <div className="rounded-xl border border-border bg-card p-6">
            <h2 className="mb-3 text-sm font-semibold text-card-foreground uppercase tracking-wider">
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
              <p className="text-sm text-foreground whitespace-pre-wrap leading-relaxed">
                {contact.notes}
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">Geen notities</p>
            )}
          </div>
        </div>

        {/* Right column: Linked Cases */}
        <div className="lg:col-span-2">
          <div className="rounded-xl border border-border bg-card">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <div className="flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold text-card-foreground">
                  Gekoppelde zaken
                  {contactCases && contactCases.length > 0 && (
                    <span className="ml-1.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                      {contactCases.length}
                    </span>
                  )}
                </h2>
              </div>
              <Link
                href="/zaken/nieuw"
                className="text-xs text-primary hover:underline"
              >
                + Nieuwe zaak
              </Link>
            </div>
            {contactCases && contactCases.length > 0 ? (
              <div className="divide-y divide-border">
                {contactCases.map((zaak) => (
                  <Link
                    key={zaak.id}
                    href={`/zaken/${zaak.id}`}
                    className="flex items-center justify-between px-5 py-3.5 hover:bg-muted/40 transition-colors"
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-mono font-semibold text-foreground">
                          {zaak.case_number}
                        </span>
                        <span
                          className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset ${
                            STATUS_BADGE[zaak.status] ??
                            "bg-slate-50 text-slate-600 ring-slate-500/20"
                          }`}
                        >
                          {STATUS_LABELS[zaak.status] ?? zaak.status}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5 truncate">
                        {zaak.client?.id === id && zaak.opposing_party
                          ? `vs. ${zaak.opposing_party.name}`
                          : zaak.client?.name ?? zaak.description ?? ""}
                      </p>
                    </div>
                    <div className="text-right shrink-0 ml-3">
                      <p className="text-sm font-semibold text-foreground tabular-nums">
                        {formatCurrency(zaak.total_principal)}
                      </p>
                      <span
                        className={`text-[10px] font-medium ${
                          zaak.client?.id === id
                            ? "text-primary"
                            : "text-amber-600"
                        }`}
                      >
                        {zaak.client?.id === id ? "Client" : "Wederpartij"}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="px-5 py-8 text-center">
                <Briefcase className="mx-auto h-8 w-8 text-muted-foreground/30 mb-2" />
                <p className="text-sm text-muted-foreground">
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
      </div>
    </div>
  );
}
