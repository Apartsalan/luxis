"use client";

import { useState, useEffect, useCallback } from "react";
import { useConfirm } from "@/components/confirm-dialog";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Building2,
  Download,
  File,
  Loader2,
  User,
  Trash2,
  Pencil,
  Upload,
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
      default_interest_type: contact.default_interest_type || "",
      default_contractual_rate: contact.default_contractual_rate?.toString() || "",
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
      data.default_interest_type = editForm.default_interest_type || null;
      data.default_contractual_rate =
        editForm.default_interest_type === "contractual" && editForm.default_contractual_rate
          ? editForm.default_contractual_rate
          : null;
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

function TermsSection({ contactId, termsFileName }: { contactId: string; termsFileName?: string | null }) {
  const [uploading, setUploading] = useState(false);
  const [currentFile, setCurrentFile] = useState(termsFileName);
  const { data: contact, refetch } = useRelation(contactId);

  // Sync with contact data
  useEffect(() => {
    if (contact) setCurrentFile(contact.terms_file_name);
  }, [contact?.terms_file_name]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const token = tokenStore.getAccess();
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`/api/relations/${contactId}/terms`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => null);
        throw new Error(err?.detail || "Upload mislukt");
      }
      const data = await res.json();
      setCurrentFile(data.terms_file_name);
      refetch();
      toast.success("Algemene voorwaarden geüpload");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Upload mislukt");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleDownload = async () => {
    try {
      const token = tokenStore.getAccess();
      const res = await fetch(`/api/relations/${contactId}/terms`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Download mislukt");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = currentFile || "voorwaarden.pdf";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Download mislukt");
    }
  };

  const handleDelete = async () => {
    try {
      const token = tokenStore.getAccess();
      const res = await fetch(`/api/relations/${contactId}/terms`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Verwijderen mislukt");
      setCurrentFile(null);
      refetch();
      toast.success("Algemene voorwaarden verwijderd");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Verwijderen mislukt");
    }
  };

  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h3 className="text-sm font-semibold text-card-foreground mb-3">
        Algemene Voorwaarden
      </h3>

      {currentFile ? (
        <div className="flex items-center justify-between gap-3 rounded-lg border border-border bg-muted/30 px-3 py-2.5">
          <div className="flex items-center gap-2 min-w-0">
            <File className="h-4 w-4 text-muted-foreground shrink-0" />
            <span className="text-sm text-foreground truncate">{currentFile}</span>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <button
              type="button"
              onClick={handleDownload}
              className="rounded-md p-1.5 hover:bg-muted transition-colors"
              title="Downloaden"
            >
              <Download className="h-3.5 w-3.5 text-muted-foreground" />
            </button>
            <label className="rounded-md p-1.5 hover:bg-muted transition-colors cursor-pointer" title="Vervangen">
              <Upload className="h-3.5 w-3.5 text-muted-foreground" />
              <input type="file" accept=".pdf,.docx,.doc" onChange={handleUpload} className="hidden" />
            </label>
            <button
              type="button"
              onClick={handleDelete}
              className="rounded-md p-1.5 hover:bg-destructive/10 transition-colors"
              title="Verwijderen"
            >
              <Trash2 className="h-3.5 w-3.5 text-destructive" />
            </button>
          </div>
        </div>
      ) : (
        <label className="flex items-center justify-center gap-2 rounded-lg border border-dashed border-border bg-muted/20 px-4 py-6 cursor-pointer hover:bg-muted/40 transition-colors">
          {uploading ? (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          ) : (
            <Upload className="h-4 w-4 text-muted-foreground" />
          )}
          <span className="text-sm text-muted-foreground">
            {uploading ? "Uploaden..." : "Upload algemene voorwaarden (PDF, DOCX)"}
          </span>
          <input type="file" accept=".pdf,.docx,.doc" onChange={handleUpload} className="hidden" disabled={uploading} />
        </label>
      )}
    </div>
  );
}
