"use client";

import { Fragment, Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Search,
  Plus,
  X,
  Check,
  ChevronRight,
  ChevronLeft,
  ChevronDown,
  ChevronUp,
  FileText,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { useCreateCase, useConflictCheck, useAddCaseParty } from "@/hooks/use-cases";
import type { CaseCreateInput } from "@/hooks/use-cases";
import { useRelations, useRelation, useCreateRelation, useCreateContactLink } from "@/hooks/use-relations";
import { useCreateClaim } from "@/hooks/use-collections";
import { useModules } from "@/hooks/use-modules";
import { AlertTriangle, ShieldAlert } from "lucide-react";
import { useKycStatus } from "@/hooks/use-kyc";
import { InvoiceUploadZone } from "@/components/InvoiceUploadZone";
import type { InvoiceParseResult } from "@/hooks/use-invoice-parser";
import { tokenStore } from "@/lib/token-store";
import { ConfidenceDot } from "@/components/cases/wizard/ConfidenceDot";

// ── Types ────────────────────────────────────────────────────────────────────

interface ClaimForm {
  description: string;
  principal_amount: string;
  default_date: string;
  invoice_number: string;
  invoice_date: string;
  rate_basis: string;
}

const EMPTY_CLAIM: ClaimForm = {
  description: "",
  principal_amount: "",
  default_date: "",
  invoice_number: "",
  invoice_date: "",
  rate_basis: "yearly",
};

interface InlineContact {
  contact_type: "company" | "person";
  name: string;
  email: string;
  phone: string;
  kvk_number: string;
  btw_number: string;
  visit_address: string;
  visit_postcode: string;
  visit_city: string;
  postal_address: string;
  postal_postcode: string;
  postal_city: string;
}

const EMPTY_INLINE_CONTACT: InlineContact = {
  contact_type: "company",
  name: "",
  email: "",
  phone: "",
  kvk_number: "",
  btw_number: "",
  visit_address: "",
  visit_postcode: "",
  visit_city: "",
  postal_address: "",
  postal_postcode: "",
  postal_city: "",
};

// ── Stepper Component ────────────────────────────────────────────────────────

function WizardStepper({
  currentStep,
  steps,
  onStepClick,
}: {
  currentStep: number;
  steps: { label: string; optional?: boolean }[];
  onStepClick: (step: number) => void;
}) {
  return (
    <div className="flex items-center">
      {steps.map((step, index) => {
        const stepNum = index + 1;
        const isActive = stepNum === currentStep;
        const isCompleted = stepNum < currentStep;
        const isClickable = stepNum < currentStep;

        return (
          <Fragment key={index}>
            <button
              type="button"
              onClick={() => isClickable && onStepClick(stepNum)}
              className={`flex items-center gap-2 transition-colors ${
                isClickable ? "cursor-pointer" : isActive ? "cursor-default" : "cursor-default"
              }`}
            >
              <span
                className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-all ${
                  isActive
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : isCompleted
                    ? "bg-primary/10 text-primary"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {isCompleted ? <Check className="h-4 w-4" /> : stepNum}
              </span>
              <span
                className={`hidden sm:inline text-sm font-medium ${
                  isActive
                    ? "text-foreground"
                    : isCompleted
                    ? "text-primary"
                    : "text-muted-foreground"
                }`}
              >
                {step.label}
                {step.optional && (
                  <span className="text-[11px] text-muted-foreground font-normal">
                    {" "}(optioneel)
                  </span>
                )}
              </span>
            </button>
            {index < steps.length - 1 && (
              <div
                className={`mx-3 h-px flex-1 transition-colors ${
                  stepNum < currentStep ? "bg-primary" : "bg-border"
                }`}
              />
            )}
          </Fragment>
        );
      })}
    </div>
  );
}

// ── Inline Contact Details (expandable extra fields) ────────────────────────

const inputCls = "rounded-md border border-input bg-background px-2 py-1.5 text-sm";

function InlineContactDetails({
  data,
  onChange,
  expanded,
  onToggle,
}: {
  data: InlineContact;
  onChange: (updates: Partial<InlineContact>) => void;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div>
      <button
        type="button"
        onClick={onToggle}
        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        {expanded ? "Minder details" : "Meer details (adres, telefoon, KvK)"}
      </button>
      {expanded && (
        <div className="mt-2 space-y-2">
          {/* Phone */}
          <input
            type="tel"
            placeholder="Telefoon"
            value={data.phone}
            onChange={(e) => onChange({ phone: e.target.value })}
            className={inputCls}
          />
          {/* KvK + BTW (only for companies) */}
          {data.contact_type === "company" && (
            <div className="grid gap-2 sm:grid-cols-2">
              <input
                type="text"
                placeholder="KvK-nummer"
                value={data.kvk_number}
                onChange={(e) => onChange({ kvk_number: e.target.value })}
                className={inputCls}
              />
              <input
                type="text"
                placeholder="BTW-nummer"
                value={data.btw_number}
                onChange={(e) => onChange({ btw_number: e.target.value })}
                className={inputCls}
              />
            </div>
          )}
          {/* Visit address */}
          <div>
            <p className="text-xs text-muted-foreground mb-1">Bezoekadres</p>
            <div className="grid gap-2 sm:grid-cols-3">
              <input
                type="text"
                placeholder="Straat + huisnr"
                value={data.visit_address}
                onChange={(e) => onChange({ visit_address: e.target.value })}
                className={`${inputCls} sm:col-span-1`}
              />
              <input
                type="text"
                placeholder="Postcode"
                value={data.visit_postcode}
                onChange={(e) => onChange({ visit_postcode: e.target.value })}
                className={inputCls}
              />
              <input
                type="text"
                placeholder="Plaats"
                value={data.visit_city}
                onChange={(e) => onChange({ visit_city: e.target.value })}
                className={inputCls}
              />
            </div>
          </div>
          {/* Postal address */}
          <div>
            <p className="text-xs text-muted-foreground mb-1">Postadres (optioneel)</p>
            <div className="grid gap-2 sm:grid-cols-3">
              <input
                type="text"
                placeholder="Straat + huisnr"
                value={data.postal_address}
                onChange={(e) => onChange({ postal_address: e.target.value })}
                className={`${inputCls} sm:col-span-1`}
              />
              <input
                type="text"
                placeholder="Postcode"
                value={data.postal_postcode}
                onChange={(e) => onChange({ postal_postcode: e.target.value })}
                className={inputCls}
              />
              <input
                type="text"
                placeholder="Plaats"
                value={data.postal_city}
                onChange={(e) => onChange({ postal_city: e.target.value })}
                className={inputCls}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Page Wrapper ─────────────────────────────────────────────────────────────

export default function NieuweZaakPageWrapper() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-2xl py-12 text-center text-muted-foreground">
          Laden...
        </div>
      }
    >
      <NieuweZaakPage />
    </Suspense>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────

function NieuweZaakPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const createCase = useCreateCase();
  const createClaim = useCreateClaim();
  const { hasModule } = useModules();

  const prefillClientId = searchParams.get("client_id") || "";
  const prefillClientName = searchParams.get("client_name") || "";
  const prefillOpponentId = searchParams.get("opposing_party_id") || "";
  const prefillOpponentName = searchParams.get("opposing_party_name") || "";

  // ── Invoice AI parse state ──────────────────────────────────────────────
  const [invoiceData, setInvoiceData] = useState<InvoiceParseResult | null>(null);
  const [fieldConfidence, setFieldConfidence] = useState<Record<string, number>>({});
  const [invoiceFile, setInvoiceFile] = useState<File | null>(null);

  // ── Step state ───────────────────────────────────────────────────────────
  const [currentStep, setCurrentStep] = useState(1);

  // ── Case form state ──────────────────────────────────────────────────────
  const [form, setForm] = useState({
    case_type: "incasso",
    debtor_type: "",
    description: "",
    reference: "",
    court_case_number: "",
    interest_type: "statutory",
    contractual_rate: "",
    rate_basis: "yearly",
    budget: "",
    client_id: prefillClientId,
    opposing_party_id: prefillOpponentId,
    date_opened: new Date().toISOString().split("T")[0],
    // LF-19/22 fields
    hourly_rate: "",
    payment_term_days: "",
    collection_strategy: "",
    debtor_notes: "",
  });

  // ── Claims state (Step 3) ───────────────────────────────────────────────
  const [claims, setClaims] = useState<ClaimForm[]>([{ ...EMPTY_CLAIM }]);

  // ── Contact search / inline creation state ───────────────────────────────
  const [clientSearch, setClientSearch] = useState(prefillClientName);
  const [opponentSearch, setOpponentSearch] = useState(prefillOpponentName);
  const [lawyerSearch, setLawyerSearch] = useState("");
  const [selectedLawyer, setSelectedLawyer] = useState<{
    id: string;
    name: string;
  } | null>(null);
  const [error, setError] = useState("");
  const [wizardFieldErrors, setWizardFieldErrors] = useState<Record<string, string>>({});

  const validateWizardField = (field: string, value: string): string => {
    if (field === "date_opened" && !value) return "Datum geopend is verplicht";
    if (field === "contractual_rate" && form.interest_type === "contractual" && !value) return "Rentepercentage is verplicht";
    if (field === "client_id" && !value) return "Selecteer een client";
    return "";
  };

  const handleWizardBlur = (field: string) => {
    const value = form[field as keyof typeof form] || "";
    const err = validateWizardField(field, value);
    setWizardFieldErrors((prev) => ({ ...prev, [field]: err }));
  };

  const createRelation = useCreateRelation();
  const createContactLink = useCreateContactLink();
  const addParty = useAddCaseParty();
  const [opponentContactType, setOpponentContactType] = useState("");

  const [showNewClient, setShowNewClient] = useState(false);
  const [newClient, setNewClient] = useState<InlineContact>({ ...EMPTY_INLINE_CONTACT });
  const [showClientDetails, setShowClientDetails] = useState(true);
  const [showNewOpponent, setShowNewOpponent] = useState(false);
  const [newOpponent, setNewOpponent] = useState<InlineContact>({ ...EMPTY_INLINE_CONTACT });
  const [showOpponentDetails, setShowOpponentDetails] = useState(true);
  const [showNewLawyer, setShowNewLawyer] = useState(false);
  const [newLawyer, setNewLawyer] = useState<InlineContact>({ ...EMPTY_INLINE_CONTACT, contact_type: "person" });
  const [showLawyerDetails, setShowLawyerDetails] = useState(true);

  // ── Inline contact creation handler ──────────────────────────────────────
  const handleCreateInlineContact = async (
    role: "client" | "opponent" | "lawyer",
    data: InlineContact
  ) => {
    try {
      const payload: Record<string, unknown> = {
        contact_type: data.contact_type,
        name: data.name,
      };
      // Only include non-empty optional fields
      if (data.email) payload.email = data.email;
      if (data.phone) payload.phone = data.phone;
      if (data.kvk_number) payload.kvk_number = data.kvk_number;
      if (data.btw_number) payload.btw_number = data.btw_number;
      if (data.visit_address) payload.visit_address = data.visit_address;
      if (data.visit_postcode) payload.visit_postcode = data.visit_postcode;
      if (data.visit_city) payload.visit_city = data.visit_city;
      if (data.postal_address) payload.postal_address = data.postal_address;
      if (data.postal_postcode) payload.postal_postcode = data.postal_postcode;
      if (data.postal_city) payload.postal_city = data.postal_city;

      const result = await createRelation.mutateAsync(payload as any);
      if (role === "client") {
        updateField("client_id", result.id);
        setClientSearch(result.name);
        setShowNewClient(false);
        setNewClient({ ...EMPTY_INLINE_CONTACT });
        setShowClientDetails(false);
      } else if (role === "opponent") {
        updateField("opposing_party_id", result.id);
        setOpponentSearch(result.name);
        setOpponentContactType(data.contact_type);
        setShowNewOpponent(false);
        setNewOpponent({ ...EMPTY_INLINE_CONTACT });
        setShowOpponentDetails(false);
        if (!form.debtor_type) {
          updateField(
            "debtor_type",
            data.contact_type === "company" ? "b2b" : "b2c"
          );
        }
      } else if (role === "lawyer") {
        setSelectedLawyer({ id: result.id, name: result.name });
        setLawyerSearch(result.name);
        setShowNewLawyer(false);
        setNewLawyer({ ...EMPTY_INLINE_CONTACT, contact_type: "person" });
        setShowLawyerDetails(false);
      }
      toast.success(`${data.name} aangemaakt`);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Kon relatie niet aanmaken");
    }
  };

  // ── Data queries ─────────────────────────────────────────────────────────
  const { data: clientResults } = useRelations({
    search: clientSearch || undefined,
    per_page: 5,
  });
  const { data: opponentResults } = useRelations({
    search: opponentSearch || undefined,
    per_page: 5,
  });
  const { data: lawyerResults } = useRelations({
    search: lawyerSearch || undefined,
    per_page: 5,
  });

  const { data: clientConflict } = useConflictCheck(
    form.client_id || undefined,
    "client"
  );
  const { data: opponentConflict } = useConflictCheck(
    form.opposing_party_id || undefined,
    "opposing_party"
  );
  const { data: clientKycStatus } = useKycStatus(
    hasModule("wwft") ? form.client_id || undefined : undefined
  );

  // ── Pre-fill interest defaults from client (DF-09) ───────────────────────
  const { data: selectedClient } = useRelation(form.client_id || undefined);
  useEffect(() => {
    if (selectedClient?.default_interest_type && form.interest_type === "statutory") {
      setForm((prev) => ({
        ...prev,
        interest_type: selectedClient.default_interest_type!,
        ...(selectedClient.default_interest_type === "contractual" && selectedClient.default_contractual_rate
          ? { contractual_rate: String(selectedClient.default_contractual_rate) }
          : {}),
      }));
    }
  }, [selectedClient?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Helpers ──────────────────────────────────────────────────────────────
  const updateField = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    // Clear validation error when a required field is filled
    if (field === "client_id" && value) setError("");
    // Clear inline field error when user types
    if (wizardFieldErrors[field]) {
      setWizardFieldErrors((prev) => ({ ...prev, [field]: "" }));
    }
  };

  // ── Auto-select contacts when AI parsing pre-fills search fields ─────────
  const [aiParsedClient, setAiParsedClient] = useState(false);
  const [aiParsedOpponent, setAiParsedOpponent] = useState(false);

  // Auto-select client from search results when AI-parsed
  useEffect(() => {
    if (aiParsedClient && clientSearch && !form.client_id && clientResults?.items) {
      if (clientResults.items.length > 0) {
        // Match found — auto-select
        const match = clientResults.items[0];
        updateField("client_id", match.id);
        setClientSearch(match.name);
        setAiParsedClient(false);
      } else {
        // No match — auto-open inline form (already pre-filled by handleInvoiceParsed)
        setShowNewClient(true);
        setAiParsedClient(false);
      }
    }
  }, [aiParsedClient, clientSearch, clientResults, form.client_id]);

  // Auto-select opponent from search results when AI-parsed
  useEffect(() => {
    if (aiParsedOpponent && opponentSearch && !form.opposing_party_id && opponentResults?.items) {
      if (opponentResults.items.length > 0) {
        // Match found — auto-select
        const match = opponentResults.items[0];
        updateField("opposing_party_id", match.id);
        setOpponentSearch(match.name);
        setOpponentContactType(match.contact_type);
        if (!form.debtor_type) {
          updateField("debtor_type", match.contact_type === "company" ? "b2b" : "b2c");
        }
        setAiParsedOpponent(false);
      } else {
        // No match — auto-open inline form (already pre-filled by handleInvoiceParsed)
        setShowNewOpponent(true);
        setAiParsedOpponent(false);
      }
    }
  }, [aiParsedOpponent, opponentSearch, opponentResults, form.opposing_party_id, form.debtor_type]);

  // ── Invoice parse handler ────────────────────────────────────────────────
  const handleInvoiceParsed = useCallback(
    (data: InvoiceParseResult, file: File) => {
      setInvoiceData(data);
      setFieldConfidence(data.confidence || {});
      setInvoiceFile(file);

      // Step 1: Zaakgegevens
      if (data.description) updateField("description", data.description);
      if (data.debtor_type) {
        updateField("debtor_type", data.debtor_type === "company" ? "b2b" : "b2c");
      }

      // Step 2: Partijen — pre-fill search fields and trigger auto-match
      if (data.debtor_name) {
        setOpponentSearch(data.debtor_name);
        setAiParsedOpponent(true);
        // Pre-fill inline opponent form with all extracted NAW data
        setNewOpponent({
          contact_type: data.debtor_type || "company",
          name: data.debtor_name || "",
          email: data.debtor_email || "",
          phone: "",
          kvk_number: data.debtor_kvk || "",
          btw_number: "",
          visit_address: data.debtor_address || "",
          visit_postcode: data.debtor_postcode || "",
          visit_city: data.debtor_city || "",
          postal_address: data.debtor_postal_address || "",
          postal_postcode: data.debtor_postal_postcode || "",
          postal_city: data.debtor_postal_city || "",
        });
        if (data.debtor_address || data.debtor_postcode || data.debtor_postal_address) {
          setShowOpponentDetails(true);
        }
      }
      if (data.creditor_name) {
        setClientSearch(data.creditor_name);
        setAiParsedClient(true);
        // Pre-fill inline client form with all extracted NAW data
        setNewClient({
          contact_type: data.creditor_type || "company",
          name: data.creditor_name || "",
          email: data.creditor_email || "",
          phone: "",
          kvk_number: data.creditor_kvk || "",
          btw_number: data.creditor_btw || "",
          visit_address: data.creditor_address || "",
          visit_postcode: data.creditor_postcode || "",
          visit_city: data.creditor_city || "",
          postal_address: data.creditor_postal_address || "",
          postal_postcode: data.creditor_postal_postcode || "",
          postal_city: data.creditor_postal_city || "",
        });
        if (data.creditor_address || data.creditor_postcode || data.creditor_postal_address) {
          setShowClientDetails(true);
        }
      }

      // Step 3: Vordering — pre-fill first claim
      const claimUpdates: Partial<ClaimForm> = {};
      if (data.principal_amount != null) {
        claimUpdates.principal_amount = String(data.principal_amount);
      }
      if (data.invoice_number) claimUpdates.invoice_number = data.invoice_number;
      if (data.invoice_date) claimUpdates.invoice_date = data.invoice_date;
      if (data.due_date) claimUpdates.default_date = data.due_date;
      if (data.description) claimUpdates.description = data.description;

      if (Object.keys(claimUpdates).length > 0) {
        setClaims((prev) => {
          const updated = [...prev];
          updated[0] = { ...updated[0], ...claimUpdates };
          return updated;
        });
      }

      toast.success("Factuurgegevens ingevuld");
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  // UX-16: Warn on unsaved changes
  const wizardDirty = form.client_id || form.description || form.reference || claims.some(c => c.description || c.principal_amount);
  useEffect(() => {
    if (!wizardDirty) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [wizardDirty]);

  const isIncasso = form.case_type === "incasso";
  const totalSteps = isIncasso ? 3 : 2;

  const steps = isIncasso
    ? [
        { label: "Zaakgegevens" },
        { label: "Partijen" },
        { label: "Vordering", optional: true },
      ]
    : [{ label: "Zaakgegevens" }, { label: "Partijen" }];

  const updateClaim = (index: number, field: keyof ClaimForm, value: string) => {
    setClaims((prev) =>
      prev.map((c, i) => (i === index ? { ...c, [field]: value } : c))
    );
  };

  const addClaim = () => {
    setClaims((prev) => [...prev, { ...EMPTY_CLAIM }]);
  };

  const removeClaim = (index: number) => {
    setClaims((prev) => prev.filter((_, i) => i !== index));
  };

  // ── Step validation ──────────────────────────────────────────────────────
  const validateStep = (step: number): string | null => {
    if (step === 1) {
      if (!form.date_opened) return "Datum geopend is verplicht";
    }
    if (step === 2) {
      if (!form.client_id) return "Selecteer een client";
    }
    // Step 3 claims are optional — but if filled, validate required fields
    if (step === 3) {
      if (
        form.interest_type === "contractual" &&
        isIncasso &&
        !form.contractual_rate
      )
        return "Contractueel rentepercentage is verplicht";
      for (let i = 0; i < claims.length; i++) {
        const c = claims[i];
        if (c.description || c.principal_amount || c.default_date) {
          if (!c.description)
            return `Vordering ${i + 1}: omschrijving is verplicht`;
          if (!c.principal_amount)
            return `Vordering ${i + 1}: hoofdsom is verplicht`;
          if (!c.default_date)
            return `Vordering ${i + 1}: verzuimdatum is verplicht`;
        }
      }
    }
    return null;
  };

  const handleNext = () => {
    const validationError = validateStep(currentStep);
    if (validationError) {
      setError(validationError);
      // Set inline field errors for the current step
      if (currentStep === 1) {
        const errs: Record<string, string> = {};
        if (!form.date_opened) errs.date_opened = "Datum geopend is verplicht";
        if (form.interest_type === "contractual" && isIncasso && !form.contractual_rate) errs.contractual_rate = "Rentepercentage is verplicht";
        setWizardFieldErrors((prev) => ({ ...prev, ...errs }));
      }
      if (currentStep === 2) {
        if (!form.client_id) setWizardFieldErrors((prev) => ({ ...prev, client_id: "Selecteer een client" }));
      }
      return;
    }
    setError("");
    setCurrentStep((prev) => Math.min(prev + 1, totalSteps));
  };

  const handlePrev = () => {
    setError("");
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  // ── Submit ───────────────────────────────────────────────────────────────
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // If not on the last step, advance instead of submitting
    // (prevents Enter key in inputs from skipping steps)
    if (currentStep !== totalSteps) {
      handleNext();
      return;
    }
    setError("");

    // Validate all steps
    for (let s = 1; s <= totalSteps; s++) {
      const validationError = validateStep(s);
      if (validationError) {
        setCurrentStep(s);
        setError(validationError);
        return;
      }
    }

    setIsSubmitting(true);

    try {
      // 1. Build case data
      const data: CaseCreateInput = {
        case_type: form.case_type,
        interest_type: form.interest_type,
        client_id: form.client_id,
        date_opened: form.date_opened,
      };

      if (form.debtor_type) data.debtor_type = form.debtor_type;
      if (form.description) data.description = form.description;
      if (form.reference) data.reference = form.reference;
      if (form.court_case_number)
        data.court_case_number = form.court_case_number;
      if (form.opposing_party_id)
        data.opposing_party_id = form.opposing_party_id;
      if (form.interest_type === "contractual" && form.contractual_rate) {
        data.contractual_rate = form.contractual_rate;
      }
      if (form.budget) data.budget = form.budget;
      if (form.hourly_rate) data.hourly_rate = form.hourly_rate;
      if (form.payment_term_days)
        data.payment_term_days = parseInt(form.payment_term_days, 10);
      if (form.collection_strategy)
        data.collection_strategy = form.collection_strategy;
      if (form.debtor_notes) data.debtor_notes = form.debtor_notes;

      // 2. Create the case
      const result = await createCase.mutateAsync(data);

      // 3. Add advocaat wederpartij as party if selected
      if (selectedLawyer) {
        try {
          await addParty.mutateAsync({
            caseId: result.id,
            data: {
              contact_id: selectedLawyer.id,
              role: "advocaat_wederpartij",
            },
          });
        } catch {
          toast.error(
            "Dossier aangemaakt, maar advocaat wederpartij kon niet worden toegevoegd"
          );
        }
        if (form.opposing_party_id && opponentContactType === "company") {
          try {
            await createContactLink.mutateAsync({
              person_id: selectedLawyer.id,
              company_id: form.opposing_party_id,
              role_at_company: "Advocaat",
            });
          } catch {
            // Non-blocking: link may already exist
          }
        }
      }

      // 4. Create claims (if any are filled in)
      if (isIncasso) {
        const filledClaims = claims.filter(
          (c) => c.description && c.principal_amount && c.default_date
        );
        for (const claim of filledClaims) {
          try {
            await createClaim.mutateAsync({
              caseId: result.id,
              data: {
                description: claim.description,
                principal_amount: claim.principal_amount,
                default_date: claim.default_date,
                ...(claim.invoice_number && {
                  invoice_number: claim.invoice_number,
                }),
                ...(claim.invoice_date && {
                  invoice_date: claim.invoice_date,
                }),
                rate_basis: form.interest_type === "contractual" ? form.rate_basis : "yearly",
              },
            });
          } catch {
            toast.error(
              `Vordering "${claim.description}" kon niet worden aangemaakt`
            );
          }
        }
      }

      // 5. Upload invoice PDF to case documents (if uploaded via AI parse)
      if (invoiceFile) {
        try {
          const formData = new FormData();
          formData.append("file", invoiceFile);
          formData.append("description", `Factuur: ${invoiceFile.name}`);
          const token = tokenStore.getAccess();
          await fetch(`/api/cases/${result.id}/files`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            body: formData,
          });
        } catch {
          // Non-blocking: case is created, file upload is optional
          toast.error("Factuurbestand kon niet worden gekoppeld aan het dossier");
        }
      }

      toast.success("Dossier aangemaakt");
      router.push(`/zaken/${result.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Er ging iets mis");
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── Styling ──────────────────────────────────────────────────────────────
  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";
  const inputErrorClass = inputClass.replace("border-input", "border-destructive").replace("focus:border-primary", "focus:border-destructive").replace("focus:ring-primary/20", "focus:ring-destructive/20");
  const getWizardInputClass = (field: string) => wizardFieldErrors[field] ? inputErrorClass : inputClass;

  const isLastStep = currentStep === totalSteps;

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="mx-auto max-w-2xl space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link
          href="/zaken"
          className="rounded-lg p-2 hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-muted-foreground" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Nieuw dossier</h1>
          <p className="text-sm text-muted-foreground">
            Maak een nieuw dossier aan
          </p>
        </div>
      </div>

      {/* AI Invoice Upload */}
      {isIncasso && (
        <InvoiceUploadZone onParsed={handleInvoiceParsed} />
      )}

      {/* Stepper */}
      <div className="rounded-xl border border-border bg-card px-6 py-4">
        <WizardStepper
          currentStep={currentStep}
          steps={steps}
          onStepClick={setCurrentStep}
        />
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* ── STEP 1: Zaakgegevens ──────────────────────────────────────── */}
        <div className={currentStep !== 1 ? "hidden" : "space-y-6"}>
            <div className="rounded-xl border border-border bg-card p-6 space-y-4">
              <h2 className="text-base font-semibold text-foreground">
                Dossiergegevens
              </h2>

              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <label className="block text-sm font-medium text-foreground">
                    Dossiertype *
                  </label>
                  <select
                    value={form.case_type}
                    onChange={(e) => updateField("case_type", e.target.value)}
                    className={inputClass}
                  >
                    <option value="incasso">Incasso</option>
                    <option value="dossier">Dossier</option>
                    <option value="advies">Advies</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground">
                    Debiteurtype
                    <ConfidenceDot field="debtor_type" confidence={fieldConfidence} />
                  </label>
                  <select
                    value={form.debtor_type}
                    onChange={(e) => updateField("debtor_type", e.target.value)}
                    className={inputClass}
                  >
                    <option value="">Automatisch</option>
                    <option value="b2b">B2B (bedrijf)</option>
                    <option value="b2c">B2C (particulier)</option>
                  </select>
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    Wordt automatisch ingevuld bij selectie wederpartij
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground">
                    Datum geopend *
                  </label>
                  <input
                    type="date"
                    required
                    value={form.date_opened}
                    onChange={(e) => updateField("date_opened", e.target.value)}
                    onBlur={() => handleWizardBlur("date_opened")}
                    className={getWizardInputClass("date_opened")}
                  />
                  {wizardFieldErrors.date_opened && (
                    <p className="mt-1 text-xs text-destructive">{wizardFieldErrors.date_opened}</p>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground">
                  Beschrijving
                  <ConfidenceDot field="description" confidence={fieldConfidence} />
                </label>
                <textarea
                  value={form.description}
                  onChange={(e) => updateField("description", e.target.value)}
                  rows={2}
                  className={inputClass}
                  placeholder="Korte omschrijving van het dossier..."
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-foreground">
                    Referentie (klantreferentie)
                  </label>
                  <input
                    type="text"
                    value={form.reference}
                    onChange={(e) => updateField("reference", e.target.value)}
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground">
                    Zaaknummer rechtbank
                  </label>
                  <input
                    type="text"
                    value={form.court_case_number}
                    onChange={(e) =>
                      updateField("court_case_number", e.target.value)
                    }
                    className={inputClass}
                    placeholder="Bijv. C/13/123456 / HA ZA 24-789"
                  />
                </div>
              </div>

              {/* G13: Budget field */}
              {hasModule("budget") && (
                <div className="sm:w-1/2">
                  <label className="block text-sm font-medium text-foreground">
                    Budget
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={form.budget}
                    onChange={(e) => updateField("budget", e.target.value)}
                    className={inputClass}
                    placeholder="Bijv. 5000.00"
                  />
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    Optioneel budget in euro&apos;s voor dit dossier
                  </p>
                </div>
              )}
            </div>


        </div>

        {/* ── STEP 2: Partijen ──────────────────────────────────────────── */}
        <div className={currentStep !== 2 ? "hidden" : ""}>
          <div className="rounded-xl border border-border bg-card p-6 space-y-4">
            <h2 className="text-base font-semibold text-foreground">
              Partijen
            </h2>

            {/* Client selection */}
            <div>
              <label className="block text-sm font-medium text-foreground">
                Client *
                {invoiceData && <ConfidenceDot field="creditor_name" confidence={fieldConfidence} />}
              </label>
              {form.client_id ? (
                <div className="mt-1.5 flex items-center gap-2">
                  <span className="rounded-lg bg-primary/10 px-3 py-1.5 text-sm text-primary font-medium">
                    {clientResults?.items.find((c) => c.id === form.client_id)
                      ?.name ||
                      prefillClientName ||
                      "Geselecteerd"}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      updateField("client_id", "");
                      setClientSearch("");
                    }}
                    className="text-xs text-destructive hover:underline"
                  >
                    Wijzigen
                  </button>
                </div>
              ) : (
                <div className="mt-1.5">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <input
                      type="text"
                      value={clientSearch}
                      onChange={(e) => setClientSearch(e.target.value)}
                      className={`w-full rounded-lg border bg-background pl-10 pr-4 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 transition-colors ${
                        wizardFieldErrors.client_id
                          ? "border-destructive focus:border-destructive focus:ring-destructive/20"
                          : "border-input focus:border-primary focus:ring-primary/20"
                      }`}
                      placeholder="Zoek een client..."
                    />
                  </div>
                  {wizardFieldErrors.client_id && (
                    <p className="mt-1 text-xs text-destructive">{wizardFieldErrors.client_id}</p>
                  )}
                  {clientSearch &&
                    clientResults?.items &&
                    clientResults.items.length > 0 && (
                      <div className="mt-1 rounded-lg border border-border bg-card shadow-lg overflow-hidden">
                        {clientResults.items.map((contact) => (
                          <button
                            key={contact.id}
                            type="button"
                            onClick={() => {
                              updateField("client_id", contact.id);
                              setClientSearch(contact.name);
                            }}
                            className="w-full px-4 py-2.5 text-left text-sm hover:bg-muted transition-colors"
                          >
                            {contact.name}
                            <span className="ml-2 text-xs text-muted-foreground">
                              {contact.contact_type === "company"
                                ? "Bedrijf"
                                : "Persoon"}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                  {!showNewClient && (
                    <button
                      type="button"
                      onClick={() => {
                        setShowNewClient(true);
                        setNewClient((c) => ({ ...c, name: clientSearch }));
                      }}
                      className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      Nieuwe relatie aanmaken
                    </button>
                  )}
                  {showNewClient && (
                    <div className="mt-2 rounded-lg border border-primary/20 bg-primary/5 p-3 space-y-2 animate-fade-in">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-primary">
                          Nieuwe client aanmaken
                        </span>
                        <button
                          type="button"
                          onClick={() => setShowNewClient(false)}
                          className="text-muted-foreground hover:text-foreground"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      <div className="grid gap-2 sm:grid-cols-3">
                        <select
                          value={newClient.contact_type}
                          onChange={(e) =>
                            setNewClient((c) => ({
                              ...c,
                              contact_type: e.target.value as any,
                            }))
                          }
                          className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                        >
                          <option value="company">Bedrijf</option>
                          <option value="person">Persoon</option>
                        </select>
                        <input
                          type="text"
                          placeholder="Naam *"
                          value={newClient.name}
                          onChange={(e) =>
                            setNewClient((c) => ({
                              ...c,
                              name: e.target.value,
                            }))
                          }
                          className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                        />
                        <input
                          type="email"
                          placeholder="E-mail (optioneel)"
                          value={newClient.email}
                          onChange={(e) =>
                            setNewClient((c) => ({
                              ...c,
                              email: e.target.value,
                            }))
                          }
                          className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                        />
                      </div>
                      <InlineContactDetails
                        data={newClient}
                        onChange={(updates) => setNewClient((c) => ({ ...c, ...updates }))}
                        expanded={showClientDetails}
                        onToggle={() => setShowClientDetails((v) => !v)}
                      />
                      <button
                        type="button"
                        disabled={
                          !newClient.name.trim() || createRelation.isPending
                        }
                        onClick={() =>
                          handleCreateInlineContact("client", newClient)
                        }
                        className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                      >
                        {createRelation.isPending
                          ? "Aanmaken..."
                          : "Aanmaken en selecteren"}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Client conflict warning */}
            {clientConflict?.has_conflict && (
              <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-amber-800">
                      Conflict gedetecteerd
                    </p>
                    <p className="mt-0.5 text-xs text-amber-700">
                      Deze cli&euml;nt is in{" "}
                      {clientConflict.conflicts.length === 1
                        ? "een ander dossier"
                        : `${clientConflict.conflicts.length} andere dossiers`}{" "}
                      wederpartij:
                    </p>
                    <ul className="mt-1 space-y-0.5">
                      {clientConflict.conflicts.map((c) => (
                        <li key={c.case_id} className="text-xs text-amber-700">
                          <span className="font-mono font-medium">
                            {c.case_number}
                          </span>
                          {" — wederpartij van "}
                          <span className="font-medium">{c.client_name}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Client KYC warning */}
            {form.client_id &&
              clientKycStatus &&
              !clientKycStatus.is_compliant && (
                <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3">
                  <div className="flex items-start gap-2">
                    <ShieldAlert className="h-4 w-4 text-red-600 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-red-800">
                        WWFT-verificatie niet voltooid
                      </p>
                      <p className="mt-0.5 text-xs text-red-700">
                        {clientKycStatus.status === "niet_gestart"
                          ? "Deze cli\u00EBnt heeft nog geen WWFT/KYC verificatie. Dit is wettelijk verplicht voordat juridische diensten worden verleend."
                          : clientKycStatus.is_overdue
                          ? "De WWFT-verificatie van deze cli\u00EBnt is verlopen en moet opnieuw worden beoordeeld."
                          : "De WWFT-verificatie van deze cli\u00EBnt is nog niet afgerond."}
                      </p>
                      <Link
                        href={`/relaties/${form.client_id}`}
                        className="mt-1.5 inline-block text-xs font-medium text-red-700 hover:text-red-900 underline"
                      >
                        Ga naar verificatie &rarr;
                      </Link>
                    </div>
                  </div>
                </div>
              )}

            {/* Opposing party selection */}
            <div>
              <label className="block text-sm font-medium text-foreground">
                Wederpartij
                {invoiceData && <ConfidenceDot field="debtor_name" confidence={fieldConfidence} />}
              </label>
              {form.opposing_party_id ? (
                <div className="mt-1.5 flex items-center gap-2">
                  <span className="rounded-lg bg-warning/10 px-3 py-1.5 text-sm text-warning font-medium">
                    {opponentResults?.items.find(
                      (c) => c.id === form.opposing_party_id
                    )?.name ||
                      prefillOpponentName ||
                      "Geselecteerd"}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      updateField("opposing_party_id", "");
                      setOpponentSearch("");
                      setOpponentContactType("");
                    }}
                    className="text-xs text-destructive hover:underline"
                  >
                    Wijzigen
                  </button>
                </div>
              ) : (
                <div className="mt-1.5">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <input
                      type="text"
                      value={opponentSearch}
                      onChange={(e) => setOpponentSearch(e.target.value)}
                      className="w-full rounded-lg border border-input bg-background pl-10 pr-4 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                      placeholder="Zoek een wederpartij..."
                    />
                  </div>
                  {opponentSearch &&
                    opponentResults?.items &&
                    opponentResults.items.length > 0 && (
                      <div className="mt-1 rounded-lg border border-border bg-card shadow-lg overflow-hidden">
                        {opponentResults.items.map((contact) => (
                          <button
                            key={contact.id}
                            type="button"
                            onClick={() => {
                              updateField("opposing_party_id", contact.id);
                              setOpponentSearch(contact.name);
                              setOpponentContactType(contact.contact_type);
                              if (!form.debtor_type) {
                                updateField(
                                  "debtor_type",
                                  contact.contact_type === "company"
                                    ? "b2b"
                                    : "b2c"
                                );
                              }
                            }}
                            className="w-full px-4 py-2.5 text-left text-sm hover:bg-muted transition-colors"
                          >
                            {contact.name}
                            <span className="ml-2 text-xs text-muted-foreground">
                              {contact.contact_type === "company"
                                ? "Bedrijf"
                                : "Persoon"}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                  {!showNewOpponent && (
                    <button
                      type="button"
                      onClick={() => {
                        setShowNewOpponent(true);
                        setNewOpponent((c) => ({
                          ...c,
                          name: opponentSearch,
                        }));
                      }}
                      className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      Nieuwe relatie aanmaken
                    </button>
                  )}
                  {showNewOpponent && (
                    <div className="mt-2 rounded-lg border border-primary/20 bg-primary/5 p-3 space-y-2 animate-fade-in">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-primary">
                          Nieuwe wederpartij aanmaken
                        </span>
                        <button
                          type="button"
                          onClick={() => setShowNewOpponent(false)}
                          className="text-muted-foreground hover:text-foreground"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      <div className="grid gap-2 sm:grid-cols-3">
                        <select
                          value={newOpponent.contact_type}
                          onChange={(e) =>
                            setNewOpponent((c) => ({
                              ...c,
                              contact_type: e.target.value as any,
                            }))
                          }
                          className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                        >
                          <option value="company">Bedrijf</option>
                          <option value="person">Persoon</option>
                        </select>
                        <input
                          type="text"
                          placeholder="Naam *"
                          value={newOpponent.name}
                          onChange={(e) =>
                            setNewOpponent((c) => ({
                              ...c,
                              name: e.target.value,
                            }))
                          }
                          className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                        />
                        <input
                          type="email"
                          placeholder="E-mail (optioneel)"
                          value={newOpponent.email}
                          onChange={(e) =>
                            setNewOpponent((c) => ({
                              ...c,
                              email: e.target.value,
                            }))
                          }
                          className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                        />
                      </div>
                      <InlineContactDetails
                        data={newOpponent}
                        onChange={(updates) => setNewOpponent((c) => ({ ...c, ...updates }))}
                        expanded={showOpponentDetails}
                        onToggle={() => setShowOpponentDetails((v) => !v)}
                      />
                      <button
                        type="button"
                        disabled={
                          !newOpponent.name.trim() || createRelation.isPending
                        }
                        onClick={() =>
                          handleCreateInlineContact("opponent", newOpponent)
                        }
                        className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                      >
                        {createRelation.isPending
                          ? "Aanmaken..."
                          : "Aanmaken en selecteren"}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Opposing party conflict warning */}
            {opponentConflict?.has_conflict && (
              <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-amber-800">
                      Conflict gedetecteerd
                    </p>
                    <p className="mt-0.5 text-xs text-amber-700">
                      Deze wederpartij is in{" "}
                      {opponentConflict.conflicts.length === 1
                        ? "een ander dossier"
                        : `${opponentConflict.conflicts.length} andere dossiers`}{" "}
                      cli&euml;nt:
                    </p>
                    <ul className="mt-1 space-y-0.5">
                      {opponentConflict.conflicts.map((c) => (
                        <li key={c.case_id} className="text-xs text-amber-700">
                          <span className="font-mono font-medium">
                            {c.case_number}
                          </span>
                          {" — cli\u00EBnt"}
                          {c.opposing_party_name && (
                            <span> vs. {c.opposing_party_name}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Advocaat wederpartij selection */}
            <div>
              <label className="block text-sm font-medium text-foreground">
                Advocaat wederpartij
              </label>
              {selectedLawyer ? (
                <div className="mt-1.5 flex items-center gap-2">
                  <span className="rounded-lg bg-violet-50 px-3 py-1.5 text-sm text-violet-700 font-medium">
                    {selectedLawyer.name}
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedLawyer(null);
                      setLawyerSearch("");
                    }}
                    className="text-xs text-destructive hover:underline"
                  >
                    Wijzigen
                  </button>
                </div>
              ) : (
                <div className="mt-1.5">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <input
                      type="text"
                      value={lawyerSearch}
                      onChange={(e) => setLawyerSearch(e.target.value)}
                      className="w-full rounded-lg border border-input bg-background pl-10 pr-4 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                      placeholder="Zoek advocaat wederpartij..."
                    />
                  </div>
                  {lawyerSearch &&
                    lawyerResults?.items &&
                    lawyerResults.items.length > 0 && (
                      <div className="mt-1 rounded-lg border border-border bg-card shadow-lg overflow-hidden">
                        {lawyerResults.items.map((contact) => (
                          <button
                            key={contact.id}
                            type="button"
                            onClick={() => {
                              setSelectedLawyer({
                                id: contact.id,
                                name: contact.name,
                              });
                              setLawyerSearch(contact.name);
                            }}
                            className="w-full px-4 py-2.5 text-left text-sm hover:bg-muted transition-colors"
                          >
                            {contact.name}
                            <span className="ml-2 text-xs text-muted-foreground">
                              {contact.contact_type === "company"
                                ? "Bedrijf"
                                : "Persoon"}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                  {!showNewLawyer && (
                    <button
                      type="button"
                      onClick={() => {
                        setShowNewLawyer(true);
                        setNewLawyer((c) => ({ ...c, name: lawyerSearch }));
                      }}
                      className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      Nieuwe advocaat aanmaken
                    </button>
                  )}
                  {showNewLawyer && (
                    <div className="mt-2 rounded-lg border border-violet-200 bg-violet-50 p-3 space-y-2 animate-fade-in">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-violet-700">
                          Nieuwe advocaat wederpartij aanmaken
                        </span>
                        <button
                          type="button"
                          onClick={() => setShowNewLawyer(false)}
                          className="text-muted-foreground hover:text-foreground"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </div>
                      <div className="grid gap-2 sm:grid-cols-2">
                        <input
                          type="text"
                          placeholder="Naam *"
                          value={newLawyer.name}
                          onChange={(e) =>
                            setNewLawyer((c) => ({
                              ...c,
                              name: e.target.value,
                            }))
                          }
                          className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                        />
                        <input
                          type="email"
                          placeholder="E-mail (optioneel)"
                          value={newLawyer.email}
                          onChange={(e) =>
                            setNewLawyer((c) => ({
                              ...c,
                              email: e.target.value,
                            }))
                          }
                          className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                        />
                      </div>
                      <InlineContactDetails
                        data={newLawyer}
                        onChange={(updates) => setNewLawyer((c) => ({ ...c, ...updates }))}
                        expanded={showLawyerDetails}
                        onToggle={() => setShowLawyerDetails((v) => !v)}
                      />
                      <button
                        type="button"
                        disabled={
                          !newLawyer.name.trim() || createRelation.isPending
                        }
                        onClick={() =>
                          handleCreateInlineContact("lawyer", newLawyer)
                        }
                        className="rounded-md bg-violet-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-violet-700 disabled:opacity-50 transition-colors"
                      >
                        {createRelation.isPending
                          ? "Aanmaken..."
                          : "Aanmaken en selecteren"}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── STEP 3: Vordering (incasso only) ──────────────────────────── */}
        <div className={currentStep !== 3 || !isIncasso ? "hidden" : ""}>
          <div className="space-y-4">
            <div className="rounded-xl border border-border bg-card p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-foreground">
                    Vorderingen
                  </h2>
                  <p className="text-xs text-muted-foreground">
                    Voeg een of meerdere vorderingen toe aan dit dossier.
                    Dit kan ook later.
                  </p>
                </div>
              </div>

              {claims.map((claim, index) => (
                <div
                  key={index}
                  className="rounded-lg border border-border bg-background p-4 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium text-foreground">
                        Vordering {index + 1}
                      </span>
                    </div>
                    {claims.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeClaim(index)}
                        className="rounded-md p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="sm:col-span-2">
                      <label className="block text-sm font-medium text-foreground">
                        Omschrijving
                        {index === 0 && invoiceData && <ConfidenceDot field="description" confidence={fieldConfidence} />}
                      </label>
                      <input
                        type="text"
                        value={claim.description}
                        onChange={(e) =>
                          updateClaim(index, "description", e.target.value)
                        }
                        className={inputClass}
                        placeholder="Bijv. Factuur nr. 2025-001"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-foreground">
                        Hoofdsom
                        {index === 0 && invoiceData && <ConfidenceDot field="principal_amount" confidence={fieldConfidence} />}
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={claim.principal_amount}
                        onChange={(e) =>
                          updateClaim(
                            index,
                            "principal_amount",
                            e.target.value
                          )
                        }
                        className={inputClass}
                        placeholder="0.00"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-foreground">
                        Verzuimdatum
                        {index === 0 && invoiceData && <ConfidenceDot field="due_date" confidence={fieldConfidence} />}
                      </label>
                      <input
                        type="date"
                        value={claim.default_date}
                        onChange={(e) =>
                          updateClaim(index, "default_date", e.target.value)
                        }
                        className={inputClass}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-foreground">
                        Factuurnummer
                        {index === 0 && invoiceData && <ConfidenceDot field="invoice_number" confidence={fieldConfidence} />}
                      </label>
                      <input
                        type="text"
                        value={claim.invoice_number}
                        onChange={(e) =>
                          updateClaim(index, "invoice_number", e.target.value)
                        }
                        className={inputClass}
                        placeholder="Optioneel"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-foreground">
                        Factuurdatum
                        {index === 0 && invoiceData && <ConfidenceDot field="invoice_date" confidence={fieldConfidence} />}
                      </label>
                      <input
                        type="date"
                        value={claim.invoice_date}
                        onChange={(e) =>
                          updateClaim(index, "invoice_date", e.target.value)
                        }
                        className={inputClass}
                      />
                    </div>
                  </div>
                </div>
              ))}

              <button
                type="button"
                onClick={addClaim}
                className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
              >
                <Plus className="h-4 w-4" />
                Nog een vordering toevoegen
              </button>
            </div>

            {/* Interest settings — moved from step 1 to step 3 */}
            <div className="rounded-xl border border-border bg-card p-6 space-y-4">
              <h2 className="text-base font-semibold text-foreground">
                Rente-instellingen
              </h2>

              <div>
                <label className="block text-sm font-medium text-foreground">
                  Type rente
                </label>
                <select
                  value={form.interest_type}
                  onChange={(e) =>
                    updateField("interest_type", e.target.value)
                  }
                  className={inputClass}
                >
                  <option value="statutory">
                    Wettelijke rente (art. 6:119 BW)
                  </option>
                  <option value="commercial">
                    Handelsrente (art. 6:119a BW)
                  </option>
                  <option value="government">
                    Overheidsrente (art. 6:119b BW)
                  </option>
                  <option value="contractual">Contractuele rente</option>
                </select>
              </div>

              {form.interest_type === "contractual" && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-foreground">
                      Contractueel rentepercentage (%) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      required={form.interest_type === "contractual"}
                      value={form.contractual_rate}
                      onChange={(e) =>
                        updateField("contractual_rate", e.target.value)
                      }
                      onBlur={() => handleWizardBlur("contractual_rate")}
                      className={getWizardInputClass("contractual_rate")}
                      placeholder="Bijv. 8.00"
                    />
                    {wizardFieldErrors.contractual_rate && (
                      <p className="mt-1 text-xs text-destructive">{wizardFieldErrors.contractual_rate}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground">
                      Rentefrequentie
                    </label>
                    <select
                      value={form.rate_basis}
                      onChange={(e) =>
                        updateField("rate_basis", e.target.value)
                      }
                      className={inputClass}
                    >
                      <option value="yearly">Per jaar</option>
                      <option value="monthly">Per maand</option>
                    </select>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* ── Error display ─────────────────────────────────────────────── */}
        {error && (
          <div className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* ── Navigation buttons ────────────────────────────────────────── */}
        <div className="flex items-center justify-between">
          <div>
            {currentStep > 1 && (
              <button
                type="button"
                onClick={handlePrev}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border px-4 py-2.5 text-sm font-medium text-foreground hover:bg-muted transition-colors"
              >
                <ChevronLeft className="h-4 w-4" />
                Vorige
              </button>
            )}
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/zaken"
              className="rounded-lg border border-border px-4 py-2.5 text-sm font-medium text-foreground hover:bg-muted transition-colors"
            >
              Annuleren
            </Link>

            {isLastStep ? (
              <button
                key="submit"
                type="submit"
                disabled={isSubmitting}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? "Aanmaken..." : "Dossier aanmaken"}
              </button>
            ) : (
              <button
                key="next"
                type="button"
                onClick={handleNext}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
              >
                Volgende
                <ChevronRight className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
