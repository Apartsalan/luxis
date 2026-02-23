"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Search, Plus, X } from "lucide-react";
import { toast } from "sonner";
import { useCreateCase, useConflictCheck, useAddCaseParty } from "@/hooks/use-cases";
import { useRelations, useCreateRelation } from "@/hooks/use-relations";
import { useModules } from "@/hooks/use-modules";
import { AlertTriangle, ShieldAlert } from "lucide-react";
import { useKycStatus } from "@/hooks/use-kyc";

export default function NieuweZaakPageWrapper() {
  return (
    <Suspense fallback={<div className="mx-auto max-w-2xl py-12 text-center text-muted-foreground">Laden...</div>}>
      <NieuweZaakPage />
    </Suspense>
  );
}

function NieuweZaakPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const createCase = useCreateCase();
  const { hasModule } = useModules();

  const prefillClientId = searchParams.get("client_id") || "";
  const prefillClientName = searchParams.get("client_name") || "";

  const [form, setForm] = useState({
    case_type: "incasso",
    debtor_type: "", // auto-filled from opposing party contact_type
    description: "",
    reference: "",
    court_case_number: "",
    interest_type: "statutory",
    contractual_rate: "",
    budget: "", // G13
    client_id: prefillClientId,
    opposing_party_id: "",
    date_opened: new Date().toISOString().split("T")[0],
  });
  const [clientSearch, setClientSearch] = useState(prefillClientName);
  const [opponentSearch, setOpponentSearch] = useState("");
  const [lawyerSearch, setLawyerSearch] = useState("");
  const [selectedLawyer, setSelectedLawyer] = useState<{ id: string; name: string } | null>(null);
  const [error, setError] = useState("");
  const createRelation = useCreateRelation();
  const addParty = useAddCaseParty();

  // Inline contact creation forms
  const [showNewClient, setShowNewClient] = useState(false);
  const [newClient, setNewClient] = useState({ contact_type: "company" as "company" | "person", name: "", email: "" });
  const [showNewOpponent, setShowNewOpponent] = useState(false);
  const [newOpponent, setNewOpponent] = useState({ contact_type: "company" as "company" | "person", name: "", email: "" });

  const handleCreateInlineContact = async (
    role: "client" | "opponent",
    data: { contact_type: "company" | "person"; name: string; email: string }
  ) => {
    try {
      const result = await createRelation.mutateAsync({
        contact_type: data.contact_type,
        name: data.name,
        ...(data.email && { email: data.email }),
      });
      if (role === "client") {
        updateField("client_id", result.id);
        setClientSearch(result.name);
        setShowNewClient(false);
        setNewClient({ contact_type: "company", name: "", email: "" });
      } else {
        updateField("opposing_party_id", result.id);
        setOpponentSearch(result.name);
        setShowNewOpponent(false);
        setNewOpponent({ contact_type: "company", name: "", email: "" });
        if (!form.debtor_type) {
          updateField("debtor_type", data.contact_type === "company" ? "b2b" : "b2c");
        }
      }
      toast.success(`${data.name} aangemaakt`);
    } catch (err: any) {
      toast.error(err.message || "Kon relatie niet aanmaken");
    }
  };

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

  // Conflict checks — runs when client or opposing party is selected
  const { data: clientConflict } = useConflictCheck(
    form.client_id || undefined,
    "client"
  );
  const { data: opponentConflict } = useConflictCheck(
    form.opposing_party_id || undefined,
    "opposing_party"
  );

  // KYC status check for selected client (only when wwft module enabled)
  const { data: clientKycStatus } = useKycStatus(
    hasModule("wwft") ? (form.client_id || undefined) : undefined
  );

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

    if (form.debtor_type) data.debtor_type = form.debtor_type;
    if (form.description) data.description = form.description;
    if (form.reference) data.reference = form.reference;
    if (form.court_case_number) data.court_case_number = form.court_case_number;
    if (form.opposing_party_id) data.opposing_party_id = form.opposing_party_id;
    if (form.interest_type === "contractual" && form.contractual_rate) {
      data.contractual_rate = parseFloat(form.contractual_rate);
    }
    if (form.budget) data.budget = parseFloat(form.budget);

    try {
      const result = await createCase.mutateAsync(data);
      // Add advocaat wederpartij as party if selected
      if (selectedLawyer) {
        try {
          await addParty.mutateAsync({
            caseId: result.id,
            data: { contact_id: selectedLawyer.id, role: "advocaat_wederpartij" },
          });
        } catch {
          // Non-blocking: case is created, party addition failed
          toast.error("Dossier aangemaakt, maar advocaat wederpartij kon niet worden toegevoegd");
        }
      }
      toast.success("Dossier aangemaakt");
      router.push(`/zaken/${result.id}`);
    } catch (err: any) {
      setError(err.message || "Er ging iets mis");
    }
  };

  const inputClass =
    "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors";

  return (
    <div className="mx-auto max-w-2xl space-y-6 animate-fade-in">
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

      <form onSubmit={handleSubmit} className="space-y-6">
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
                <option value="insolventie">Insolventie</option>
                <option value="advies">Advies</option>
                <option value="overig">Overig</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground">
                Debiteurtype
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
                className={inputClass}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground">
              Beschrijving
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
                onChange={(e) => updateField("court_case_number", e.target.value)}
                className={inputClass}
                placeholder="Bijv. C/13/123456 / HA ZA 24-789"
              />
            </div>
          </div>

          {/* G13: Budget field — only shown when budget module is enabled */}
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

        {/* Interest settings — only for incasso cases */}
        {form.case_type === "incasso" && <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          <h2 className="text-base font-semibold text-foreground">
            Rente-instellingen
          </h2>

          <div>
            <label className="block text-sm font-medium text-foreground">
              Type rente
            </label>
            <select
              value={form.interest_type}
              onChange={(e) => updateField("interest_type", e.target.value)}
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
            <div>
              <label className="block text-sm font-medium text-foreground">
                Contractueel rentepercentage (%) *
              </label>
              <input
                type="number"
                step="0.01"
                required={form.interest_type === "contractual"}
                value={form.contractual_rate}
                onChange={(e) => updateField("contractual_rate", e.target.value)}
                className={inputClass}
                placeholder="Bijv. 8.00"
              />
            </div>
          )}
        </div>}

        {/* Parties */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          <h2 className="text-base font-semibold text-foreground">Partijen</h2>

          {/* Client selection */}
          <div>
            <label className="block text-sm font-medium text-foreground">
              Client *
            </label>
            {form.client_id ? (
              <div className="mt-1.5 flex items-center gap-2">
                <span className="rounded-lg bg-primary/10 px-3 py-1.5 text-sm text-primary font-medium">
                  {clientResults?.items.find((c) => c.id === form.client_id)
                    ?.name || prefillClientName || "Geselecteerd"}
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
                    className="w-full rounded-lg border border-input bg-background pl-10 pr-4 py-2.5 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-colors"
                    placeholder="Zoek een client..."
                  />
                </div>
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
                    onClick={() => { setShowNewClient(true); setNewClient(c => ({ ...c, name: clientSearch })); }}
                    className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    Nieuwe relatie aanmaken
                  </button>
                )}
                {showNewClient && (
                  <div className="mt-2 rounded-lg border border-primary/20 bg-primary/5 p-3 space-y-2 animate-fade-in">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-primary">Nieuwe client aanmaken</span>
                      <button type="button" onClick={() => setShowNewClient(false)} className="text-muted-foreground hover:text-foreground"><X className="h-3.5 w-3.5" /></button>
                    </div>
                    <div className="grid gap-2 sm:grid-cols-3">
                      <select
                        value={newClient.contact_type}
                        onChange={(e) => setNewClient(c => ({ ...c, contact_type: e.target.value as any }))}
                        className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                      >
                        <option value="company">Bedrijf</option>
                        <option value="person">Persoon</option>
                      </select>
                      <input
                        type="text"
                        placeholder="Naam *"
                        value={newClient.name}
                        onChange={(e) => setNewClient(c => ({ ...c, name: e.target.value }))}
                        className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                      />
                      <input
                        type="email"
                        placeholder="E-mail (optioneel)"
                        value={newClient.email}
                        onChange={(e) => setNewClient(c => ({ ...c, email: e.target.value }))}
                        className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                      />
                    </div>
                    <button
                      type="button"
                      disabled={!newClient.name.trim() || createRelation.isPending}
                      onClick={() => handleCreateInlineContact("client", newClient)}
                      className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                    >
                      {createRelation.isPending ? "Aanmaken..." : "Aanmaken en selecteren"}
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
                    Deze cliënt is in {clientConflict.conflicts.length === 1 ? "een ander dossier" : `${clientConflict.conflicts.length} andere dossiers`} wederpartij:
                  </p>
                  <ul className="mt-1 space-y-0.5">
                    {clientConflict.conflicts.map((c) => (
                      <li key={c.case_id} className="text-xs text-amber-700">
                        <span className="font-mono font-medium">{c.case_number}</span>
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
          {form.client_id && clientKycStatus && !clientKycStatus.is_compliant && (
            <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3">
              <div className="flex items-start gap-2">
                <ShieldAlert className="h-4 w-4 text-red-600 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-medium text-red-800">
                    WWFT-verificatie niet voltooid
                  </p>
                  <p className="mt-0.5 text-xs text-red-700">
                    {clientKycStatus.status === "niet_gestart"
                      ? "Deze cliënt heeft nog geen WWFT/KYC verificatie. Dit is wettelijk verplicht voordat juridische diensten worden verleend."
                      : clientKycStatus.is_overdue
                      ? "De WWFT-verificatie van deze cliënt is verlopen en moet opnieuw worden beoordeeld."
                      : "De WWFT-verificatie van deze cliënt is nog niet afgerond."}
                  </p>
                  <Link
                    href={`/relaties/${form.client_id}`}
                    className="mt-1.5 inline-block text-xs font-medium text-red-700 hover:text-red-900 underline"
                  >
                    Ga naar verificatie →
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* Opposing party selection */}
          <div>
            <label className="block text-sm font-medium text-foreground">
              Wederpartij
            </label>
            {form.opposing_party_id ? (
              <div className="mt-1.5 flex items-center gap-2">
                <span className="rounded-lg bg-warning/10 px-3 py-1.5 text-sm text-warning font-medium">
                  {opponentResults?.items.find(
                    (c) => c.id === form.opposing_party_id
                  )?.name || "Geselecteerd"}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    updateField("opposing_party_id", "");
                    setOpponentSearch("");
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
                            // Auto-fill debtor_type from contact type
                            if (!form.debtor_type) {
                              updateField(
                                "debtor_type",
                                contact.contact_type === "company" ? "b2b" : "b2c"
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
                    onClick={() => { setShowNewOpponent(true); setNewOpponent(c => ({ ...c, name: opponentSearch })); }}
                    className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    Nieuwe relatie aanmaken
                  </button>
                )}
                {showNewOpponent && (
                  <div className="mt-2 rounded-lg border border-primary/20 bg-primary/5 p-3 space-y-2 animate-fade-in">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-primary">Nieuwe wederpartij aanmaken</span>
                      <button type="button" onClick={() => setShowNewOpponent(false)} className="text-muted-foreground hover:text-foreground"><X className="h-3.5 w-3.5" /></button>
                    </div>
                    <div className="grid gap-2 sm:grid-cols-3">
                      <select
                        value={newOpponent.contact_type}
                        onChange={(e) => setNewOpponent(c => ({ ...c, contact_type: e.target.value as any }))}
                        className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                      >
                        <option value="company">Bedrijf</option>
                        <option value="person">Persoon</option>
                      </select>
                      <input
                        type="text"
                        placeholder="Naam *"
                        value={newOpponent.name}
                        onChange={(e) => setNewOpponent(c => ({ ...c, name: e.target.value }))}
                        className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                      />
                      <input
                        type="email"
                        placeholder="E-mail (optioneel)"
                        value={newOpponent.email}
                        onChange={(e) => setNewOpponent(c => ({ ...c, email: e.target.value }))}
                        className="rounded-md border border-input bg-background px-2 py-1.5 text-sm"
                      />
                    </div>
                    <button
                      type="button"
                      disabled={!newOpponent.name.trim() || createRelation.isPending}
                      onClick={() => handleCreateInlineContact("opponent", newOpponent)}
                      className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                    >
                      {createRelation.isPending ? "Aanmaken..." : "Aanmaken en selecteren"}
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
                    Deze wederpartij is in {opponentConflict.conflicts.length === 1 ? "een ander dossier" : `${opponentConflict.conflicts.length} andere dossiers`} cliënt:
                  </p>
                  <ul className="mt-1 space-y-0.5">
                    {opponentConflict.conflicts.map((c) => (
                      <li key={c.case_id} className="text-xs text-amber-700">
                        <span className="font-mono font-medium">{c.case_number}</span>
                        {" — cliënt"}
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
                            setSelectedLawyer({ id: contact.id, name: contact.name });
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
              </div>
            )}
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
            disabled={createCase.isPending}
            className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {createCase.isPending ? "Aanmaken..." : "Dossier aanmaken"}
          </button>
          <Link
            href="/zaken"
            className="rounded-lg border border-border px-6 py-2.5 text-sm font-medium text-foreground hover:bg-muted transition-colors"
          >
            Annuleren
          </Link>
        </div>
      </form>
    </div>
  );
}
