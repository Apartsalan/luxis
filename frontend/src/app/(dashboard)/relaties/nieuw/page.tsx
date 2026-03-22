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
      ...(form.notes && { notes: form.notes }),
    };

    try {
      const result = await createRelation.mutateAsync(data);
      toast.success("Relatie aangemaakt");
      router.push(`/relaties/${result.id}`);
    } catch (err: any) {
      setError(err.message || "Er ging iets mis");
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
              <label className="block text-sm font-medium text-foreground">
                Bedrijfsnaam *
              </label>
              <input
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
                <label className="block text-sm font-medium text-foreground">
                  Voornaam *
                </label>
                <input
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
                <label className="block text-sm font-medium text-foreground">
                  Achternaam *
                </label>
                <input
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
              <label className="block text-sm font-medium text-foreground">
                E-mail
              </label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => updateField("email", e.target.value)}
                onBlur={() => handleBlur("email")}
                className={getInputClass("email")}
              />
              <FieldError field="email" />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground">
                Telefoon
              </label>
              <input
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
                <label className="block text-sm font-medium text-foreground">
                  KvK-nummer
                </label>
                <input
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
                <label className="block text-sm font-medium text-foreground">
                  BTW-nummer
                </label>
                <input
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
            <label className="block text-sm font-medium text-foreground">
              Straat + huisnummer
            </label>
            <input
              type="text"
              value={form.visit_address}
              onChange={(e) => updateField("visit_address", e.target.value)}
              className={inputClass}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-foreground">
                Postcode
              </label>
              <input
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
              <label className="block text-sm font-medium text-foreground">
                Plaats
              </label>
              <input
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
            <label className="block text-sm font-medium text-foreground">
              Straat + huisnummer
            </label>
            <input
              type="text"
              value={form.postal_address}
              onChange={(e) => updateField("postal_address", e.target.value)}
              className={inputClass}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-foreground">
                Postcode
              </label>
              <input
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
              <label className="block text-sm font-medium text-foreground">
                Plaats
              </label>
              <input
                type="text"
                value={form.postal_city}
                onChange={(e) => updateField("postal_city", e.target.value)}
                className={inputClass}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground">
              Notities
            </label>
            <textarea
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
