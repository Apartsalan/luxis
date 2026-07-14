"use client";

import { useState, useEffect, useCallback } from "react";
import { useConfirm } from "@/components/confirm-dialog";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  Download,
  File,
  FileText,
  Loader2,
  User,
  Trash2,
  Pencil,
  Upload,
  X,
  Check,
  Plus,
  Edit2,
} from "lucide-react";
import { toast } from "sonner";
import {
  useRelation,
  useUpdateRelation,
  useDeleteRelation,
} from "@/hooks/use-relations";
import {
  useContactTerms,
  useUploadContactTerms,
  useUpdateContactTerms,
  useDeleteContactTerms,
  downloadContactTermsFile,
  type ContactTerms,
  type ContactTermsCreate,
  type ContactTermsUpdate,
} from "@/hooks/use-contact-terms";
import { useCases } from "@/hooks/use-cases";
import { useModules } from "@/hooks/use-modules";
import { useKyc, useSaveKyc, useCompleteKyc, type KycFormData } from "@/hooks/use-kyc";
import { formatDateShort } from "@/lib/utils";
import { ContactLinks } from "@/components/relations/contact-links";
import { useBreadcrumbs } from "@/components/layout/breadcrumb-context";
import { tokenStore } from "@/lib/token-store";
import {
  ContactInfoSection,
  LinkedCasesSection,
  KycSection,
  KYC_STATUS_CONFIG,
  type KycFormState,
} from "@/components/relations/detail";

