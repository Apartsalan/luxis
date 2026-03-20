import Link from "next/link";
import { Search, Plus, X, AlertTriangle, ShieldAlert } from "lucide-react";
import { ConfidenceDot } from "./ConfidenceDot";
import { InlineContactDetails } from "./InlineContactDetails";
import type { InlineContact } from "./types";
import type { InvoiceParseResult } from "@/hooks/use-invoice-parser";
import type { LuxisModule } from "@/hooks/use-modules";
import type { ConflictResult } from "@/hooks/use-cases";
import type { KycStatus } from "@/hooks/use-kyc";

interface Step2Props {
  form: {
    client_id: string;
    opposing_party_id: string;
    debtor_type: string;
  };
  updateField: (field: string, value: string) => void;
  inputClass: string;
  fieldConfidence: Record<string, number>;
  invoiceData: InvoiceParseResult | null;

  // Client
  clientSearch: string;
  setClientSearch: (v: string) => void;
  clientResults: { items: { id: string; name: string; contact_type: string }[] } | undefined;
  prefillClientName: string;
  showNewClient: boolean;
  setShowNewClient: (v: boolean) => void;
  newClient: InlineContact;
  setNewClient: React.Dispatch<React.SetStateAction<InlineContact>>;
  showClientDetails: boolean;
  setShowClientDetails: React.Dispatch<React.SetStateAction<boolean>>;
  clientConflict: ConflictResult | undefined;
  clientKycStatus: KycStatus | undefined;
  hasModule: (mod: LuxisModule) => boolean;

  // Opponent
  opponentSearch: string;
  setOpponentSearch: (v: string) => void;
  opponentResults: { items: { id: string; name: string; contact_type: string }[] } | undefined;
  prefillOpponentName: string;
  showNewOpponent: boolean;
  setShowNewOpponent: (v: boolean) => void;
  newOpponent: InlineContact;
  setNewOpponent: React.Dispatch<React.SetStateAction<InlineContact>>;
  showOpponentDetails: boolean;
  setShowOpponentDetails: React.Dispatch<React.SetStateAction<boolean>>;
  opponentConflict: ConflictResult | undefined;
  setOpponentContactType: (v: string) => void;

  // Lawyer
  lawyerSearch: string;
  setLawyerSearch: (v: string) => void;
  lawyerResults: { items: { id: string; name: string; contact_type: string }[] } | undefined;
  selectedLawyer: { id: string; name: string } | null;
  setSelectedLawyer: (v: { id: string; name: string } | null) => void;
  showNewLawyer: boolean;
  setShowNewLawyer: (v: boolean) => void;
  newLawyer: InlineContact;
  setNewLawyer: React.Dispatch<React.SetStateAction<InlineContact>>;
  showLawyerDetails: boolean;
  setShowLawyerDetails: React.Dispatch<React.SetStateAction<boolean>>;

  // Shared
  handleCreateInlineContact: (role: "client" | "opponent" | "lawyer", data: InlineContact) => Promise<void>;
  createRelationIsPending: boolean;
}

export function Step2Partijen(props: Step2Props) {
  const {
    form, updateField, fieldConfidence, invoiceData,
    clientSearch, setClientSearch, clientResults, prefillClientName,
    showNewClient, setShowNewClient, newClient, setNewClient,
    showClientDetails, setShowClientDetails,
    clientConflict, clientKycStatus, hasModule,
    opponentSearch, setOpponentSearch, opponentResults, prefillOpponentName,
    showNewOpponent, setShowNewOpponent, newOpponent, setNewOpponent,
    showOpponentDetails, setShowOpponentDetails,
    opponentConflict, setOpponentContactType,
    lawyerSearch, setLawyerSearch, lawyerResults,
    selectedLawyer, setSelectedLawyer,
    showNewLawyer, setShowNewLawyer, newLawyer, setNewLawyer,
    showLawyerDetails, setShowLawyerDetails,
    handleCreateInlineContact, createRelationIsPending,
  } = props;

  return (
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
                    !newClient.name.trim() || createRelationIsPending
                  }
                  onClick={() =>
                    handleCreateInlineContact("client", newClient)
                  }
                  className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  {createRelationIsPending
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
                    !newOpponent.name.trim() || createRelationIsPending
                  }
                  onClick={() =>
                    handleCreateInlineContact("opponent", newOpponent)
                  }
                  className="rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  {createRelationIsPending
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
                    !newLawyer.name.trim() || createRelationIsPending
                  }
                  onClick={() =>
                    handleCreateInlineContact("lawyer", newLawyer)
                  }
                  className="rounded-md bg-violet-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-violet-700 disabled:opacity-50 transition-colors"
                >
                  {createRelationIsPending
                    ? "Aanmaken..."
                    : "Aanmaken en selecteren"}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
