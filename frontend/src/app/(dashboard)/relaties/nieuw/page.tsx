"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useCreateRelation } from "@/hooks/use-relations";

export default function NieuweRelatiePage() {
  const router = useRouter();
  const createRelation = useCreateRelation();

  const [contactType, setContactType] = useState<"company" | "person">("company");
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
    notes: "",
  });
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    const data = {
      contact_type: contactType,
      name: contactType === "person" ? `${form.first_name} ${form.last_name}`.trim() : form.name,
      ...(contactType === "person" && { first_name: form.first_name, last_name: form.last_name }),
      ...(form.email && { email: form.email }),
      ...(form.phone && { phone: form.phone }),
      ...(form.kvk_number && { kvk_number: form.kvk_number }),
      ...(form.btw_number && { btw_number: form.btw_number }),
      ...(form.visit_address && { visit_address: form.visit_address }),
      ...(form.visit_postcode && { visit_postcode: form.visit_postcode }),
      ...(form.visit_city && { visit_city: form.visit_city }),
      ...(form.notes && { notes: form.notes }),
    };

    try {
      const result = await createRelation.mutateAsync(data);
      router.push(`/relaties/${result.id}`);
    } catch (err: any) {
      setError(err.message || "Er ging iets mis");
    }
  };

  const updateField = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href="/relaties"
          className="rounded-md p-2 hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-navy-500" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-navy-800">Nieuwe relatie</h1>
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
            className={`flex-1 rounded-md border p-3 text-sm font-medium transition-colors ${
              contactType === "company"
                ? "border-navy-500 bg-navy-50 text-navy-700"
                : "border-border text-muted-foreground hover:border-navy-200"
            }`}
          >
            Bedrijf
          </button>
          <button
            type="button"
            onClick={() => setContactType("person")}
            className={`flex-1 rounded-md border p-3 text-sm font-medium transition-colors ${
              contactType === "person"
                ? "border-navy-500 bg-navy-50 text-navy-700"
                : "border-border text-muted-foreground hover:border-navy-200"
            }`}
          >
            Persoon
          </button>
        </div>

        <div className="rounded-lg border border-border bg-white p-6 space-y-4">
          {contactType === "company" ? (
            <div>
              <label className="block text-sm font-medium text-navy-700">
                Bedrijfsnaam *
              </label>
              <input
                type="text"
                required
                value={form.name}
                onChange={(e) => updateField("name", e.target.value)}
                className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm focus:border-navy-500 focus:outline-none focus:ring-1 focus:ring-navy-500"
                placeholder="Acme B.V."
              />
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-navy-700">
                  Voornaam *
                </label>
                <input
                  type="text"
                  required
                  value={form.first_name}
                  onChange={(e) => updateField("first_name", e.target.value)}
                  className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm focus:border-navy-500 focus:outline-none focus:ring-1 focus:ring-navy-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-navy-700">
                  Achternaam *
                </label>
                <input
                  type="text"
                  required
                  value={form.last_name}
                  onChange={(e) => updateField("last_name", e.target.value)}
                  className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm focus:border-navy-500 focus:outline-none focus:ring-1 focus:ring-navy-500"
                />
              </div>
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-navy-700">E-mail</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => updateField("email", e.target.value)}
                className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm focus:border-navy-500 focus:outline-none focus:ring-1 focus:ring-navy-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700">Telefoon</label>
              <input
                type="tel"
                value={form.phone}
                onChange={(e) => updateField("phone", e.target.value)}
                className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm focus:border-navy-500 focus:outline-none focus:ring-1 focus:ring-navy-500"
              />
            </div>
          </div>

          {contactType === "company" && (
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-navy-700">KvK-nummer</label>
                <input
                  type="text"
                  value={form.kvk_number}
                  onChange={(e) => updateField("kvk_number", e.target.value)}
                  className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm focus:border-navy-500 focus:outline-none focus:ring-1 focus:ring-navy-500"
                  maxLength={8}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-navy-700">BTW-nummer</label>
                <input
                  type="text"
                  value={form.btw_number}
                  onChange={(e) => updateField("btw_number", e.target.value)}
                  className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm focus:border-navy-500 focus:outline-none focus:ring-1 focus:ring-navy-500"
                  placeholder="NL123456789B01"
                />
              </div>
            </div>
          )}

          <h3 className="pt-2 text-sm font-semibold text-navy-700">Adres</h3>
          <div>
            <label className="block text-sm font-medium text-navy-700">Straat + huisnummer</label>
            <input
              type="text"
              value={form.visit_address}
              onChange={(e) => updateField("visit_address", e.target.value)}
              className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm focus:border-navy-500 focus:outline-none focus:ring-1 focus:ring-navy-500"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-navy-700">Postcode</label>
              <input
                type="text"
                value={form.visit_postcode}
                onChange={(e) => updateField("visit_postcode", e.target.value)}
                className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm focus:border-navy-500 focus:outline-none focus:ring-1 focus:ring-navy-500"
                placeholder="1234 AB"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700">Plaats</label>
              <input
                type="text"
                value={form.visit_city}
                onChange={(e) => updateField("visit_city", e.target.value)}
                className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm focus:border-navy-500 focus:outline-none focus:ring-1 focus:ring-navy-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-navy-700">Notities</label>
            <textarea
              value={form.notes}
              onChange={(e) => updateField("notes", e.target.value)}
              rows={3}
              className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm focus:border-navy-500 focus:outline-none focus:ring-1 focus:ring-navy-500"
            />
          </div>
        </div>

        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={createRelation.isPending}
            className="rounded-md bg-navy-500 px-6 py-2 text-sm font-medium text-white hover:bg-navy-600 disabled:opacity-50 transition-colors"
          >
            {createRelation.isPending ? "Opslaan..." : "Opslaan"}
          </button>
          <Link
            href="/relaties"
            className="rounded-md border border-border px-6 py-2 text-sm font-medium text-navy-600 hover:bg-muted transition-colors"
          >
            Annuleren
          </Link>
        </div>
      </form>
    </div>
  );
}