export default function RelatieDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { hasModule } = useModules();
  const { data: contact, isLoading } = useRelation(id);
  const updateRelation = useUpdateRelation();
  const deleteRelation = useDeleteRelation();
  const { confirm, ConfirmDialog: ConfirmDialogEl } = useConfirm();
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState<Record<string, string>>({});

  // KYC (only when wwft module enabled)
  const { data: kycData, isLoading: kycLoading } = useKyc(hasModule("wwft") ? id : undefined);
  const saveKyc = useSaveKyc();
  const completeKyc = useCompleteKyc();
  const [kycOpen, setKycOpen] = useState(false);
  const [kycEditing, setKycEditing] = useState(false);
  const [kycForm, setKycForm] = useState<KycFormState>({
    risk_level: "",
    risk_notes: "",
    id_type: "",
    id_number: "",
    id_expiry_date: "",
    id_verified_at: "",
    ubo_name: "",
    ubo_dob: "",
    ubo_nationality: "",
    ubo_percentage: "",
    ubo_verified_at: "",
    pep_checked: false,
    pep_is_pep: false,
    pep_notes: "",
    sanctions_checked: false,
    sanctions_hit: false,
    sanctions_notes: "",
    source_of_funds: "",
    source_of_funds_verified: false,
    notes: "",
  });

  // Set breadcrumb label to contact name
  useBreadcrumbs(contact ? [{ segment: id, label: contact.name }] : []);

  // UX-16: Warn on unsaved changes (beforeunload)
  useEffect(() => {
    if (!editing) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [editing]);

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
      salutation: contact.salutation || "unknown",
      date_of_birth: contact.date_of_birth || "",
      email: contact.email || "",
      phone: contact.phone || "",
      kvk_number: contact.kvk_number || "",
      btw_number: contact.btw_number || "",
      legal_form: contact.legal_form || "",
      visit_address: contact.visit_address || "",
      visit_postcode: contact.visit_postcode || "",
      visit_city: contact.visit_city || "",
      visit_country: contact.visit_country || "",
      postal_address: contact.postal_address || "",
      postal_postcode: contact.postal_postcode || "",
      postal_city: contact.postal_city || "",
      postal_country: contact.postal_country || "",
      default_hourly_rate: contact.default_hourly_rate?.toString() || "",
      payment_term_days: contact.payment_term_days?.toString() || "",
      billing_email: contact.billing_email || "",
      iban: contact.iban || "",
      default_interest_type: contact.default_interest_type || "",
      default_contractual_rate: contact.default_contractual_rate?.toString() || "",
      default_rate_basis: contact.default_rate_basis || "",
      default_bik_mode: contact.default_bik_override_percentage != null
        ? "percentage"
        : contact.default_bik_override != null
          ? "amount"
          : "wik",
      default_bik_override: contact.default_bik_override?.toString() || "",
      default_bik_override_percentage: contact.default_bik_override_percentage?.toString() || "",
      default_minimum_fee: contact.default_minimum_fee?.toString() || "",
      default_bik_minimum_fee: contact.default_bik_minimum_fee?.toString() || "",
      default_provisie_percentage: contact.default_provisie_percentage?.toString() || "",
      is_btw_plichtig: contact.is_btw_plichtig ? "true" : "false",
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
        data.salutation = editForm.salutation || "unknown";
      }
      data.email = editForm.email?.trim() || null;
      data.phone = editForm.phone?.trim() || null;
      data.kvk_number = editForm.kvk_number?.trim() || null;
      data.btw_number = editForm.btw_number?.trim() || null;
      data.legal_form = editForm.legal_form?.trim() || null;
      data.visit_address = editForm.visit_address?.trim() || null;
      data.visit_postcode = editForm.visit_postcode?.trim() || null;
      data.visit_city = editForm.visit_city?.trim() || null;
      data.visit_country = editForm.visit_country?.trim() || null;
      data.postal_address = editForm.postal_address?.trim() || null;
      data.postal_postcode = editForm.postal_postcode?.trim() || null;
      data.postal_city = editForm.postal_city?.trim() || null;
      data.postal_country = editForm.postal_country?.trim() || null;
      data.default_hourly_rate = editForm.default_hourly_rate ? editForm.default_hourly_rate : null;
      data.payment_term_days = editForm.payment_term_days ? editForm.payment_term_days : null;
      data.billing_email = editForm.billing_email?.trim() || null;
      data.iban = editForm.iban?.trim() || null;
      data.default_interest_type = editForm.default_interest_type || null;
      data.default_contractual_rate =
        editForm.default_interest_type === "contractual" && editForm.default_contractual_rate
          ? editForm.default_contractual_rate
          : null;
      // DF120: rate_basis (yearly/monthly) — only meaningful for contractual interest
      data.default_rate_basis =
        editForm.default_interest_type === "contractual" && editForm.default_rate_basis
          ? editForm.default_rate_basis
          : null;
      // DF117-22: BIK defaults — only one mode wins (amount XOR percentage XOR wik=both null)
      data.default_bik_override =
        editForm.default_bik_mode === "amount" && editForm.default_bik_override
          ? editForm.default_bik_override
          : null;
      data.default_bik_override_percentage =
        editForm.default_bik_mode === "percentage" && editForm.default_bik_override_percentage
          ? editForm.default_bik_override_percentage
          : null;
      // DF120: minimum_fee — independent of BIK mode (still applies as floor)
      data.default_minimum_fee = editForm.default_minimum_fee || null;
      data.default_bik_minimum_fee = editForm.default_bik_minimum_fee || null;
      // S210: standaard succesprovisie-% dat nieuwe dossiers van deze cliënt erven
      data.default_provisie_percentage = editForm.default_provisie_percentage || null;
      // AUD124-01: BTW-plichtig flag
      (data as Record<string, unknown>).is_btw_plichtig = editForm.is_btw_plichtig === "true";
      data.notes = editForm.notes?.trim() || null;

      await updateRelation.mutateAsync({ id, data });
      toast.success("Relatie bijgewerkt");
      setEditing(false);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Kon niet opslaan");
    }
  };

  const handleDelete = async () => {
    if (!await confirm({ title: "Relatie verwijderen", description: "Weet je zeker dat je deze relatie wilt verwijderen?", variant: "destructive", confirmText: "Verwijderen" })) return;
    try {
      await deleteRelation.mutateAsync(id);
      toast.success("Relatie verwijderd");
      router.push("/relaties");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Kon de relatie niet verwijderen";
      toast.error(msg);
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
      const data: KycFormData = {
        contact_id: id,
        risk_level: kycForm.risk_level || null,
        risk_notes: kycForm.risk_notes?.trim() || null,
        id_type: kycForm.id_type || null,
        id_number: kycForm.id_number?.trim() || null,
        id_expiry_date: kycForm.id_expiry_date || null,
        id_verified_at: kycForm.id_verified_at || null,
        ubo_name: kycForm.ubo_name?.trim() || null,
        ubo_dob: kycForm.ubo_dob || null,
        ubo_nationality: kycForm.ubo_nationality?.trim() || null,
        ubo_percentage: kycForm.ubo_percentage?.trim() || null,
        ubo_verified_at: kycForm.ubo_verified_at || null,
        pep_checked: kycForm.pep_checked,
        pep_is_pep: kycForm.pep_is_pep,
        pep_notes: kycForm.pep_notes?.trim() || null,
        sanctions_checked: kycForm.sanctions_checked,
        sanctions_hit: kycForm.sanctions_hit,
        sanctions_notes: kycForm.sanctions_notes?.trim() || null,
        source_of_funds: kycForm.source_of_funds?.trim() || null,
        source_of_funds_verified: kycForm.source_of_funds_verified,
        notes: kycForm.notes?.trim() || null,
      };

      await saveKyc.mutateAsync(data);
      toast.success("WWFT-gegevens opgeslagen");
      setKycEditing(false);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Kon niet opslaan");
    }
  };

  const handleKycComplete = async () => {
    if (!kycData?.id) return;
    try {
      await completeKyc.mutateAsync({ id: kycData.id });
      toast.success("KYC verificatie afgerond");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Kon verificatie niet afronden");
    }
  };

  const updateKycField = (field: string, value: string | boolean) => {
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
          Terug naar overzicht
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
      {ConfirmDialogEl}
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
        <ContactInfoSection
          contact={contact}
          editing={editing}
          editForm={editForm}
          updateEdit={updateEdit}
          inputClass={inputClass}
        />

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

          <LinkedCasesSection
            contactId={id}
            contactName={contact.name}
            cases={contactCases}
          />

          {/* CONN-9: doorklik naar facturen van deze klant */}
          <Link
            href={`/facturen?contact_id=${id}&contact_name=${encodeURIComponent(contact.name)}`}
            className="flex items-center justify-between rounded-xl border border-border bg-card px-5 py-4 hover:bg-muted/40 transition-colors"
          >
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-semibold text-card-foreground">
                Facturen van deze klant
              </span>
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
          </Link>
        </div>
      </div>

      {/* WWFT / KYC Section */}
      {hasModule("wwft") && (
        <KycSection
          contactId={id}
          contactType={contact.contact_type}
          kycData={kycData}
          kycLoading={kycLoading}
          kycOpen={kycOpen}
          setKycOpen={setKycOpen}
          kycEditing={kycEditing}
          setKycEditing={setKycEditing}
          kycForm={kycForm}
          updateKycField={updateKycField}
          startKycEditing={startKycEditing}
          handleKycSave={handleKycSave}
          handleKycComplete={handleKycComplete}
          saveKycIsPending={saveKyc.isPending}
          completeKycIsPending={completeKyc.isPending}
          inputClass={inputClass}
        />
      )}

      {/* AI-UX-11: Algemene Voorwaarden */}
      <TermsSection contactId={id} termsFileName={contact.terms_file_name} />
    </div>
  );
}

