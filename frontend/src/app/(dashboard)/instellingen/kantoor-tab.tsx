"use client";

import { useState } from "react";
import { useUnsavedWarning } from "@/hooks/use-unsaved-warning";
import { Save, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useTenant, useUpdateTenant } from "@/hooks/use-settings";

export function KantoorTab() {
  const { data: tenant, isLoading } = useTenant();
  const updateTenant = useUpdateTenant();

  const [form, setForm] = useState({
    name: "",
    kvk_number: "",
    btw_number: "",
    address: "",
    postal_code: "",
    city: "",
    phone: "",
    email: "",
    iban: "",
    trust_account_iban: "",
    trust_account_holder: "",
    trust_account_bic: "",
  });
  const [initialized, setInitialized] = useState(false);

  // Initialize form when tenant data loads
  if (tenant && !initialized) {
    setForm({
      name: tenant.name || "",
      kvk_number: tenant.kvk_number || "",
      btw_number: tenant.btw_number || "",
      address: tenant.address || "",
      postal_code: tenant.postal_code || "",
      city: tenant.city || "",
      phone: tenant.phone || "",
      email: tenant.email || "",
      iban: tenant.iban || "",
      trust_account_iban: tenant.trust_account_iban || "",
      trust_account_holder: tenant.trust_account_holder || "",
      trust_account_bic: tenant.trust_account_bic || "",
    });
    setInitialized(true);
  }

  const isDirty = initialized && tenant && (
    form.name !== (tenant.name || "") ||
    form.kvk_number !== (tenant.kvk_number || "") ||
    form.btw_number !== (tenant.btw_number || "") ||
    form.address !== (tenant.address || "") ||
    form.postal_code !== (tenant.postal_code || "") ||
    form.city !== (tenant.city || "") ||
    form.phone !== (tenant.phone || "") ||
    form.email !== (tenant.email || "") ||
    form.iban !== (tenant.iban || "") ||
    form.trust_account_iban !== (tenant.trust_account_iban || "") ||
    form.trust_account_holder !== (tenant.trust_account_holder || "") ||
    form.trust_account_bic !== (tenant.trust_account_bic || "")
  );
  useUnsavedWarning(!!isDirty);

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  const handleSave = () => {
    updateTenant.mutate(
      {
        name: form.name || undefined,
        kvk_number: form.kvk_number || null,
        btw_number: form.btw_number || null,
        address: form.address || null,
        postal_code: form.postal_code || null,
        city: form.city || null,
        phone: form.phone || null,
        email: form.email || null,
        iban: form.iban || null,
        trust_account_iban: form.trust_account_iban || null,
        trust_account_holder: form.trust_account_holder || null,
        trust_account_bic: form.trust_account_bic || null,
      },
      {
        onSuccess: () => toast.success("Kantoorgegevens bijgewerkt"),
      }
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          <div className="h-5 w-40 rounded skeleton" />
          <div className="grid gap-4 sm:grid-cols-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="space-y-2">
                <div className="h-3 w-20 rounded skeleton" />
                <div className="h-9 w-full rounded skeleton" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold text-foreground mb-4">
          Kantoorgegevens
        </h2>
        <div className="space-y-4 max-w-md">
          <div>
            <label htmlFor="settings-office-name" className="block text-sm font-medium text-foreground">
              Kantoornaam
            </label>
            <input
              id="settings-office-name"
              type="text"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className={inputClass}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="settings-kvk-number" className="block text-sm font-medium text-foreground">
                KvK-nummer
              </label>
              <input
                id="settings-kvk-number"
                type="text"
                value={form.kvk_number}
                onChange={(e) =>
                  setForm((f) => ({ ...f, kvk_number: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label htmlFor="settings-btw-number" className="block text-sm font-medium text-foreground">
                BTW-nummer
              </label>
              <input
                id="settings-btw-number"
                type="text"
                value={form.btw_number}
                onChange={(e) =>
                  setForm((f) => ({ ...f, btw_number: e.target.value }))
                }
                className={inputClass}
              />
            </div>
          </div>
          <div>
            <label htmlFor="settings-address" className="block text-sm font-medium text-foreground">
              Adres
            </label>
            <input
              id="settings-address"
              type="text"
              value={form.address}
              onChange={(e) =>
                setForm((f) => ({ ...f, address: e.target.value }))
              }
              className={inputClass}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="settings-postal-code" className="block text-sm font-medium text-foreground">
                Postcode
              </label>
              <input
                id="settings-postal-code"
                type="text"
                value={form.postal_code}
                onChange={(e) =>
                  setForm((f) => ({ ...f, postal_code: e.target.value }))
                }
                className={inputClass}
              />
            </div>
            <div>
              <label htmlFor="settings-city" className="block text-sm font-medium text-foreground">
                Plaats
              </label>
              <input
                id="settings-city"
                type="text"
                value={form.city}
                onChange={(e) =>
                  setForm((f) => ({ ...f, city: e.target.value }))
                }
                className={inputClass}
              />
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="settings-phone" className="block text-sm font-medium text-foreground">
                Telefoonnummer
              </label>
              <input
                id="settings-phone"
                type="tel"
                value={form.phone}
                onChange={(e) =>
                  setForm((f) => ({ ...f, phone: e.target.value }))
                }
                placeholder="020 123 4567"
                className={inputClass}
              />
            </div>
            <div>
              <label htmlFor="settings-email" className="block text-sm font-medium text-foreground">
                E-mailadres
              </label>
              <input
                id="settings-email"
                type="email"
                value={form.email}
                onChange={(e) =>
                  setForm((f) => ({ ...f, email: e.target.value }))
                }
                placeholder="info@kantoor.nl"
                className={inputClass}
              />
            </div>
          </div>
          <div>
            <label htmlFor="settings-iban" className="block text-sm font-medium text-foreground">
              IBAN (kantoorrekening)
            </label>
            <input
              id="settings-iban"
              type="text"
              value={form.iban}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  iban: e.target.value.toUpperCase().replace(/\s/g, ""),
                }))
              }
              placeholder="NL00BANK0123456789"
              className={inputClass}
            />
            <p className="mt-1.5 text-xs text-muted-foreground">
              Wordt gebruikt op betaalsommaties en facturen als rekening voor de betaling.
              Apart van de Stichting Derdengelden hieronder.
            </p>
          </div>
          <button
            onClick={handleSave}
            disabled={updateTenant.isPending}
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {updateTenant.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            Opslaan
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-base font-semibold text-foreground mb-1">
          Stichting Derdengelden
        </h2>
        <p className="text-sm text-muted-foreground mb-4">
          Bankgegevens van je Stichting Derdengelden — gebruikt voor SEPA-uitbetalingen
          en NOvA-rapportages. Apart van de kantoorrekening hierboven.
        </p>
        <div className="space-y-4 max-w-md">
          <div>
            <label htmlFor="settings-trust-holder" className="block text-sm font-medium text-foreground">
              Tenaamstelling
            </label>
            <input
              id="settings-trust-holder"
              type="text"
              placeholder="Stichting Derdengelden Kesting Legal"
              value={form.trust_account_holder}
              onChange={(e) =>
                setForm((f) => ({ ...f, trust_account_holder: e.target.value }))
              }
              className={inputClass}
            />
          </div>
          <div>
            <label htmlFor="settings-trust-iban" className="block text-sm font-medium text-foreground">
              IBAN
            </label>
            <input
              id="settings-trust-iban"
              type="text"
              placeholder="NL44RABO0123456789"
              value={form.trust_account_iban}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  trust_account_iban: e.target.value.toUpperCase().replace(/\s/g, ""),
                }))
              }
              className={inputClass}
            />
          </div>
          <div>
            <label htmlFor="settings-trust-bic" className="block text-sm font-medium text-foreground">
              BIC (optioneel — vereist voor sommige banken)
            </label>
            <input
              id="settings-trust-bic"
              type="text"
              placeholder="RABONL2U"
              value={form.trust_account_bic}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  trust_account_bic: e.target.value.toUpperCase().replace(/\s/g, ""),
                }))
              }
              className={inputClass}
            />
          </div>
          <p className="text-xs text-muted-foreground">
            Wijzigingen worden opgeslagen via de knop &ldquo;Opslaan&rdquo; in de bovenste sectie.
          </p>
        </div>
      </div>
    </div>
  );
}
