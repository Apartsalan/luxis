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
  Shield,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Clock,
} from "lucide-react";
import { toast } from "sonner";
import {
  useRelation,
  useUpdateRelation,
  useDeleteRelation,
} from "@/hooks/use-relations";
import { useCases } from "@/hooks/use-cases";
import { useModules } from "@/hooks/use-modules";
import { useKyc, useSaveKyc, useCompleteKyc } from "@/hooks/use-kyc";
import { formatDate, formatCurrency, formatDateShort } from "@/lib/utils";
import { ContactLinks } from "@/components/relations/contact-links";
import { useBreadcrumbs } from "@/components/layout/breadcrumb-context";

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

const KYC_STATUS_CONFIG: Record<string, { label: string; badge: string; icon: any }> = {
  niet_gestart: {
    label: "Niet gestart",
    badge: "bg-red-50 text-red-700 ring-red-600/20",
    icon: ShieldAlert,
  },
  in_behandeling: {
    label: "In behandeling",
    badge: "bg-amber-50 text-amber-700 ring-amber-600/20",
    icon: Shield,
  },
  voltooid: {
    label: "Voltooid",
    badge: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
    icon: ShieldCheck,
  },
  verlopen: {
    label: "Verlopen",
    badge: "bg-red-50 text-red-700 ring-red-600/20",
    icon: ShieldAlert,
  },
};

const ID_TYPE_LABELS: Record<string, string> = {
  paspoort: "Paspoort",
  id_kaart: "ID-kaart",
  rijbewijs: "Rijbewijs",
  verblijfsdocument: "Verblijfsdocument",
  kvk_uittreksel: "KvK-uittreksel",
  anders: "Anders",
};

const RISK_LABELS: Record<string, { label: string; color: string }> = {
  laag: { label: "Laag", color: "bg-emerald-50 text-emerald-700" },
  midden: { label: "Midden", color: "bg-amber-50 text-amber-700" },
  hoog: { label: "Hoog", color: "bg-red-50 text-red-700" },
};