// ── Algemene Voorwaarden Section ─────────────────────────────────────────────

function TermsSection({ contactId, termsFileName: _legacyFileName }: { contactId: string; termsFileName?: string | null }) {
  const { data: versions = [], isLoading } = useContactTerms(contactId);
  const uploadMutation = useUploadContactTerms(contactId);
  const updateMutation = useUpdateContactTerms(contactId);
  const deleteMutation = useDeleteContactTerms(contactId);
  const { confirm, ConfirmDialog: ConfirmDialogEl } = useConfirm();

  const [showUploadForm, setShowUploadForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const handleDownload = async (termsId: string, fileName: string) => {
    try {
      await downloadContactTermsFile(contactId, termsId, fileName);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Download mislukt");
    }
  };

  const handleDelete = async (termsId: string, label: string | null) => {
    const ok = await confirm({
      title: `AV-versie "${label || "(geen label)"}" verwijderen?`,
      description:
        "Dossiers die naar deze versie verwezen krijgen 'geen versie gekoppeld' (terugval op smart-default).",
      confirmText: "Verwijderen",
      variant: "destructive",
    });
    if (!ok) return;
    try {
      await deleteMutation.mutateAsync(termsId);
      toast.success("AV-versie verwijderd");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Verwijderen mislukt");
    }
  };

  const formatPeriod = (vf: string | null, vt: string | null) => {
    if (!vf && !vt) return "Altijd geldig";
    const fmt = (d: string | null) =>
      d ? new Date(d).toLocaleDateString("nl-NL", { day: "2-digit", month: "short", year: "numeric" }) : null;
    const from = fmt(vf);
    const to = fmt(vt);
    if (from && to) return `${from} t/m ${to}`;
    if (from) return `Vanaf ${from}`;
    return `T/m ${to}`;
  };

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      {ConfirmDialogEl}
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-card-foreground">
          Algemene Voorwaarden
        </h3>
        {!showUploadForm && (
          <button
            type="button"
            onClick={() => setShowUploadForm(true)}
            className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
          >
            <Plus className="h-3 w-3" />
            Nieuwe versie
          </button>
        )}
      </div>

      {showUploadForm && (
        <TermsUploadForm
          onCancel={() => setShowUploadForm(false)}
          onSubmit={async (data) => {
            try {
              await uploadMutation.mutateAsync(data);
              toast.success("AV-versie geüpload");
              setShowUploadForm(false);
            } catch (err: unknown) {
              toast.error(err instanceof Error ? err.message : "Upload mislukt");
            }
          }}
          uploading={uploadMutation.isPending}
        />
      )}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Versies laden...</p>
      ) : versions.length === 0 ? (
        !showUploadForm && (
          <p className="text-sm text-muted-foreground">
            Nog geen algemene voorwaarden geüpload. Klik &lsquo;Nieuwe versie&rsquo; om te beginnen.
          </p>
        )
      ) : (
        <div className="space-y-2">
          {versions.map((v) => (
            <div key={v.id}>
              {editingId === v.id ? (
                <TermsEditForm
                  version={v}
                  onCancel={() => setEditingId(null)}
                  onSubmit={async (data) => {
                    try {
                      await updateMutation.mutateAsync({ termsId: v.id, data });
                      toast.success("AV-versie bijgewerkt");
                      setEditingId(null);
                    } catch (err: unknown) {
                      toast.error(err instanceof Error ? err.message : "Bijwerken mislukt");
                    }
                  }}
                  saving={updateMutation.isPending}
                />
              ) : (
                <div className="flex items-center justify-between gap-3 rounded-lg border border-border bg-muted/30 px-3 py-2.5">
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <File className="h-4 w-4 text-muted-foreground shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">
                        {v.label || "(geen label)"}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">
                        {formatPeriod(v.valid_from, v.valid_to)} · {v.file_name}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      type="button"
                      onClick={() => handleDownload(v.id, v.file_name)}
                      className="rounded-md p-1.5 hover:bg-muted transition-colors"
                      title="Downloaden"
                    >
                      <Download className="h-3.5 w-3.5 text-muted-foreground" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingId(v.id)}
                      className="rounded-md p-1.5 hover:bg-muted transition-colors"
                      title="Bewerken"
                    >
                      <Edit2 className="h-3.5 w-3.5 text-muted-foreground" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(v.id, v.label)}
                      className="rounded-md p-1.5 hover:bg-destructive/10 transition-colors"
                      title="Verwijderen"
                    >
                      <Trash2 className="h-3.5 w-3.5 text-destructive" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function TermsUploadForm({
  onCancel,
  onSubmit,
  uploading,
}: {
  onCancel: () => void;
  onSubmit: (data: ContactTermsCreate) => Promise<void>;
  uploading: boolean;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [label, setLabel] = useState("");
  const [validFrom, setValidFrom] = useState("");
  const [validTo, setValidTo] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      toast.error("Selecteer een bestand");
      return;
    }
    await onSubmit({
      file,
      label: label || undefined,
      valid_from: validFrom || undefined,
      valid_to: validTo || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="mb-3 space-y-3 rounded-lg border border-border bg-muted/20 p-3">
      <div>
        <label className="block text-xs font-medium text-muted-foreground mb-1">
          Bestand (PDF, DOCX)
        </label>
        <input
          type="file"
          accept=".pdf,.docx,.doc"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="block w-full text-xs text-foreground file:mr-2 file:rounded-md file:border-0 file:bg-background file:px-2 file:py-1 file:text-xs file:font-medium hover:file:bg-muted"
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-muted-foreground mb-1">
          Label
        </label>
        <input
          type="text"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder="Bijv. AV 2025-01 of v3.2"
          className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
        />
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1">
            Geldig vanaf
          </label>
          <input
            type="date"
            value={validFrom}
            onChange={(e) => setValidFrom(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1">
            Geldig t/m
          </label>
          <input
            type="date"
            value={validTo}
            onChange={(e) => setValidTo(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
      </div>
      <p className="text-[11px] text-muted-foreground">
        Laat data leeg voor &laquo;altijd geldig&raquo;. AI gebruikt automatisch de versie die geldig is
        op de factuur-datum van het dossier.
      </p>
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={uploading || !file}
          className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {uploading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Upload className="h-3 w-3" />}
          Uploaden
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={uploading}
          className="rounded-md border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
        >
          Annuleren
        </button>
      </div>
    </form>
  );
}

function TermsEditForm({
  version,
  onCancel,
  onSubmit,
  saving,
}: {
  version: ContactTerms;
  onCancel: () => void;
  onSubmit: (data: ContactTermsUpdate) => Promise<void>;
  saving: boolean;
}) {
  const [label, setLabel] = useState(version.label ?? "");
  const [validFrom, setValidFrom] = useState(version.valid_from ?? "");
  const [validTo, setValidTo] = useState(version.valid_to ?? "");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit({
      label: label || null,
      valid_from: validFrom || null,
      valid_to: validTo || null,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-2 rounded-lg border border-primary/30 bg-primary/5 p-3">
      <div>
        <label className="block text-xs font-medium text-muted-foreground mb-1">Label</label>
        <input
          type="text"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
        />
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1">Geldig vanaf</label>
          <input
            type="date"
            value={validFrom}
            onChange={(e) => setValidFrom(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-muted-foreground mb-1">Geldig t/m</label>
          <input
            type="date"
            value={validTo}
            onChange={(e) => setValidTo(e.target.value)}
            className="w-full rounded-md border border-input bg-background px-2 py-1 text-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
          />
        </div>
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={saving}
          className="rounded-md bg-primary px-3 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {saving ? "Opslaan..." : "Opslaan"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={saving}
          className="rounded-md border border-border px-3 py-1 text-xs font-medium text-muted-foreground hover:bg-muted transition-colors"
        >
          Annuleren
        </button>
      </div>
    </form>
  );
}
