"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Search } from "lucide-react";
import { useCreateCase } from "@/hooks/use-cases";
import { useRelations } from "@/hooks/use-relations";

export default function NieuweZaakPage() {
  const router = useRouter();
  const createCase = useCreateCase();

  const [form, setForm] = useState({
    case_type: "incasso",
    description: "",
    reference: "",
    interest_type: "statutory",
    contractual_rate: "",
    client_id: "",
    opposing_party_id: "",
    date_opened: new Date().toISOString().split("T")[0],
  });
  const [clientSearch, setClientSearch] = useState("");
  const [opponentSearch, setOpponentSearch] = useState("");
  const [error, setError] = useState("");

  // Search for contacts for client/opponent selection
  const { data: clientResults } = useRelations({
    search: clientSearch || undefined,
    per_page: 5,
  });
  const { data: opponentResults } = useRelations({
    search: opponentSearch || undefined,
    per_page: 5,
  });

  const updateField = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!form.client_id) {
      setError("Selecteer een client");
      return;
    }

    const data: any = {
      case_type: form.case_type,
      interest_type: form.interest_type,
      client_id: form.client_id,
      date_opened: form.date_opened,
    };

    if (form.description) data.description = form.description;
    if (form.reference) data.reference = form.reference;
    if (form.opposing_party_id) data.opposing_party_id = form.opposing_party_id;
    if (form.interest_type === "contractual" && form.contractual_rate) {
      data.contractual_rate = parseFloat(form.contractual_rate);
    }

    try {
      const result = await createCase.mutateAsync(data);
      router.push(`/zaken/${result.id}`);
    } catch (err: any) {
      setError(err.message || "Er ging iets mis");
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href="/zaken"
          className="rounded-md p-2 hover:bg-muted transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-navy-500" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-navy-800">Nieuwe zaak</h1>
          <p className="text-sm text-muted-foreground">
            Maak een nieuw dossier aan
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="rounded-lg border border-border bg-white p-6 space-y-4">
          <h2 className="text-lg font-semibold text-navy-800">Zaakgegevens</h2>

          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-navy-700">
                Zaaktype *
              </label>
              <select
                value={form.case_type}
                onChange={(e) => updateField("case_type", e.target.value)}
                className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm"
              >
                <option value="incasso">Incasso</option>
                <option value="insolventie">Insolventie</option>
                <option value="advies">Advies</option>
                <option value="overig">Overig</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-navy-700">
                Datum geopend *
              </label>
              <input
                type="date"
                required
                value={form.date_opened}
                onChange={(e) => updateField("date_opened", e.target.value)}
                className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-navy-700">
              Beschrijving
            </label>
            <textarea
              value={form.description}
              onChange={(e) => updateField("description", e.target.value)}
              rows={2}
              className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm"
              placeholder="Korte omschrijving van de zaak..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-navy-700">
              Referentie (klantreferentie)
            </label>
            <input
              type="text"
              value={form.reference}
              onChange={(e) => updateField("reference", e.target.value)}
              className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm"
            />
          </div>
        </div>

        {/* Interest settings */}
        <div className="rounded-lg border border-border bg-white p-6 space-y-4">
          <h2 className="text-lg font-semibold text-navy-800">Rente-instellingen</h2>

          <div>
            <label className="block text-sm font-medium text-navy-700">
              Type rente
            </label>
            <select
              value={form.interest_type}
              onChange={(e) => updateField("interest_type", e.target.value)}
              className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm"
            >
              <option value="statutory">Wettelijke rente (art. 6:119 BW)</option>
              <option value="commercial">Handelsrente (art. 6:119a BW)</option>
              <option value="government">Overheidsrente (art. 6:119b BW)</option>
              <option value="contractual">Contractuele rente</option>
            </select>
          </div>

          {form.interest_type === "contractual" && (
            <div>
              <label className="block text-sm font-medium text-navy-700">
                Contractueel rentepercentage (%) *
              </label>
              <input
                type="number"
                step="0.01"
                required={form.interest_type === "contractual"}
                value={form.contractual_rate}
                onChange={(e) => updateField("contractual_rate", e.target.value)}
                className="mt-1 w-full rounded-md border border-input px-3 py-2 text-sm"
                placeholder="Bijv. 8.00"
              />
            </div>
          )}
        </div>

        {/* Parties */}
        <div className="rounded-lg border border-border bg-white p-6 space-y-4">
          <h2 className="text-lg font-semibold text-navy-800">Partijen</h2>

          {/* Client selection */}
          <div>
            <label className="block text-sm font-medium text-navy-700">
              Client *
            </label>
            {form.client_id ? (
              <div className="mt-1 flex items-center gap-2">
                <span className="rounded-md bg-navy-50 px-3 py-1.5 text-sm text-navy-700">
                  {clientResults?.items.find((c) => c.id === form.client_id)?.name ||
                    "Geselecteerd"}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    updateField("client_id", "");
                    setClientSearch("");
                  }}
                  className="text-xs text-red-500 hover:underline"
                >
                  Wijzigen
                </button>
              </div>
            ) : (
              <div className="mt-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <input
                    type="text"
                    value={clientSearch}
                    onChange={(e) => setClientSearch(e.target.value)}
                    className="w-full rounded-md border border-input bg-white pl-10 pr-4 py-2 text-sm"
                    placeholder="Zoek een client..."
                  />
                </div>
                {clientSearch && clientResults?.items && clientResults.items.length > 0 && (
                  <div className="mt-1 rounded-md border border-border bg-white shadow-sm">
                    {clientResults.items.map((contact) => (
                      <button
                        key={contact.id}
                        type="button"
                        onClick={() => {
                          updateField("client_id", contact.id);
                          setClientSearch(contact.name);
                        }}
                        className="w-full px-4 py-2 text-left text-sm hover:bg-muted"
                      >
                        {contact.name}
                        <span className="ml-2 text-xs text-muted-foreground">
                          {contact.contact_type === "company" ? "Bedrijf" : "Persoon"}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Opposing party selection */}
          <div>
            <label className="block text-sm font-medium text-navy-700">
              Wederpartij
            </label>
            {form.opposing_party_id ? (
              <div className="mt-1 flex items-center gap-2">
                <span className="rounded-md bg-navy-50 px-3 py-1.5 text-sm text-navy-700">
                  {opponentResults?.items.find((c) => c.id === form.opposing_party_id)?.name ||
                    "Geselecteerd"}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    updateField("opposing_party_id", "");
                    setOpponentSearch("");
                  }}
                  className="text-xs text-red-500 hover:underline"
                >
                  Wijzigen
                </button>
              </div>
            ) : (
              <div className="mt-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <input
                    type="text"
                    value={opponentSearch}
                    onChange={(e) => setOpponentSearch(e.target.value)}
                    className="w-full rounded-md border border-input bg-white pl-10 pr-4 py-2 text-sm"
                    placeholder="Zoek een wederpartij..."
                  />
                </div>
                {opponentSearch && opponentResults?.items && opponentResults.items.length > 0 && (
                  <div className="mt-1 rounded-md border border-border bg-white shadow-sm">
                    {opponentResults.items.map((contact) => (
                      <button
                        key={contact.id}
                        type="button"
                        onClick={() => {
                          updateField("opposing_party_id", contact.id);
                          setOpponentSearch(contact.name);
                        }}
                        className="w-full px-4 py-2 text-left text-sm hover:bg-muted"
                      >
                        {contact.name}
                        <span className="ml-2 text-xs text-muted-foreground">
                          {contact.contact_type === "company" ? "Bedrijf" : "Persoon"}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={createCase.isPending}
            className="rounded-md bg-navy-500 px-6 py-2 text-sm font-medium text-white hover:bg-navy-600 disabled:opacity-50 transition-colors"
          >
            {createCase.isPending ? "Aanmaken..." : "Zaak aanmaken"}
          </button>
          <Link
            href="/zaken"
            className="rounded-md border border-border px-6 py-2 text-sm font-medium text-navy-600 hover:bg-muted transition-colors"
          >
            Annuleren
          </Link>
        </div>
      </form>
    </div>
  );
}