export default function RelatieDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { hasModule } = useModules();
  const { data: contact, isLoading } = useRelation(id);
  const updateRelation = useUpdateRelation();
  const deleteRelation = useDeleteRelation();
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<Record<string, string>>({});

  // KYC (only when wwft module enabled)
  const { data: kycData, isLoading: kycLoading } = useKyc(hasModule("wwft") ? id : undefined);
  const saveKyc = useSaveKyc();
  const completeKyc = useCompleteKyc();
  const [kycOpen, setKycOpen] = useState(false);
  const [kycEditing, setKycEditing] = useState(false);
  const [kycForm, setKycForm] = useState<Record<string, any>>({});

  // Set breadcrumb label to contact name
  useBreadcrumbs(contact ? [{ segment: id, label: contact.name }] : []);

  // Fetch cases where this contact is client or opposing party
  const { data: linkedCases } = useCases({
    client_id: id,
    per_page: 50,
  });

  const startEditing = () => {
    if (!contact) return;
    setEditForm({
      name: contact.name || "",
      first_name: contact.first_name || "",
      last_name: contact.last_name || "",
      date_of_birth: contact.date_of_birth || "",
      email: contact.email || "",
      phone: contact.phone || "",
      kvk_number: contact.kvk_number || "",
      btw_number: contact.btw_number || "",
      visit_address: contact.visit_address || "",
      visit_postcode: contact.visit_postcode || "",
      visit_city: contact.visit_city || "",
      postal_address: contact.postal_address || "",
      postal_postcode: contact.postal_postcode || "",
      postal_city: contact.postal_city || "",
      default_hourly_rate: contact.default_hourly_rate?.toString() || "",
      payment_term_days: contact.payment_term_days?.toString() || "",
      billing_email: contact.billing_email || "",
      iban: contact.iban || "",
      notes: contact.notes || "",
    });
    setEditing(true);
  };

  const handleSave = async () => {
    if (!contact) return;
    try {
      const data: Record<string, string | null> = {};
      if (contact.contact_type === "company") {
        data.name = editForm.name;
      } else {
        data.first_name = editForm.first_name;
        data.last_name = editForm.last_name;
        data.name = `${editForm.first_name} ${editForm.last_name}`.trim();
        data.date_of_birth = editForm.date_of_birth || null;
      }
      data.email = editForm.email?.trim() || null;
      data.phone = editForm.phone?.trim() || null;
      data.kvk_number = editForm.kvk_number?.trim() || null;
      data.btw_number = editForm.btw_number?.trim() || null;
      data.visit_address = editForm.visit_address?.trim() || null;
      data.visit_postcode = editForm.visit_postcode?.trim() || null;
      data.visit_city = editForm.visit_city?.trim() || null;
      data.postal_address = editForm.postal_address?.trim() || null;
      data.postal_postcode = editForm.postal_postcode?.trim() || null;
      data.postal_city = editForm.postal_city?.trim() || null;
      data.default_hourly_rate = editForm.default_hourly_rate ? editForm.default_hourly_rate : null;
      data.payment_term_days = editForm.payment_term_days ? editForm.payment_term_days : null;
      data.billing_email = editForm.billing_email?.trim() || null;
      data.iban = editForm.iban?.trim() || null;
      data.notes = editForm.notes?.trim() || null;

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

  // KYC handlers
  const startKycEditing = () => {
    setKycForm({
      risk_level: kycData?.risk_level || "",
      risk_notes: kycData?.risk_notes || "",
      id_type: kycData?.id_type || "",
      id_number: kycData?.id_number || "",
      id_expiry_date: kycData?.id_expiry_date || "",
      id_verified_at: kycData?.id_verified_at || "",
      ubo_name: kycData?.ubo_name || "",
      ubo_dob: kycData?.ubo_dob || "",
      ubo_nationality: kycData?.ubo_nationality || "",
      ubo_percentage: kycData?.ubo_percentage || "",
      ubo_verified_at: kycData?.ubo_verified_at || "",
      pep_checked: kycData?.pep_checked || false,
      pep_is_pep: kycData?.pep_is_pep || false,
      pep_notes: kycData?.pep_notes || "",
      sanctions_checked: kycData?.sanctions_checked || false,
      sanctions_hit: kycData?.sanctions_hit || false,
      sanctions_notes: kycData?.sanctions_notes || "",
      source_of_funds: kycData?.source_of_funds || "",
      source_of_funds_verified: kycData?.source_of_funds_verified || false,
      notes: kycData?.notes || "",
    });
    setKycEditing(true);
    setKycOpen(true);
  };

  const handleKycSave = async () => {
    try {
      const data: Record<string, any> = { contact_id: id };
      data.risk_level = kycForm.risk_level || null;
      data.risk_notes = kycForm.risk_notes?.trim() || null;
      data.id_type = kycForm.id_type || null;
      data.id_number = kycForm.id_number?.trim() || null;
      data.id_expiry_date = kycForm.id_expiry_date || null;
      data.id_verified_at = kycForm.id_verified_at || null;
      data.ubo_name = kycForm.ubo_name?.trim() || null;
      data.ubo_dob = kycForm.ubo_dob || null;
      data.ubo_nationality = kycForm.ubo_nationality?.trim() || null;
      data.ubo_percentage = kycForm.ubo_percentage?.trim() || null;
      data.ubo_verified_at = kycForm.ubo_verified_at || null;
      data.pep_checked = kycForm.pep_checked;
      data.pep_is_pep = kycForm.pep_is_pep;
      data.pep_notes = kycForm.pep_notes?.trim() || null;
      data.sanctions_checked = kycForm.sanctions_checked;
      data.sanctions_hit = kycForm.sanctions_hit;
      data.sanctions_notes = kycForm.sanctions_notes?.trim() || null;
      data.source_of_funds = kycForm.source_of_funds?.trim() || null;
      data.source_of_funds_verified = kycForm.source_of_funds_verified;
      data.notes = kycForm.notes?.trim() || null;

      await saveKyc.mutateAsync(data);
      toast.success("WWFT-gegevens opgeslagen");
      setKycEditing(false);
    } catch (err: any) {
      toast.error(err.message || "Kon niet opslaan");
    }
  };

  const handleKycComplete = async () => {
    if (!kycData?.id) return;
    try {
      await completeKyc.mutateAsync({ id: kycData.id });
      toast.success("KYC verificatie afgerond");
    } catch (err: any) {
      toast.error(err.message || "Kon verificatie niet afronden");
    }
  };

  const updateKycField = (field: string, value: any) => {
    setKycForm((prev) => ({ ...prev, [field]: value }));
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

  // Backend already filters: client, opposing party, OR case party (advocaat etc.)
  const contactCases = linkedCases?.items;

  const kycStatus = kycData?.status || "niet_gestart";
  const kycConfig = KYC_STATUS_CONFIG[kycStatus] || KYC_STATUS_CONFIG.niet_gestart;
  const KycIcon = kycConfig.icon;

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
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-foreground">
                  {contact.name}
                </h1>
                {/* KYC badge in header */}
                {hasModule("wwft") && (
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ring-inset ${kycConfig.badge}`}
                  >
                    <KycIcon className="h-3 w-3" />
                    WWFT: {kycConfig.label}
                  </span>
                )}
              </div>
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
                {contact.contact_type === "person" && (
                  <div>
                    <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                      Geboortedatum
                    </label>
                    <input
                      type="date"
                      value={editForm.date_of_birth}
                      onChange={(e) =>
                        updateEdit("date_of_birth", e.target.value)
                      }
                      className={inputClass}
                    />
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
                    Bezoekadres
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
                <div className="pt-2">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                    Postadres <span className="font-normal normal-case">(optioneel, indien afwijkend)</span>
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        Postbus / straat
                      </label>
                      <input
                        type="text"
                        value={editForm.postal_address}
                        onChange={(e) =>
                          updateEdit("postal_address", e.target.value)
                        }
                        className={inputClass}
                        placeholder="bijv. Postbus 123"
                      />
                    </div>
                    <div className="grid gap-4 grid-cols-2">
                      <div>
                        <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                          Postcode
                        </label>
                        <input
                          type="text"
                          value={editForm.postal_postcode}
                          onChange={(e) =>
                            updateEdit("postal_postcode", e.target.value)
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
                          value={editForm.postal_city}
                          onChange={(e) =>
                            updateEdit("postal_city", e.target.value)
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
                {contact.contact_type === "person" && contact.date_of_birth && (
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Geboortedatum</p>
                      <p className="text-sm text-foreground">
                        {formatDate(contact.date_of_birth)}
                      </p>
                    </div>
                  </div>
                )}
                {contact.visit_address && (
                  <div className="flex items-start gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted mt-0.5">
                      <MapPin className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">
                        {contact.postal_address ? "Bezoekadres" : "Adres"}
                      </p>
                      <p className="text-sm text-foreground">
                        {contact.visit_address}
                        <br />
                        {contact.visit_postcode} {contact.visit_city}
                      </p>
                    </div>
                  </div>
                )}
                {contact.postal_address && (
                  <div className="flex items-start gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted mt-0.5">
                      <MapPin className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Postadres</p>
                      <p className="text-sm text-foreground">
                        {contact.postal_address}
                        <br />
                        {contact.postal_postcode} {contact.postal_city}
                      </p>
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

          {/* Billing Profile (F6) */}
          <div className="rounded-xl border border-border bg-card p-6">
            <h2 className="mb-3 text-sm font-semibold text-card-foreground uppercase tracking-wider">
              Facturatie
            </h2>
            {editing ? (
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Standaard uurtarief (€)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={editForm.default_hourly_rate}
                    onChange={(e) => updateEdit("default_hourly_rate", e.target.value)}
                    className={inputClass}
                    placeholder="Bijv. 250.00"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Betalingstermijn (dagen)</label>
                  <input
                    type="number"
                    value={editForm.payment_term_days}
                    onChange={(e) => updateEdit("payment_term_days", e.target.value)}
                    className={inputClass}
                    placeholder="Bijv. 14"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">Factuur e-mail</label>
                  <input
                    type="email"
                    value={editForm.billing_email}
                    onChange={(e) => updateEdit("billing_email", e.target.value)}
                    className={inputClass}
                    placeholder="facturen@bedrijf.nl"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1">IBAN</label>
                  <input
                    type="text"
                    value={editForm.iban}
                    onChange={(e) => updateEdit("iban", e.target.value)}
                    className={inputClass}
                    placeholder="NL00 BANK 0000 0000 00"
                  />
                </div>
              </div>
            ) : (contact.default_hourly_rate || contact.payment_term_days || contact.billing_email || contact.iban) ? (
              <dl className="grid gap-3 sm:grid-cols-2">
                {contact.default_hourly_rate && (
                  <div>
                    <dt className="text-xs text-muted-foreground">Uurtarief</dt>
                    <dd className="text-sm font-medium text-foreground">€ {contact.default_hourly_rate.toFixed(2)}</dd>
                  </div>
                )}
                {contact.payment_term_days && (
                  <div>
                    <dt className="text-xs text-muted-foreground">Betalingstermijn</dt>
                    <dd className="text-sm font-medium text-foreground">{contact.payment_term_days} dagen</dd>
                  </div>
                )}
                {contact.billing_email && (
                  <div>
                    <dt className="text-xs text-muted-foreground">Factuur e-mail</dt>
                    <dd className="text-sm text-foreground">{contact.billing_email}</dd>
                  </div>
                )}
                {contact.iban && (
                  <div>
                    <dt className="text-xs text-muted-foreground">IBAN</dt>
                    <dd className="text-sm font-mono text-foreground">{contact.iban}</dd>
                  </div>
                )}
              </dl>
            ) : (
              <p className="text-sm text-muted-foreground">Geen facturatiegegevens ingesteld</p>
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

        {/* Right column: Links + Cases */}
        <div className="lg:col-span-2 space-y-6">
          {/* Contact Links (companies for persons, persons for companies) */}
          <ContactLinks
            contactId={id}
            contactType={contact.contact_type}
            links={
              contact.contact_type === "person"
                ? contact.linked_companies ?? []
                : contact.linked_persons ?? []
            }
          />

          <div className="rounded-xl border border-border bg-card">
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <div className="flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold text-card-foreground">
                  Gekoppelde dossiers
                  {contactCases && contactCases.length > 0 && (
                    <span className="ml-1.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                      {contactCases.length}
                    </span>
                  )}
                </h2>
              </div>
              <div className="flex items-center gap-3">
                <Link
                  href={`/zaken/nieuw?client_id=${id}&client_name=${encodeURIComponent(contact?.name || "")}`}
                  className="text-xs text-primary hover:underline"
                >
                  + Als client
                </Link>
                <span className="text-xs text-muted-foreground">|</span>
                <Link
                  href={`/zaken/nieuw?opposing_party_id=${id}&opposing_party_name=${encodeURIComponent(contact?.name || "")}`}
                  className="text-xs text-amber-600 hover:underline"
                >
                  + Als wederpartij
                </Link>
              </div>
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
                            : zaak.opposing_party?.id === id
                            ? "text-amber-600"
                            : "text-violet-600"
                        }`}
                      >
                        {zaak.client?.id === id ? "Client" : zaak.opposing_party?.id === id ? "Wederpartij" : "Partij"}
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="px-5 py-8 text-center">
                <Briefcase className="mx-auto h-8 w-8 text-muted-foreground/30 mb-2" />
                <p className="text-sm text-muted-foreground">
                  Nog geen gekoppelde dossiers
                </p>
                <Link
                  href={`/zaken/nieuw?client_id=${id}&client_name=${encodeURIComponent(contact?.name || "")}`}
                  className="mt-1 inline-block text-sm text-primary hover:underline"
                >
                  Maak een nieuw dossier aan
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── WWFT / KYC Section (only when wwft module enabled) ────────── */}
      {hasModule("wwft") && <div className="rounded-xl border border-border bg-card overflow-hidden">
        {/* Collapsible header */}
        <button
          type="button"
          onClick={() => setKycOpen(!kycOpen)}
          className="flex w-full items-center justify-between px-6 py-4 hover:bg-muted/30 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div
              className={`flex h-9 w-9 items-center justify-center rounded-lg ${
                kycStatus === "voltooid"
                  ? "bg-emerald-50 text-emerald-600"
                  : kycStatus === "in_behandeling"
                  ? "bg-amber-50 text-amber-600"
                  : "bg-red-50 text-red-600"
              }`}
            >
              <KycIcon className="h-5 w-5" />
            </div>
            <div className="text-left">
              <h2 className="text-sm font-semibold text-foreground">
                WWFT / Cliëntidentificatie
              </h2>
              <p className="text-xs text-muted-foreground">
                {kycStatus === "voltooid" && kycData?.verification_date
                  ? `Geverifieerd op ${formatDateShort(kycData.verification_date)}`
                  : kycStatus === "in_behandeling"
                  ? "Verificatie in behandeling"
                  : "Nog niet geverifieerd — verplicht per WWFT"}
                {kycData?.risk_level && (
                  <span
                    className={`ml-2 inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-medium ${
                      RISK_LABELS[kycData.risk_level]?.color || ""
                    }`}
                  >
                    Risico: {RISK_LABELS[kycData.risk_level]?.label}
                  </span>
                )}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {!kycEditing && kycStatus !== "voltooid" && (
              <span
                onClick={(e) => {
                  e.stopPropagation();
                  startKycEditing();
                }}
                className="text-xs text-primary hover:underline cursor-pointer"
              >
                {kycData ? "Bewerken" : "Starten"}
              </span>
            )}
            {kycOpen ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </button>

        {/* Collapsible content */}
        {kycOpen && (
          <div className="border-t border-border px-6 py-5 space-y-6">
            {kycEditing ? (
              /* ── KYC Edit Form ──────────────────────────────────── */
              <div className="space-y-6">
                {/* Risk Classification */}
                <div>
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                    Risicoclassificatie
                  </h3>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        Risiconiveau *
                      </label>
                      <select
                        value={kycForm.risk_level}
                        onChange={(e) =>
                          updateKycField("risk_level", e.target.value)
                        }
                        className={inputClass}
                      >
                        <option value="">Selecteer...</option>
                        <option value="laag">Laag</option>
                        <option value="midden">Midden</option>
                        <option value="hoog">Hoog</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        Toelichting risico
                      </label>
                      <input
                        type="text"
                        value={kycForm.risk_notes}
                        onChange={(e) =>
                          updateKycField("risk_notes", e.target.value)
                        }
                        className={inputClass}
                        placeholder="Waarom dit risiconiveau?"
                      />
                    </div>
                  </div>
                </div>

                {/* Identity Document */}
                <div>
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                    Identiteitsdocument
                  </h3>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        Type document *
                      </label>
                      <select
                        value={kycForm.id_type}
                        onChange={(e) =>
                          updateKycField("id_type", e.target.value)
                        }
                        className={inputClass}
                      >
                        <option value="">Selecteer...</option>
                        <option value="paspoort">Paspoort</option>
                        <option value="id_kaart">ID-kaart</option>
                        <option value="rijbewijs">Rijbewijs</option>
                        <option value="verblijfsdocument">
                          Verblijfsdocument
                        </option>
                        <option value="kvk_uittreksel">KvK-uittreksel</option>
                        <option value="anders">Anders</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        Documentnummer *
                      </label>
                      <input
                        type="text"
                        value={kycForm.id_number}
                        onChange={(e) =>
                          updateKycField("id_number", e.target.value)
                        }
                        className={inputClass}
                        placeholder="Bijv. NW1234567"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        Vervaldatum document
                      </label>
                      <input
                        type="date"
                        value={kycForm.id_expiry_date}
                        onChange={(e) =>
                          updateKycField("id_expiry_date", e.target.value)
                        }
                        className={inputClass}
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                        Datum verificatie *
                      </label>
                      <input
                        type="date"
                        value={kycForm.id_verified_at}
                        onChange={(e) =>
                          updateKycField("id_verified_at", e.target.value)
                        }
                        className={inputClass}
                      />
                    </div>
                  </div>
                </div>

                {/* UBO — only for companies */}
                {contact.contact_type === "company" && (
                  <div>
                    <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                      UBO (Ultimate Beneficial Owner)
                    </h3>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div>
                        <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                          Naam UBO *
                        </label>
                        <input
                          type="text"
                          value={kycForm.ubo_name}
                          onChange={(e) =>
                            updateKycField("ubo_name", e.target.value)
                          }
                          className={inputClass}
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                          Geboortedatum UBO
                        </label>
                        <input
                          type="date"
                          value={kycForm.ubo_dob}
                          onChange={(e) =>
                            updateKycField("ubo_dob", e.target.value)
                          }
                          className={inputClass}
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                          Nationaliteit
                        </label>
                        <input
                          type="text"
                          value={kycForm.ubo_nationality}
                          onChange={(e) =>
                            updateKycField("ubo_nationality", e.target.value)
                          }
                          className={inputClass}
                          placeholder="Bijv. Nederlands"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                          Belang (%)
                        </label>
                        <select
                          value={kycForm.ubo_percentage}
                          onChange={(e) =>
                            updateKycField("ubo_percentage", e.target.value)
                          }
                          className={inputClass}
                        >
                          <option value="">Selecteer...</option>
                          <option value="25-50%">25-50%</option>
                          <option value=">50%">Meer dan 50%</option>
                          <option value="100%">100%</option>
                        </select>
                      </div>
                    </div>
                  </div>
                )}

                {/* PEP + Sanctions checks */}
                <div>
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                    Verplichte controles
                  </h3>
                  <div className="space-y-3">
                    {/* PEP */}
                    <div className="rounded-lg border border-border p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-foreground">
                          PEP-controle (Politically Exposed Person) *
                        </span>
                        <label className="relative inline-flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={kycForm.pep_checked}
                            onChange={(e) =>
                              updateKycField("pep_checked", e.target.checked)
                            }
                            className="sr-only peer"
                          />
                          <div className="w-9 h-5 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all"></div>
                          <span className="text-xs text-muted-foreground">
                            Gecontroleerd
                          </span>
                        </label>
                      </div>
                      {kycForm.pep_checked && (
                        <div className="flex items-center gap-4">
                          <label className="flex items-center gap-2 text-sm">
                            <input
                              type="checkbox"
                              checked={kycForm.pep_is_pep}
                              onChange={(e) =>
                                updateKycField("pep_is_pep", e.target.checked)
                              }
                              className="rounded border-gray-300"
                            />
                            Is PEP
                          </label>
                          <input
                            type="text"
                            value={kycForm.pep_notes}
                            onChange={(e) =>
                              updateKycField("pep_notes", e.target.value)
                            }
                            className={`${inputClass} flex-1`}
                            placeholder="Toelichting..."
                          />
                        </div>
                      )}
                    </div>

                    {/* Sanctions */}
                    <div className="rounded-lg border border-border p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-foreground">
                          Sanctielijstcontrole *
                        </span>
                        <label className="relative inline-flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={kycForm.sanctions_checked}
                            onChange={(e) =>
                              updateKycField(
                                "sanctions_checked",
                                e.target.checked
                              )
                            }
                            className="sr-only peer"
                          />
                          <div className="w-9 h-5 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all"></div>
                          <span className="text-xs text-muted-foreground">
                            Gecontroleerd
                          </span>
                        </label>
                      </div>
                      {kycForm.sanctions_checked && (
                        <div className="flex items-center gap-4">
                          <label className="flex items-center gap-2 text-sm">
                            <input
                              type="checkbox"
                              checked={kycForm.sanctions_hit}
                              onChange={(e) =>
                                updateKycField(
                                  "sanctions_hit",
                                  e.target.checked
                                )
                              }
                              className="rounded border-gray-300"
                            />
                            Hit gevonden
                          </label>
                          <input
                            type="text"
                            value={kycForm.sanctions_notes}
                            onChange={(e) =>
                              updateKycField(
                                "sanctions_notes",
                                e.target.value
                              )
                            }
                            className={`${inputClass} flex-1`}
                            placeholder="Toelichting..."
                          />
                        </div>
                      )}
                    </div>

                    {/* Source of Funds */}
                    <div className="rounded-lg border border-border p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-foreground">
                          Herkomst middelen
                        </span>
                        <label className="relative inline-flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={kycForm.source_of_funds_verified}
                            onChange={(e) =>
                              updateKycField(
                                "source_of_funds_verified",
                                e.target.checked
                              )
                            }
                            className="sr-only peer"
                          />
                          <div className="w-9 h-5 bg-gray-200 peer-focus:ring-2 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:bg-primary after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all"></div>
                          <span className="text-xs text-muted-foreground">
                            Geverifieerd
                          </span>
                        </label>
                      </div>
                      <input
                        type="text"
                        value={kycForm.source_of_funds}
                        onChange={(e) =>
                          updateKycField("source_of_funds", e.target.value)
                        }
                        className={inputClass}
                        placeholder="Bijv. bedrijfsomzet, salaris, etc."
                      />
                    </div>
                  </div>
                </div>

                {/* Notes */}
                <div>
                  <label className="block text-xs font-medium text-muted-foreground mb-1.5">
                    Opmerkingen
                  </label>
                  <textarea
                    value={kycForm.notes}
                    onChange={(e) => updateKycField("notes", e.target.value)}
                    rows={2}
                    className={`${inputClass} resize-none`}
                    placeholder="Eventuele opmerkingen bij de verificatie..."
                  />
                </div>

                {/* Save / Cancel */}
                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={handleKycSave}
                    disabled={saveKyc.isPending}
                    className="rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                  >
                    {saveKyc.isPending ? "Opslaan..." : "Opslaan"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setKycEditing(false)}
                    className="rounded-lg border border-border px-4 py-2.5 text-sm hover:bg-muted transition-colors"
                  >
                    Annuleren
                  </button>
                </div>
              </div>
            ) : kycData ? (
              /* ── KYC Read-Only View ─────────────────────────────── */
              <div className="space-y-5">
                {/* Summary grid */}
                <div className="grid gap-4 sm:grid-cols-3">
                  {/* Risk level */}
                  <div className="rounded-lg bg-muted/50 p-3">
                    <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                      Risiconiveau
                    </p>
                    {kycData.risk_level ? (
                      <span
                        className={`mt-1 inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                          RISK_LABELS[kycData.risk_level]?.color || ""
                        }`}
                      >
                        {RISK_LABELS[kycData.risk_level]?.label}
                      </span>
                    ) : (
                      <p className="mt-1 text-sm text-muted-foreground">—</p>
                    )}
                  </div>

                  {/* ID Document */}
                  <div className="rounded-lg bg-muted/50 p-3">
                    <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                      ID-document
                    </p>
                    {kycData.id_type ? (
                      <p className="mt-1 text-sm text-foreground">
                        {ID_TYPE_LABELS[kycData.id_type] || kycData.id_type}
                        {kycData.id_number && (
                          <span className="ml-1 font-mono text-xs text-muted-foreground">
                            ({kycData.id_number})
                          </span>
                        )}
                      </p>
                    ) : (
                      <p className="mt-1 text-sm text-muted-foreground">—</p>
                    )}
                  </div>

                  {/* Next Review */}
                  <div className="rounded-lg bg-muted/50 p-3">
                    <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                      Volgende review
                    </p>
                    {kycData.next_review_date ? (
                      <p className="mt-1 text-sm text-foreground">
                        {formatDateShort(kycData.next_review_date)}
                      </p>
                    ) : (
                      <p className="mt-1 text-sm text-muted-foreground">—</p>
                    )}
                  </div>
                </div>

                {/* Checks */}
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="flex items-center gap-2">
                    {kycData.pep_checked ? (
                      <Check className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <X className="h-4 w-4 text-red-400" />
                    )}
                    <span className="text-sm text-foreground">
                      PEP-controle
                      {kycData.pep_is_pep && (
                        <span className="ml-1 text-xs text-red-600 font-medium">
                          (PEP!)
                        </span>
                      )}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {kycData.sanctions_checked ? (
                      <Check className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <X className="h-4 w-4 text-red-400" />
                    )}
                    <span className="text-sm text-foreground">
                      Sanctielijst
                      {kycData.sanctions_hit && (
                        <span className="ml-1 text-xs text-red-600 font-medium">
                          (Hit!)
                        </span>
                      )}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {kycData.source_of_funds_verified ? (
                      <Check className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <X className="h-4 w-4 text-red-400" />
                    )}
                    <span className="text-sm text-foreground">
                      Herkomst middelen
                    </span>
                  </div>
                  {contact.contact_type === "company" && (
                    <div className="flex items-center gap-2">
                      {kycData.ubo_name ? (
                        <Check className="h-4 w-4 text-emerald-500" />
                      ) : (
                        <X className="h-4 w-4 text-red-400" />
                      )}
                      <span className="text-sm text-foreground">
                        UBO-registratie
                        {kycData.ubo_name && (
                          <span className="ml-1 text-xs text-muted-foreground">
                            ({kycData.ubo_name})
                          </span>
                        )}
                      </span>
                    </div>
                  )}
                </div>

                {/* Verified by */}
                {kycData.verified_by && (
                  <div className="text-xs text-muted-foreground">
                    Geverifieerd door {kycData.verified_by.full_name}
                    {kycData.verification_date &&
                      ` op ${formatDateShort(kycData.verification_date)}`}
                  </div>
                )}

                {/* Notes */}
                {kycData.notes && (
                  <div className="text-sm text-foreground whitespace-pre-wrap">
                    {kycData.notes}
                  </div>
                )}

                {/* Action buttons */}
                <div className="flex gap-3 pt-1">
                  {kycStatus !== "voltooid" && (
                    <button
                      type="button"
                      onClick={handleKycComplete}
                      disabled={completeKyc.isPending}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50 transition-colors"
                    >
                      <ShieldCheck className="h-4 w-4" />
                      {completeKyc.isPending
                        ? "Afronden..."
                        : "Verificatie afronden"}
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={startKycEditing}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-border px-4 py-2 text-sm hover:bg-muted transition-colors"
                  >
                    <Pencil className="h-4 w-4" />
                    Bewerken
                  </button>
                </div>
              </div>
            ) : (
              /* ── No KYC yet ─────────────────────────────────────── */
              <div className="py-4 text-center">
                <ShieldAlert className="mx-auto h-10 w-10 text-red-300 mb-3" />
                <p className="text-sm font-medium text-foreground">
                  Nog geen WWFT-verificatie gestart
                </p>
                <p className="mt-1 text-xs text-muted-foreground max-w-sm mx-auto">
                  De WWFT verplicht advocatenkantoren om de identiteit van
                  cliënten te verifiëren voordat juridische diensten worden
                  verleend.
                </p>
                <button
                  type="button"
                  onClick={startKycEditing}
                  className="mt-4 inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  <Shield className="h-4 w-4" />
                  Verificatie starten
                </button>
              </div>
            )}
          </div>
        )}
      </div>}
    </div>
  );
}
