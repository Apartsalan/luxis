"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { useCreateRelation } from "@/hooks/use-relations";

export default function NieuweRelatiePage() {
  const router = useRouter();
  const createRelation = useCreateRelation();

  const [contactType, setContactType] = useState<"company" | "person">(
    "company"
  );
  const [form, setForm] = useState({
    name: "",
    first_name: "",
    last_name: "",
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
    default_interest_type: "",
    default_contractual_rate: "",
    default_rate_basis: "",
    default_bik_mode: "wik" as "wik" | "amount" | "percentage",
    default_bik_override: "",
    default_bik_override_percentage: "",
    default_minimum_fee: "",
    notes: "",
  });
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  // UX-16: Warn on unsaved changes
  const formDirty = form.name || form.first_name || form.last_name || form.email || form.phone;
  useEffect(() => {
    if (!formDirty) return;
    const handler = (e: BeforeUnloadEvent) => { e.preventDefault(); };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [formDirty]);

  const validateField = (field: string, value: string): string => {
    switch (field) {
      case "name":
        if (contactType === "company" && !value.trim()) return "Bedrijfsnaam is verplicht";
        break;
      case "first_name":
        if (contactType === "person" && !value.trim()) return "Voornaam is verplicht";
        break;
      case "last_name":
        if (contactType === "person" && !value.trim()) return "Achternaam is verplicht";
        break;
      case "email":
        if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return "Ongeldig e-mailadres";
        break;
      case "kvk_number":
        if (value && !/^\d{8}$/.test(value)) return "KvK-nummer moet 8 cijfers zijn";
        break;
      case "visit_postcode":
      case "postal_postcode":
        if (value && !/^\d{4}\s?[A-Za-z]{2}$/.test(value)) return "Ongeldige postcode (bijv. 1234 AB)";
        break;
    }
    return "";
  };

  const handleBlur = (field: string) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
    const err = validateField(field, form[field as keyof typeof form] || "");
    setFieldErrors((prev) => ({ ...prev, [field]: err }));
  };

  const validateAll = (): boolean => {
    const errors: Record<string, string> = {};
    if (contactType === "company") {
      errors.name = validateField("name", form.name);
    } else {
      errors.first_name = validateField("first_name", form.first_name);
      errors.last_name = validateField("last_name", form.last_name);
    }
    errors.email = validateField("email", form.email);
    errors.kvk_number = validateField("kvk_number", form.kvk_number);
    errors.visit_postcode = validateField("visit_postcode", form.visit_postcode);
    errors.postal_postcode = validateField("postal_postcode", form.postal_postcode);
    setFieldErrors(errors);
    setTouched(Object.fromEntries(Object.keys(errors).map((k) => [k, true])));
    return !Object.values(errors).some(Boolean);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!validateAll()) return;

    const data = {
      contact_type: contactType,
      name:
        contactType === "person"
          ? `${form.first_name} ${form.last_name}`.trim()
          : form.name,
      ...(contactType === "person" && {
        first_name: form.first_name,
        last_name: form.last_name,
      }),
      ...(form.email && { email: form.email }),
      ...(form.phone && { phone: form.phone }),
      ...(form.kvk_number && { kvk_number: form.kvk_number }),
      ...(form.btw_number && { btw_number: form.btw_number }),
      ...(form.visit_address && { visit_address: form.visit_address }),
      ...(form.visit_postcode && { visit_postcode: form.visit_postcode }),
      ...(form.visit_city && { visit_city: form.visit_city }),
      ...(form.postal_address && { postal_address: form.postal_address }),
      ...(form.postal_postcode && { postal_postcode: form.postal_postcode }),
      ...(form.postal_city && { postal_city: form.postal_city }),
      ...(form.default_interest_type && { default_interest_type: form.default_interest_type }),
      ...(form.default_interest_type === "contractual" && form.default_contractual_rate && {
        default_contractual_rate: form.default_contractual_rate,
      }),
      ...(form.default_rate_basis && { default_rate_basis: form.default_rate_basis }),
      ...(form.default_bik_mode === "amount" && form.default_bik_override && {
        default_bik_override: form.default_bik_override,
      }),
      ...(form.default_bik_mode === "percentage" && form.default_bik_override_percentage && {
        default_bik_override_percentage: form.default_bik_override_percentage,
      }),
      ...(form.default_minimum_fee && { default_minimum_fee: form.default_minimum_fee }),
      ...(form.notes && { notes: form.notes }),
    };

    try {
      const result = await createRelation.mutateAsync(data);
      toast.success("Relatie aangemaakt");
      router.push(`/relaties/${result.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Er ging iets mis");
    }
  };

  const updateField = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";
  const inputErrorClass =
    "mt-1.5 w-full rounded-lg border border-destructive bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-destructive focus:outline-none focus:ring-2 focus:ring-destructive/20 transition-colors";

  const getInputClass = (field: string) =>
    touched[field] && fieldErrors[field] ? inputErrorClass : inputClass;

  const FieldError = ({ field }: { field: string }) =>
    touched[field] && fieldErrors[field] ? (
      <p className="mt-1 text-xs text-destructive">{fieldErrors[field]}</p>
    ) : null;

  return (
    <div className="mx-auto max-w-2xl space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <Link
          href="/relaties"
          className="rounded-lg p-2 hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-muted-foreground" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Nieuwe relatie</h1>
          <p className="text-sm text-muted-foreground">
            Voeg een nieuw contact toe
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Type selector */}
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => setContactType("company")}
            className={`flex-1 rounded-lg border p-3 text-sm font-medium transition-all ${
              contactType === "company"
                ? "border-primary bg-primary/5 text-primary ring-1 ring-primary/20"
                : "border-border text-muted-foreground hover:border-primary/30"
            }`}
          >
            Bedrijf
          </button>
          <button
            type="button"
            onClick={() => setContactType("person")}
            className={`flex-1 rounded-lg border p-3 text-sm font-medium transition-all ${
              contactType === "person"
                ? "border-primary bg-primary/5 text-primary ring-1 ring-primary/20"
                : "border-border text-muted-foreground hover:border-primary/30"
            }`}
          >
            Persoon
          </button>
        </div>

        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          {contactType === "company" ? (
            <div>
              <label htmlFor="rel-name" className="block text-sm font-medium text-foreground">
                Bedrijfsnaam *
              </label>
              <input
                id="rel-name"
                type="text"
                required
                value={form.name}
                onChange={(e) => updateField("name", e.target.value)}
                onBlur={() => handleBlur("name")}
                className={getInputClass("name")}
                placeholder="Acme B.V."
              />
              <FieldError field="name" />
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="rel-first_name" className="block text-sm font-medium text-foreground">
                  Voornaam *
                </label>
                <input
                  id="rel-first_name"
                  type="text"
                  required
                  value={form.first_name}
                  onChange={(e) => updateField("first_name", e.target.value)}
                  onBlur={() => handleBlur("first_name")}
                  className={getInputClass("first_name")}
                />
                <FieldError field="first_name" />
              </div>
              <div>
                <label htmlFor="rel-last_name" className="block text-sm font-medium text-foreground">
                  Achternaam *
                </label>
                <input
                  id="rel-last_name"
                  type="text"
                  required
                  value={form.last_name}
                  onChange={(e) => updateField("last_name", e.target.value)}
                  onBlur={() => handleBlur("last_name")}
                  className={getInputClass("last_name")}
                />
                <FieldError field="last_name" />
              </div>
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="rel-email" className="block text-sm font-medium text-foreground">
                E-mail
              </label>
              <input
                id="rel-email"
                type="email"
                value={form.email}
                onChange={(e) => updateField("email", e.target.value)}
                onBlur={() => handleBlur("email")}
                className={getInputClass("email")}
              />
              <FieldError field="email" />
            </div>
            <div>
              <label htmlFor="rel-phone" className="block text-sm font-medium text-foreground">
                Telefoon
              </label>
              <input
                id="rel-phone"
                type="tel"
                value={form.phone}
                onChange={(e) => updateField("phone", e.target.value)}
                className={inputClass}
              />
            </div>
          </div>

          {contactType === "company" && (
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="rel-kvk_number" className="block text-sm font-medium text-foreground">
                  KvK-nummer
                </label>
                <input
                  id="rel-kvk_number"
                  type="text"
                  value={form.kvk_number}
                  onChange={(e) => updateField("kvk_number", e.target.value)}
                  onBlur={() => handleBlur("kvk_number")}
                  className={getInputClass("kvk_number")}
                  maxLength={8}
                />
                <FieldError field="kvk_number" />
              </div>
              <div>
                <label htmlFor="rel-btw_number" className="block text-sm font-medium text-foreground">
                  BTW-nummer
                </label>
                <input
                  id="rel-btw_number"
                  type="text"
                  value={form.btw_number}
                  onChange={(e) => updateField("btw_number", e.target.value)}
                  className={inputClass}
                  placeholder="NL123456789B01"
                />
              </div>
            </div>
          )}

          <h3 className="pt-2 text-sm font-semibold text-foreground">Bezoekadres</h3>
          <div>
            <label htmlFor="rel-visit_address" className="block text-sm font-medium text-foreground">
              Straat + huisnummer
            </label>
            <input
              id="rel-visit_address"
              type="text"
              value={form.visit_address}
              onChange={(e) => updateField("visit_address", e.target.value)}
              className={inputClass}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="rel-visit_postcode" className="block text-sm font-medium text-foreground">
                Postcode
              </label>
              <input
                id="rel-visit_postcode"
                type="text"
                value={form.visit_postcode}
                onChange={(e) => updateField("visit_postcode", e.target.value)}
                onBlur={() => handleBlur("visit_postcode")}
                className={getInputClass("visit_postcode")}
                placeholder="1234 AB"
              />
              <FieldError field="visit_postcode" />
            </div>
            <div>
              <label htmlFor="rel-visit_city" className="block text-sm font-medium text-foreground">
                Plaats
              </label>
              <input
                id="rel-visit_city"
                type="text"
                value={form.visit_city}
                onChange={(e) => updateField("visit_city", e.target.value)}
                className={inputClass}
              />
            </div>
          </div>

          <h3 className="pt-2 text-sm font-semibold text-foreground">Postadres</h3>
          <p className="text-xs text-muted-foreground -mt-2">Alleen invullen als dit afwijkt van het bezoekadres</p>
          <div>
            <label htmlFor="rel-postal_address" className="block text-sm font-medium text-foreground">
              Straat + huisnummer
            </label>
            <input
              id="rel-postal_address"
              type="text"
              value={form.postal_address}
              onChange={(e) => updateField("postal_address", e.target.value)}
              className={inputClass}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="rel-postal_postcode" className="block text-sm font-medium text-foreground">
                Postcode
              </label>
              <input
                id="rel-postal_postcode"
                type="text"
                value={form.postal_postcode}
                onChange={(e) => updateField("postal_postcode", e.target.value)}
                onBlur={() => handleBlur("postal_postcode")}
                className={getInputClass("postal_postcode")}
                placeholder="1234 AB"
              />
              <FieldError field="postal_postcode" />
            </div>
            <div>
              <label htmlFor="rel-postal_city" className="block text-sm font-medium text-foreground">
                Plaats
              </label>
              <input
                id="rel-postal_city"
                type="text"
                value={form.postal_city}
                onChange={(e) => updateField("postal_city", e.target.value)}
                className={inputClass}
              />
            </div>
          </div>

          <h3 className="pt-2 text-sm font-semibold text-foreground">Standaard rente & incassokosten</h3>
          <p className="text-xs text-muted-foreground -mt-2">
            Wordt automatisch overgenomen bij het aanmaken van een nieuw dossier voor deze klant. Per dossier wijzigbaar.
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="rel-default_interest_type" className="block text-sm font-medium text-foreground">
                Rentetype
              </label>
              <select
                id="rel-default_interest_type"
                value={form.default_interest_type}
                onChange={(e) => updateField("default_interest_type", e.target.value)}
                className={inputClass}
              >
                <option value="">Geen standaard (kies per dossier)</option>
                <option value="statutory">Wettelijke rente (art. 6:119 BW)</option>
                <option value="commercial">Handelsrente (art. 6:119a BW)</option>
                <option value="government">Overheidsrente (art. 6:119b BW)</option>
                <option value="contractual">Contractuele rente</option>
              </select>
            </div>
            {form.default_interest_type === "contractual" && (
              <div>
                <label htmlFor="rel-default_contractual_rate" className="block text-sm font-medium text-foreground">
                  Percentage (%)
                </label>
                <input
                  id="rel-default_contractual_rate"
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  value={form.default_contractual_rate}
                  onChange={(e) => updateField("default_contractual_rate", e.target.value)}
                  className={inputClass}
                  placeholder="Bijv. 8.00"
                />
              </div>
            )}
            {form.default_interest_type === "contractual" && (
              <div>
                <label htmlFor="rel-default_rate_basis" className="block text-sm font-medium text-foreground">
                  Periode
                </label>
                <select
                  id="rel-default_rate_basis"
                  value={form.default_rate_basis}
                  onChange={(e) => updateField("default_rate_basis", e.target.value)}
                  className={inputClass}
                >
                  <option value="">Per jaar (standaard)</option>
                  <option value="yearly">Per jaar</option>
                  <option value="monthly">Per maand</option>
                </select>
              </div>
            )}
          </div>

          {/* DF117-22: Standaard incassokosten (BIK) */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="rel-default_bik_mode" className="block text-sm font-medium text-foreground">
                Standaard incassokosten
              </label>
              <select
                id="rel-default_bik_mode"
                value={form.default_bik_mode}
                onChange={(e) => updateField("default_bik_mode", e.target.value)}
                className={inputClass}
              >
                <option value="wik">WIK-staffel (art. 6:96 BW)</option>
                <option value="amount">Vast bedrag</option>
                <option value="percentage">Percentage van hoofdsom</option>
              </select>
            </div>
            {form.default_bik_mode === "amount" && (
              <div>
                <label htmlFor="rel-default_bik_override" className="block text-sm font-medium text-foreground">
                  Vast bedrag (€)
                </label>
                <input
                  id="rel-default_bik_override"
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.default_bik_override}
                  onChange={(e) => updateField("default_bik_override", e.target.value)}
                  className={inputClass}
                  placeholder="Bijv. 250.00"
                />
              </div>
            )}
            {form.default_bik_mode === "percentage" && (
              <div>
                <label htmlFor="rel-default_bik_override_percentage" className="block text-sm font-medium text-foreground">
                  Percentage van hoofdsom (%)
                </label>
                <input
                  id="rel-default_bik_override_percentage"
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  value={form.default_bik_override_percentage}
                  onChange={(e) => updateField("default_bik_override_percentage", e.target.value)}
                  className={inputClass}
                  placeholder="Bijv. 10.00"
                />
              </div>
            )}
            <div>
              <label htmlFor="rel-default_minimum_fee" className="block text-sm font-medium text-foreground">
                Minimum provisie (€)
              </label>
              <input
                id="rel-default_minimum_fee"
                type="number"
                step="0.01"
                min="0"
                value={form.default_minimum_fee}
                onChange={(e) => updateField("default_minimum_fee", e.target.value)}
                className={inputClass}
                placeholder="Leeg = WIK-minimum (€40)"
              />
            </div>
          </div>

          <div>
            <label htmlFor="rel-notes" className="block text-sm font-medium text-foreground">
              Notities
            </label>
            <textarea
              id="rel-notes"
              value={form.notes}
              onChange={(e) => updateField("notes", e.target.value)}
              rows={3}
              className={inputClass}
            />
          </div>
        </div>

        {error && (
          <div className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={createRelation.isPending}
            className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {createRelation.isPending ? "Opslaan..." : "Opslaan"}
          </button>
          <Link
            href="/relaties"
            className="rounded-lg border border-border px-6 py-2.5 text-sm font-medium text-foreground hover:bg-muted transition-colors"
          >
            Annuleren
          </Link>
        </div>
      </form>
    </div>
  );
}
