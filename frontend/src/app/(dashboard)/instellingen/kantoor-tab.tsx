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
    });
    setInitialized(true);
  }

  const isDirty = initialized && tenant && (
    form.name !== (tenant.name || "") ||
    form.kvk_number !== (tenant.kvk_number || "") ||
    form.btw_number !== (tenant.btw_number || "") ||
    form.address !== (tenant.address || "") ||
    form.postal_code !== (tenant.postal_code || "") ||
    form.city !== (tenant.city || "")
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
        <h2 className="text-base font-semibold text-foreground mb-2">
          Standaard rente-instellingen
        </h2>
        <p className="text-sm text-muted-foreground mb-4">
          Standaard instellingen voor nieuwe dossiers
        </p>
        <div className="max-w-md space-y-4">
          <div>
            <label htmlFor="settings-interest-type" className="block text-sm font-medium text-foreground">
              Standaard rentetype
            </label>
            <select id="settings-interest-type" defaultValue="statutory" className={inputClass}>
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
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="btw_bik"
              defaultChecked
              className="h-4 w-4 rounded border-input accent-primary"
            />
            <label htmlFor="btw_bik" className="text-sm text-foreground">
              BTW over BIK berekenen (client is btw-plichtig)
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
